from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseServerError, HttpResponseNotFound
from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from django.db.models.query import QuerySet
from django.core import serializers

from riv import RestResponse
from riv.http import HttpResponseNotAllowed, HttpResponseNoContent, HttpResponseCreated, HttpResponseNotImplemented
from riv.info import RestInformation
from riv.utils import detect_format, dictionize_list_for_formsets
from riv.wrappers import BaseWrapper

# A short documentation about the different Method definitions:
# (http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html)
#
# PUT:
# - URI refers to an already existing resource
# - the enclosed entity is a modified version of the requested resource
# - if the URI points to a non-existing resource the server MAY create
#   a new one.
# - resource newly created = 201; resource modified = 200 (OK) or 204 (No content)
# - The server MUST analyse the Content-* headers and return 501 if it
#   does not understand the request.
# - PUT URIs define entities. POST URIs defines resources that can HANDLE the entity.
# - If the server wants to apply the change to another resource it MUST return 
#   301 (Moved permanently).
#
# POST:
#
# GET:
#
# DELETE:
#

# TESTS TO WRITE:
# - put 'bind_model' and add queryset with invalid element.
#

# This is the public API
__all__ = (
	'Resource',
)

ALLOWED_OPTIONS = (
	'name', 						# used to create the URLs. Not tied to any model!
	'model',
	'allowed_methods',
	'include_object_in_response',
	'redirect_as_error',
	'redirect_as_error_code',
	'resource_handling_required',
	'valid_response_required',
	'readonly_queryset',
	'fields',
	'exclude',
	'inline',
	'reverse_fields',
	'extra_fields',
	'map_fields'
)

class ResourceOptions(object):
	"""
	Contains defaults for all options.
	"""
	def __init__(self, meta):
		self.model = None
		self.allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
		self.include_object_in_response = False
		self.redirect_as_error = False
		self.redirect_as_error_code = 401
		self.resource_handling_required = False
		self.readonly_queryset = False
		self.fields = None # has to be None, because [] reads as "no field"
		self.exclude = []
		self.inline = []
		self.reverse_fields = []
		self.extra_fields = []
		self.map_fields = {}

		self.formats = {
			'application/json': 'json',
			#'application/xml': 'xml',
			'text/xml': 'xml',
			#'json': 'application/json',
			#'xml': 'text/xml',
		}

		# apply overridden fields from 'class Meta'.
		self.apply_overrides(meta)

	def apply_overrides(self, meta):
		meta_dict = getattr(meta, '__dict__', None)
		if meta_dict:
			for opt_name in meta_dict:
				if opt_name.startswith('_'):
					continue
				if opt_name in ALLOWED_OPTIONS:
					setattr(self, opt_name, meta_dict[opt_name])
				else:
					raise TypeError('Invalid attribute in Meta: %s' % opt_name)
			

class ResourceMeta(type):
	"""
	Metaclass for Resources.
	"""
	def __new__(cls, name, bases, attrs):
		# TODO
		#parents = [b for b in bases if issubclass(b, Resource)]
		#print parents
		new_class = super(ResourceMeta, cls).__new__(cls, name, bases, attrs)
		meta = getattr(new_class, 'Meta', None)
		
		new_class._meta = ResourceOptions(meta)

		if getattr(new_class._meta, 'model', None):
			pass
		# TODO

		return new_class

