from StringIO import StringIO

from django.db.models import Model
from django.core.serializers import python, json
from django.core.serializers.base import SerializationError
from django.core.urlresolvers import reverse, NoReverseMatch
from django.utils.encoding import smart_unicode, is_protected_type
from django.utils import simplejson

from riv.utils import traverse_dict, create_tree_with_val, get_url_for_object

SEPARATOR = '__'

class LoadingError(Exception):
    pass

class Serializer(python.Serializer):
    """
    This is the base for all REST serializers.
    """
    internal_use_only = False

    def get_loader(self):
        return Loader

    def serialize(self, queryset, **options):
        # The "fields" option is handled by the superclass serializer.
        #
        # We added the possibility to exclude fields. The handling is done
        # in the start_object method.
        self.api_name = options.pop('api_name', None)
        self.related_as_ids = options.pop('related_as_ids', False)
        self.excluded_fields = options.pop('exclude', [])
        self.extra_fields = options.pop('extra', [])
        self.inline = options.pop('inline', [])
        self.map_fields = options.pop('map_fields', {}) # "map" is reserved!
        self.reverse_fields = options.pop('reverse_fields', [])
        self.render_only = options.pop('render_only', False)

        # If inline is True, each ForeignKey and ManyToMany field is 
        # serialized using a new Serializer. 
        # Reverse relationships include a ForeignKey/M2M back to the current
        # object which is then serialized again. That results in an infinte
        # loop. Thus, we only serialize FK/M2M/REV relationships, if reverse
        # is set to False.
        #self.reverse = options.pop('reverse', None)

        serializee = None
        try:
            iter(queryset)
        except TypeError:
            # We are asked to serialize an object instead of an iterable.
            self.single_object = True
            serializee = [queryset,]
        else:
            self.single_object = False
            serializee = queryset
        if self.render_only:
            return self.fake_serialize(serializee, **options)
        else:
            return super(Serializer, self).serialize(serializee, **options)

    def fake_serialize(self, queryset, **options):
        self.options = options
        self.stream = options.pop("stream", StringIO())
        self.selected_fields = options.pop("fields", None)

        self.start_serialization()
        # this is a dirty hack
        self.objects = [{'fields': queryset}]
        self.end_serialization()
        return self.getvalue()

    def start_serialization(self):
        super(Serializer, self).start_serialization()
        if self.selected_fields and self.excluded_fields:
            # Remove the excluded fields from the list of selected fields.
            self.selected_fields = list(
                set(self.selected_fields).difference(set(self.excluded_fields))
            )

    def start_object(self, obj):
        super(Serializer, self).start_object(obj)
        try:
            self.serialize_reverse_fields(obj)
        except AttributeError:
            raise
        # We have no fields defined but we want to exclude fields. Thus, we
        # have to grab the list of all fields and exclude the required ones.
        if not self.selected_fields and self.excluded_fields:
            self.selected_fields = list(
                set(obj._meta.get_all_field_names()).difference(set(self.excluded_fields))
            )

    def end_object(self, obj):
        if self.selected_fields is None or obj._meta.pk.name in self.selected_fields:
            # Add the primary key with its proper field name to the list of fields.
            self._current[obj._meta.pk.name] = smart_unicode(obj._get_pk_val(), strings_only=True)
        if self.extra_fields:
            for field in self.extra_fields:
                field_obj = getattr(obj, field, None)
                if field_obj:
                    if callable(field_obj):
                        self._current[field] = field_obj()
                    else:
                        self._current[field] = field_obj
        if self.map_fields:
            for key,value in self.map_fields.iteritems():
                if self._current.has_key(key):
                    self._current[value] = self._current[key]
                    del self._current[key]
                elif SEPARATOR in key and self._current.has_key(key.split(SEPARATOR)[0]):
                    key_list = key.split(SEPARATOR)
                    try:
                        # Walk down the dictionaries and return the value.
                        # This has to be done before the "value check" below to ensure that
                        # a KeyError is raised in case the ForeignKey has not been serialized
                        # (through the 'inline' option)
                        tmp = traverse_dict(self._current, key_list)

                        if SEPARATOR in value:
                            value_list = value.split(SEPARATOR)
                            if key_list[0] == value_list[0]:
                                # If the value is a ForeignKey as well (contains the SEPARATOR)
                                # we don't handle it here.
                                continue
                            else:
                                # Crossmapping between different ForeignKey objects
                                # is currently not supported.
                                raise SerializationError("Crossmapping between different ForeignKey fields is currently not supported.")

                        self._current[value] = tmp
                        # Then, walk down the dictionaries and remove the key.
                        del traverse_dict(self._current, key_list, return_parent=True)[key_list[-1]]
                    except KeyError:
                        raise SerializationError("Invalid key '%s' in map_fields. Did you add '%s' to the inline fields?" % (key, key_list[0]))
                else:
                    raise SerializationError("Invalid key '%s' in map_fields." % (key,))
        super(Serializer, self).end_object(obj)

    def end_serialization(self):
        super(Serializer, self).end_serialization()
        self.objects = [i['fields'] for i in self.objects]

        if self.single_object:
            self.objects = self.objects[0]

    def handle_fk_field(self, obj, field):
        if self.inline and field.name in self.inline:
            tmpserializer = self.__class__()
            fields, exclude, maps, inline = self._get_serialize_options_for_subfield(field.name)
            tmpserializer.serialize(
                getattr(obj, field.name),
                inline=inline,
                fields=fields,
                exclude=exclude,
                map_fields=maps,
                finalize=False
            )
            self._current[field.name] = tmpserializer.objects
        else:
            super(Serializer, self).handle_fk_field(obj, field)
            if not self.related_as_ids:
                related = getattr(obj, field.name)
                if related:
                    #val = reverse('object-%s-%s' % (self.api_name, related._meta), kwargs={'id': self._current[field.name]})
                    val = get_url_for_object(self.api_name, related, self._current[field.name])
                    self._current[field.name] = val


    def handle_m2m_field(self, obj, field):
        if self.inline and field.name in self.inline:
            tmpserializer = self.__class__()
            fields, exclude, maps, inline = self._get_serialize_options_for_subfield(field.name)
            self._current[field.name] = []
            for related in getattr(obj, field.name).iterator():
                tmpserializer.serialize(
                    related,
                    inline=inline,
                    fields=fields,
                    exclude=exclude,
                    map_fields=maps,
                    finalize=False
                )
                self._current[field.name].append(tmpserializer.objects)
        else:
            super(Serializer, self).handle_m2m_field(obj, field)
            if not self.related_as_ids:
                related = getattr(obj, field.name)
                view_name = 'object-%s-%s' % (self.api_name, related.model._meta)
                for pos,val in enumerate(self._current[field.name]):
                    try:
                        self._current[field.name][pos] = reverse(view_name, kwargs={'id': val})
                    except NoReverseMatch:
                        # this indicates that no resource has been registered for this model. So 
                        # we just return the primary key of the object.
                        pass

    def serialize_reverse_fields(self, obj):
        if not self.reverse_fields:
            return
        for fieldname in self.reverse_fields:
            if self.inline and fieldname in self.inline:
                tmpserializer = Serializer()
                fields, exclude, maps, inline = self._get_serialize_options_for_subfield(fieldname)
                if isinstance(getattr(obj, fieldname), Model):
                    self._current[fieldname] = tmpserializer.serialize(
                        getattr(obj, fieldname),
                        inline=inline, 
                        fields=fields, 
                        exclude=exclude,
                        map_fields=maps,
                    )
                else:
                    self._current[fieldname] = [tmpserializer.serialize(
                        related,
                        inline=inline,
                        fields=fields,
                        exclude=exclude,
                        map_fields=maps,
                    ) for related in getattr(obj, fieldname).iterator()]
            else:
                #rev = lambda field: reverse('object-%s-%s' % (self.api_name, field._meta), kwargs={'id': field._get_pk_val()})
                rev = lambda field: get_url_for_object(self.api_name, field)
                if isinstance(getattr(obj, fieldname), Model):
                    if self.related_as_ids:
                        self._current[fieldname] = getattr(obj, fieldname)._get_pk_val()
                    else:
                        #try:
                        #    self._current[fieldname] = rev(getattr(obj, fieldname))
                        #except NoReverseMatch:
                        #    self._current[fieldname] = getattr(obj, fieldname)._get_pk_val()
                        self._current[fieldname] = rev(getattr(obj, fieldname))
                else:
                    if self.related_as_ids:
                        self._current[fieldname] = [related._get_pk_val() for related in getattr(obj, fieldname).iterator()]
                    else:
                        #try:
                        #    self._current[fieldname] = [rev(related) for related in getattr(obj, fieldname).iterator()]
                        #except NoReverseMatch:
                        #    self._current[fieldname] = [related._get_pk_val() for related in getattr(obj, fieldname).iterator()]
                        self._current[fieldname] = [rev(related) for related in getattr(obj, fieldname).iterator()]

    def _get_serialize_options_for_subfield(self, name):
            fields, exclude, maps, inline = None, None, {}, None
            field_option_name = name + SEPARATOR
            if self.selected_fields:
                fields = [i.replace(field_option_name,'') for i in self.selected_fields if i.startswith(field_option_name)]
            if self.excluded_fields:
                exclude = [i.replace(field_option_name,'') for i in self.excluded_fields if i.startswith(field_option_name)]
            if self.inline:
                inline = [i.replace(field_option_name,'') for i in self.inline if i.startswith(field_option_name)]
            if self.map_fields:
                for k,v in self.map_fields.items():
                    if k.startswith(field_option_name) and v.startswith(field_option_name):
                        # Remove the key from the original list of fields. It
                        # has been handled here.
                        del self.map_fields[k]
                        maps[k.replace(field_option_name, '')] = v.replace(field_option_name, '')
            return fields or None, exclude or None, maps, inline


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


