from riv.resources import Resource
from riv.wrappers import StandaloneWrapper
from polls.wrappers import PollWrapper
from polls.models import Poll

#class TemporaryResource(Resource):
#	def as_json(self, queryset=None):
#		from django.utils import simplejson
#		from riv.serializers.tmp import Serializer
#		s = Serializer()
#		if not queryset:
#			s.serialize(self._queryset)
#		else:
#			s.serialize(queryset)
#		return s.get_value('json')

class ReadOnlyPollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		allowed_methods = ['GET',]

class PollResource(Resource):
	_wrapper = PollWrapper()

	class Meta:
		name = 'poll'
		allowed_methods = ['GET', 'PUT', 'DELETE']
		redirect_as_error = True
		redirect_as_error_code = 401

class ReadWritePollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		name = 'poll'
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']

class StandaloneReadOnlyPollResource(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		name = 'poll'
		allowed_methods = ['GET']
		model = Poll

class StandaloneReadWritePollResource(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		name = 'poll'
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
		model = Poll

class StandaloneReadWritePollResource2(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		name = 'poll'
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
		model = Poll
		include_object_in_response = True