class Resource(object):
	__metaclass__ = ResourceMeta

	_wrapper = BaseWrapper()
	#_has_errors = False
	#_error_dict = {}

	@property
	def __name__(self):
		return type(self).__name__

	@property
	def wrapper(self):
		return self._wrapper

	@wrapper.setter
	def wrapper(self, wrapper):
		self._wrapper = wrapper

	#@wrapper.deleter
	#def wrapper(self):
	#	del _wrapper

	def __init__(self, display_errors=False, name=None):
		# TODO: what if meta does not have a name set?
		self.name = name or self._meta.name
		self.display_errors = getattr(settings, 'RIV_DISPLAY_ERRORS', display_errors)

	def _get_urls(self):
		return patterns('',
			url(r'^%s/?$' % (self.name), self.handle_request, name='list'),
			url(r'^%s/(?P<id>\d+)/?$' % (self.name), self.handle_request, name='object'),
			url(r'^%s/(?P<id_list>\d[;\d]+)/?$' % (self.name), self.handle_request, name='multiple'),
		)
	urls = property(_get_urls)
			
	def get_format(self, request):
		# json is default
		formats = detect_format(request)

		for f in formats:
			if self._meta.formats.get(f, None):
				# We assume the first given format is the default format.
				return self._meta.formats.get(f)
			# TODO: define a default format somewhere.
			return self._meta.formats['application/json']

	#@property
	#def wrap_request(self):
	#	"""
	#	Took this elegant solution to prevent problems with the CSRF protection
	#	from Tastypie. Thank you.
	#	"""
	#	@csrf_exempt
	#	def wrapper(request, *args, **kwargs):
	#		return handle_request(request, *args, **kwargs)
	#
	#	return wrapper

	@csrf_exempt
	def handle_request(self, request, *args, **kwargs):
		# not needed anymore. remove. TODO
		#self._clean_error_variables()
		rest_info = RestInformation(self._meta)

		# TODO: Find a better solution for that.
		req_meth = request.method.upper()
		req_type = None
		if 'id' in kwargs:
			req_type = 'object'
		if 'id_list' in kwargs:
			req_type = 'multiple'
		# TODO: Why only GET?
		if req_meth == 'GET' and not kwargs.has_key('id'):
			req_type = 'multiple'

		rest_info.request_method = request.method
		rest_info.request_type = req_type
		rest_info.allowed_methods = self._http_allowed_methods(req_type)

		# TODO: Whats happens e.g. if a PUT request does not point to any resource.
		# Who handles this?

		if not self._check_method(request, req_type):
			return HttpResponseNotAllowed(allow_headers=rest_info.allowed_methods)

		# Add an is_rest() method to the request
		request.is_rest = lambda: True

		# Add the current resource
		request.tmp_resource = self # TODO: This should not be needed anymore!
		request.rest_info = rest_info

		# An exception signals malformed input data resulting
		# in a 400 Bad Request response.
		try:
			self.read_raw_data(request)
		except Exception, e:
			if settings.DEBUG and self.display_errors:
				raise
			else:
				return HttpResponseBadRequest()

		#self._handle_put_request(request)

		try:
			handling_method = self._wrapper.get_handler_for('%s_%s' % (req_meth, req_type))
		except AttributeError:
			if settings.DEBUG and self.display_errors:
				raise
			else:
				raise Http404()
		import inspect # TODO: delete

		# TODO delete
		print "%s (%s): %s" % (inspect.getframeinfo(inspect.currentframe()).filename, inspect.getframeinfo(inspect.currentframe()).lineno, handling_method)

		self.pre_view(request)

		handling_exception = None
		response = None
		try:
			response = handling_method(request, *args, **kwargs)
		except AttributeError, e:
			# Most probably this signals a malformed chain of commands.
			if settings.DEBUG and self.display_errors:
				raise
			else:
				return HttpResponseNotImplemented()
		except Exception, e:
			# TODO: Remove
			print "DO SOMETHING HERE!!!! %s" % (e,)
			rest_info._has_errors = True
			handling_exception = e
			# TODO: Should that be here?!?
			if settings.DEBUG and self.display_errors:
				raise
			else:
				pass

		self.post_view(
			request=request, 
			response=response, 
			exception=handling_exception
		)

		return self._response_postprocessing(
			request=request, 
			response=response, 
			exception=handling_exception
		)


	def pre_view(self, request):
		pass

	def post_view(self, request, response=None, exception=None):
		"""
		The response can be a NoneType in case the handling_method
		raised an exception.
		"""
		pass

	def read_raw_data(self, request):
		# convert the data into the correct format and add
		# it as POST variables.
		from django.http import QueryDict, MultiValueDict
		print "%s: %s" % (__name__, request.method)
		if not request.method in ['POST', 'PUT']:
			request._post, request._files = QueryDict('', encoding=request._encoding), MultiValueDict()
		else:
			# TODO: multipart (files) not supported.
			d = self._raw_data_to_dict(request)
			if isinstance(d, list):
				d = dictionize_list_for_formsets(d)
			print d
			q = QueryDict('', encoding=request._encoding).copy()
			q.update(d)
			request.method = 'POST'
			request._post = q
			request._files = MultiValueDict()

	def _response_postprocessing(self, request, response=None, exception=None):
		"""
		Processes the response of the handling method to ensure that we always
		return a REST compliant response.

		We expect one of the following results from the handling method:
		 
		- a 2xx response
		- a 2xx response with an invalid form
		- an arbitrary unhandled exception
		- an Http404 exception
		- a 3xx response (redirect)
		- a 4xx or 5xx error code
		- a response object which is not an HttpResponse instance
		
		Did we miss something?
		"""
		# TODO: Restructure error handling. It is messed up.

		if not response and not exception:
			return HttpResponseServerError()

		if isinstance(response, RestResponse):
			response = self._rest_to_http_response(request, response)

		# TODO: decide for a variable name
		#if self._sloppy_response:
		if False:
			if response:
				return response
			else:
				raise exception

		if (exception and isinstance(exception, Http404)) or \
		(response and response.status_code == 404):
			return HttpResponseNotFound()

		if response and response.status_code == 500:
			return HttpResponseServerError()

		if request.rest_info._has_errors:
			response = HttpResponse(status=403)
			# TODO: Return error dict in the correct format!
			from django.utils import simplejson
			response.content = simplejson.dumps(request.rest_info._error_dict)
			return response

		# A view should always return a valid HttpResponse. However, it is up
		# to the user if he requires a valid response or not. Otherwise
		# we just return an empty response.
		if response and not isinstance(response, HttpResponse):
			if settings.DEBUG and self.display_errors:
				return response
			else:
				return HttpResponseServerError()
			#if self._meta.valid_response_required:
			#	# TODO: error!
			#	return HttpResponseNoContent()
			#else:
			#	return HttpResponseNoContent()

		if response.status_code >= 300 and response.status_code < 400:
			# TODO: if rediret_as_error is defined one has to assure that
			# rediret_as_error_errocode is also defined.
			if self._meta.redirect_as_error:
				#return HttpResponseResponse(status=self._meta.redirect_as_error_code)
				# ...right?
				return HttpResponse(status=self._meta.redirect_as_error_code)

		if request.rest_info.request_method == 'DELETE':
				if response.status_code == 200 and not self._meta.include_object_in_response:
					return HttpResponseNoContent()
		elif request.rest_info.request_method in ['POST', 'PUT']:
				if response.status_code == 200:
					# TODO: This is wrong. PUT should ONLY return 201 if a new 
					# object is created. otherwise it should return 200 (ok) or
					# 204 (no content) if no content is included.
					# TODO: We need a possibility to distinguish whether the object
					# has been updated or newly created.
					if self._meta.include_object_in_response:
						response.status_code = 201
					else:
						return HttpResponseCreated()

		# Responses with 1xx do not make sense. And the HttpRequest class of Django
		# has no ability to check for the protocol version. Which is required, as
		# Http/1.0 does not now about 1xx codes.
		if response.status_code >= 100 and response.status_code < 200:
			return HttpResponseServerError()

		# The following response codes do not require any content (however, most of them should contain information). Thus,
		# we clear the content and forward the response. In case the user wants to return content he should take of
		# that manually.
		CODES_WITHOUT_CONTENT = [202, 203, 204, 205, 300, 301, 302, 303, 307, 406, 407, 408, 409, 410, 411, 412, 413, 414, 416, 417, 501, 502, 503, 504, 505]
		if response.status_code in CODES_WITHOUT_CONTENT:
			response.content = ''

		# The following codes require additional checking.
		if response.status_code == 206 and not (\
		(response.get('Content-Range', None) or response.get('Content-type', None) == 'multipart/byteranges') and \
		(response.get('Date', None)) and \
		(response.get('ETag', None) or response.get('Content-Location', None)) and \
		(response.get('Expires', None) and response.get('Cache-Control') or response.get('Vary', None))):	
			return HttpResponseServerError()
		elif response.status_code == 401 and not response.get('WWW-Authenticate', None):
			# TODO: Check header
			return HttpResponseServerError()
		# the "None" in HttpResponse.get() is necessary for Django versions < 1.4
		elif response.status_code == 405 and not response.get('Allow', None):
			return HttpResponseServerError()
		elif response.status_code == 200:
			# TODO: Check on a if the content-type matches the requested one on a code 200.
			return response
		else:
			response.content = ''

		return response

	def _http_allowed_methods(self, req_type):
		return list(set(i.split('_')[0] for i in self._meta.allowed_methods if len(i.split('_')) == 1 or i.split('_')[1] == req_type))

	def _raw_data_to_dict(self, request):
		from django.utils import simplejson
		# TODO: determine format and return correctly. encoding?
		print request.raw_post_data
		d = simplejson.loads(request.raw_post_data)
		print d
		return d
		
	def _check_method(self, request, req_type):
		"""
		Checks if the request method is allowed.
		"""
		req_meth = request.method.upper()

		full_req_type = "%s_%s" % (req_meth, req_type)
		print req_meth
		print full_req_type
		return (
			full_req_type in self._meta.allowed_methods or \
			req_meth in self._meta.allowed_methods
		)

	def _handle_put_request(self, request):
		"""
		Django does not handle PUT requests and only populates "raw_post_data"
		on POST requests. It uses the variables "_post" and "_files" to 
		check weather the fields have been populated. Hence, we remove 
		those variables and reload the input data.
		"""
		# TODO: Check if this method is still needed! Compare with read_raw_data
		if not request.method == 'PUT':
			return

		# Someone already tried to read the data but failed with an error.
		if hasattr(request, '_post') and hasattr(request, '_post_parse_error'):
			raise 

		try:
			del request._post
			del request._files
		except AttributeError:
			pass

		# Fake a POST otherwise _load_post_and_files does not load any data.
		request.method = 'POST'
		request._load_post_and_files()

		# And back to PUT
		request.method = 'PUT'
		request.PUT = request.POST

	def _rest_to_http_response(self, request, restresponse):
		# TODO: What happens if the is no data attribute?
		data = restresponse.data
		print type(data)
		if self._meta.model:
			if isinstance(data, QuerySet):
				if data.model != self._meta.model:
					# TODO appropriate http error response
					return HttpResponseNotFound()
			elif isinstance(data, list):
				if not isinstance(all(data), self._meta.model):
					# TODO appropriate http error response
					return HttpResponseNotFound()
			elif not isinstance(data, self._meta.model):
				print data
				print self._meta.model
				# TODO appropriate http error response
				return HttpResponseNotFound()

		# TODO: form errors

		frmt = self.get_format(request)
		# TODO : What if frmt does not exist
		# TODO : What if the serializer does not exist?
		# TODO : inline is missing
		print self._meta.fields
		print self._meta.exclude
		print self._meta.reverse_fields
		print self._meta.inline
		print self._meta.map_fields
		s = serializers.serialize('rest%s' % (frmt), data, fields=self._meta.fields, exclude=self._meta.exclude, reverse_fields=self._meta.reverse_fields, inline=self._meta.inline, map_fields=self._meta.map_fields, extra=self._meta.extra_fields)
		# TODO: determine the content-type from frmt!
		return HttpResponse(s, content_type='application/json; charset=utf-8')