class Loader:
    """
    This class loads the user input and rearranges the fields that
    have been mapped by the serializer. The input can be transformed
    in a formset-like input which can be treated as a normal form
    POST.
    """
    internal_use_only = False

    def load(self, queryset, **options):
        self.selected_fields = options.pop('fields', None)
        self.excluded_fields = options.pop('exclude', [])
        self.map_fields = options.pop('map_fields', None) # "map" is reserved!
        self.model = options.pop('model', None)
        # data will contain the raw material as it was given to the
        # load method. objects will contain the deserialized data
        # as python list and dictionaries.
        # For the base serializer both are the same.
        self.data = self.objects = queryset

        self.pre_loading()
        # Ensure we always have a list of objects.
        if not isinstance(self.objects, list):
            self.objects = [self.objects,]

        self.remove_excluded_fields()
        self.reverse_map_fields()
        self.post_loading()

    def pre_loading(self):
        pass

    def post_loading(self):
        pass

    def get_querydict(self, force_batch=False):
        if isinstance(self.objects, list):
            if force_batch or len(self.objects) > 1:
                self.dictionize_list_for_formsets()
            else:
                return self.get_objects()[0]
        return self.get_objects()

    def get_objects(self):
        return self.objects

    def dictionize_list_for_formsets(self):
        d = {}
        for (counter, data) in enumerate(self.objects):
            d.update(dict([(unicode("form-"+str(counter)+"-"+str(k)), v) for (k,v) in data.items()]))
        d.update({'form-TOTAL_FORMS': unicode(counter+1), 'form-INITIAL_FORMS': u'0', 'form-MAX_NUM_FORMS': u''})
        self.objects = d

    def remove_excluded_fields(self):
        for object in self.objects:
            for field in object.keys():
                if self.selected_fields and not field in self.selected_fields:
                    del object[field]
                if field in self.excluded_fields:
                    del object[field]

    def reverse_map_fields(self, objects=None):
        if not objects:
            objects = self.objects
        if not self.map_fields:
            return
        for k,v in self.map_fields.items():
            source, target = {}, {}
            source_keys = v.split(SEPARATOR)
            target_keys = k.split(SEPARATOR)
            try:
                source = traverse_dict(objects[0], source_keys, return_parent=True)
            except KeyError:
                continue
            for obj in objects:
                create_tree_with_val(obj, target_keys, source[source_keys[-1]])
            del source[source_keys[-1]]


    def rearrange_for_deserialization(self):
        """
        Rearrange the input back to fit into the standard django deserializer.

        IMPORTANT: We assume that ALL objects in the list belong to the same
        model!
        """
        new_list = []
        for obj in self.objects:
            pk = obj.get('pk', obj.get('id', None))
            new_list.append({
                'pk': pk,
                'model': self.model,
                'fields': obj
            })

        self.objects = new_list

