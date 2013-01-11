from StringIO import StringIO
from django.conf import settings
from django.utils.encoding import smart_str
from django.core.serializers.base import DeserializationError
from django.utils.xmlutils import SimplerXMLGenerator
#from xml.dom import pulldom
from xml.dom.minidom import parse

from riv.serializers import base_serializer as base

class Serializer(base.Serializer):
    internal_use_only = False

    ROOT_ELEMENT = 'objects'

    def get_loader(self):
        return Loader

    def serialize(self, queryset, **options):
        self.finalize = options.pop('finalize', True)
        self.indent_level = options.pop('indent', None)
        self.encoding = options.pop('encoding', settings.DEFAULT_CHARSET)
        return super(Serializer, self).serialize(queryset, **options)

    def indent(self, level):
        if self.indent_level is not None:
            self.xml.ignoreWhitespace('\n' + ' ' *self.indent_level*level)

    def start_object(self, obj):
        super(Serializer, self).start_object(obj)
        self._current['xml_verbose_name'] = smart_str(obj._meta.verbose_name)

    def handle_m2m_field(self, obj, field):
        super(Serializer, self).handle_m2m_field(obj, field)
        self._current[field.name].insert(0, smart_str(getattr(obj, field.name).model._meta.verbose_name))

    def serialize_reverse_fields(self, obj):
        super(Serializer, self).serialize_reverse_fields(obj)
        for fieldname in self.reverse_fields:
            related = getattr(obj, fieldname)
            if isinstance(self._current[fieldname], list):
                self._current[fieldname].insert(0, smart_str(related.model._meta.verbose_name))

    def end_serialization(self):
        super(Serializer, self).end_serialization()
        if not self.finalize:
            return
        self.xml = SimplerXMLGenerator(self.stream, self.encoding)
        self.xml.startDocument()
        self.xml.startElement(self.ROOT_ELEMENT, {})

        if not isinstance(self.objects, list):
            self.objects = [self.objects,]

        for object in self.objects:
            self.indent(1)
            name = self._get_xml_name(object)
            self.xml.startElement(name, {})
            self.handle_dict(object)
            self.xml.endElement(name)

        self.indent(0)
        self.xml.endElement(self.ROOT_ELEMENT)
        self.xml.endDocument()

    def handle_dict(self, d):
        # Make sure this key is removed.
        if d.has_key('xml_verbose_name'):
            del d['xml_verbose_name']
        for k,v in d.items():
            self.indent(2)
            if self.render_only and isinstance(v, list):
                self.handle_list(v, name=k)
            else:
                self.xml.startElement(k, {})
                if isinstance(v, list):
                    self.handle_list(v)
                elif isinstance(v, dict):
                    self.handle_dict(v)
                else:
                    self.xml.characters(smart_str(v))
                self.xml.endElement(k)

    def handle_list(self, l, name=None):
        if l and not name:
            name = smart_str(l.pop(0))
        else:
            if not name:
                name = 'object'
        for object in l:
            self.xml.startElement(name, {})
            if isinstance(object, dict):
                self.handle_dict(object)
            else:
                self.xml.characters(smart_str(object))
            self.xml.endElement(name)

    def getvalue(self):
        if callable(getattr(self.stream, 'getvalue', None)):
            return self.stream.getvalue()

    def _get_xml_name(self, obj):
        if isinstance(obj, dict) and obj.has_key('xml_verbose_name'):
            return obj.pop('xml_verbose_name')
        return 'object'

class Loader(base.Loader):
    def pre_loading(self):
        if isinstance(self.data, basestring):
            stream = StringIO(self.data)
        else:
            stream = self.data

        try:
            dom = parse(stream)
            self.objects = self._dom_to_python(dom)
        except Exception, e:
            raise base.LoadingError(e)

    def _dom_to_python(self, dom):
        if dom.documentElement.nodeName == Serializer.ROOT_ELEMENT:
            return self._handle_object_list(dom.documentElement)
        return {}

    def _handle_object_list(self, objlist):
        return [self._handle_object(node) for node in objlist.childNodes]

    def _handle_object(self, node):
        d = {}
        for child in node.childNodes:
            if child.nodeType == node.TEXT_NODE:
                return child.nodeValue
            elif child.nodeType == node.ELEMENT_NODE:
                x = self._handle_object(child)
                if d.has_key(child.nodeName):
                    d[child.nodeName] = list(d[child.nodeName])
                    d[child.nodeName].append(x)
                else:
                    d[child.nodeName] = x
        return d


# TODO this should be class based and inherit from the base deserializer.
def Deserializer(object_list, **options):
    """
    Revert all the mappings and renamings from the Serializer and pass
    the result to the django python serializer.

    It's expected that you pass the Python objects themselves (instead of a
    stream or a string) to the constructor
    """
    loader = Loader()
    loader.load(object_list, **options)
    loader.rearrange_for_deserialization()
    return python.Deserializer(loader.get_objects())
