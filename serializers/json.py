from StringIO import StringIO
from django.utils import simplejson
from django.core.serializers.json import DjangoJSONEncoder, DateTimeAwareJSONEncoder
from django.core.serializers.base import DeserializationError

from riv.serializers import base

class Serializer(base.Serializer):
	internal_use_only = False

	def end_serialization(self):
		super(Serializer, self).end_serialization()
		simplejson.dump(self.objects, self.stream, cls=DjangoJSONEncoder, **self.options)

	def getvalue(self):
		if callable(getattr(self.stream, 'getvalue', None)):
			return self.stream.getvalue()

def Deserializer(stream_or_string, **options):
    """
    Deserialize a stream or string of JSON data.
    """
    if isinstance(stream_or_string, basestring):
        stream = StringIO(stream_or_string)
    else:
        stream = stream_or_string
    try:
        for obj in base.Deserializer(simplejson.load(stream), **options):
            yield obj
    except GeneratorExit:
        raise
    except Exception, e:
        # Map to deserializer error
        raise DeserializationError(e)
