from riv.resources import Resource
from riv.wrappers import StandaloneWrapper
from polls.wrappers import PollWrapper, PollBatchWrapper, VoteWrapper, ResultWrapper
from polls.models import Poll, Choice, Tag

class VoteResource(Resource):
	_wrapper = VoteWrapper()
	class Meta:
		allowed_methods = ['POST',]
		extra_fields = ['poll', 'choice']

class ResultResource(Resource):
	_wrapper = ResultWrapper()
	class Meta:
		allowed_methods = ['GET_object',]
		redirect_as_error = True
		redirect_as_error_code = 401
		extra_fields = ['choice',]

class StandaloneTagResource(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		model = Tag
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
		allow_batch_creation = True

class StandaloneReadOnlyChoiceResource(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		model = Choice
		allowed_methods = ['GET',]

class ReadOnlyPollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		reverse = True
		allowed_methods = ['GET',]

class RelatedAsIdsPollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		related_as_ids = True
		allowed_methods = ['GET',]

class NoFallbackPollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		fallback_on_unsupported_format = False
		allowed_methods = ['GET',]

class PutOnlyPollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		allowed_methods = ['PUT',]

class PostOnlyPollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		render_object_after_post = True
		allowed_methods = ['POST',]

class DeleteOnlyPollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		allowed_methods = ['DELETE',]

class BatchDeletePollResource(Resource):
	_wrapper = PollBatchWrapper()
	class Meta:
		model = Poll
		allow_batch_deletion = True
		allowed_methods = ['DELETE',]

class ReadWritePollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']

class ReadWriteRenderPollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		render_object_after_post = True
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']

class BatchPostPollResource(Resource):
	_wrapper = PollBatchWrapper()
	class Meta:
		model = Poll
		allow_batch_creation = True
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']

# The following tests for "fields, exclude, inline, reverse,
# extra and map" are just basic tests to see if the option
# is handled. The detailed checks should be part of the
# serializer tests.
class FieldsPollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		fields = ['question',]
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']

class ExcludePollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		exclude = ['tags', 'question']
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']

class InlinePollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		inline = ['tags']
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']

class ReversePollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		reverse = ['choice_set',]
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']

class ExtraPollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		extra_fields = ['was_published_today',]
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']

class MapPollResource(Resource):
	_wrapper = PollWrapper()
	class Meta:
		model = Poll
		map_fields = {'pub_date': 'poll_date'}
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']


class StandaloneReadOnlyPollResource(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		allowed_methods = ['GET']
		model = Poll

class StandalonePutOnlyPollResource(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		model = Poll
		allowed_methods = ['PUT',]

class StandalonePostOnlyPollResource(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		model = Poll
		# This setting is mandatory if the StandaloneWrapper is used!
		allow_batch_creation = True
		render_object_after_post = True
		allowed_methods = ['POST',]

class StandaloneDeleteOnlyPollResource(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		model = Poll
		allowed_methods = ['DELETE',]

class StandaloneReadWritePollResource(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		# This setting is mandatory if the StandaloneWrapper is used!
		allow_batch_creation = True
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
		model = Poll

class StandaloneReadWritePollResource2(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		# This setting is mandatory if the StandaloneWrapper is used!
		allow_batch_creation = True
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
		model = Poll
		render_object_after_post = True

class StandaloneExcludeGetOnly(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
		model = Poll
		exclude = [{'pub_date': ['GET']}, {'tags': ['GET']}]

class StandaloneExcludePostOnly(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		# This setting is mandatory if the StandaloneWrapper is used!
		allow_batch_creation = True
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
		model = Poll
		exclude = [{'pub_date': ['POST']}]

class StandaloneExcludePutOnly(Resource):
	_wrapper = StandaloneWrapper()
	class Meta:
		allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
		model = Poll
		exclude = [{'pub_date': ['PUT']}]
