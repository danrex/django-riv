import django
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseServerError, HttpResponseNotFound
from django.conf import settings
from django.conf.urls.defaults import patterns, url
from django.views.decorators.csrf import csrf_exempt
from django.db.models.query import QuerySet
from django.core import serializers

from riv import RestResponse
from riv.exceptions import ConfigurationError, UnsupportedFormat
from riv.http import HttpResponseNotAllowed, HttpResponseNoContent, HttpResponseCreated, HttpResponseNotImplemented, \
        HttpResponseNotAcceptable, HttpResponseUnsupportedMediaType
from riv.info import RestInformation
from riv.wrappers import BaseWrapper
from riv.mime import formats, get_available_format, get_mime_for_format

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
# - POST is designed to handle a given resource not to point to a resource object
# - If a resource has been created on the origin server, the response SHOULD 
#   be 201 (Created) and contain an entity which describes the status of the 
#   request and refers to the new resource, and a Location header
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
    'name',                         # used to create the URLs. Not tied to any model!
    'api_name',
    'model',
    'reverse',
    'allowed_methods',
    'allow_batch_creation',
    'allow_batch_deletion',
    'render_object_after_post',
    'redirect_as_error',
    'redirect_as_error_code',
    'fallback_on_unsupported_format',
    'valid_response_required',
    'related_as_ids',
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
        self.name = None
        self.model = None
        # Use this resource to reverse URI resolution.
        self.reverse = False
        self.api_name = None
        self.allowed_methods = ['GET', 'POST', 'PUT', 'DELETE']
        # Allow to supply multiple entities on a POST request
        self.allow_batch_creation = False
        # Allow to delete all objects
        self.allow_batch_deletion = False
        self.render_object_after_post = False
        # Treat it as an error using the code if a view returns with a redirect.
        self.redirect_as_error = False
        self.redirect_as_error_code = 401
        # Note: HTTP/1.1 servers are allowed to return responses which are not acceptable 
        # according to the accept headers sent in the request. In some cases, this may 
        # even be preferable to sending a 406 response. User agents are encouraged to 
        # inspect the headers of an incoming response to determine if it is acceptable.
        # -- Uses 'JSON' as fallback or sends a 406 error code if set to false.
        self.fallback_on_unsupported_format = True
        # Still needed?
        self.valid_response_required = False
        # Use just the id to include related objects instead of building a resource URI
        self.related_as_ids = False
        # Only serialize the specified fields.
        self.fields = None # has to be None, because [] reads as "no field"
        # Exclude the specified fields from serialization.
        self.exclude = []
        # Include a serialized version of the given related objects.
        self.inline = []
        # Include the specified reverse relationships in the serialized object.
        self.reverse_fields = []
        # Serialize the following additional attributes.
        self.extra_fields = []
        # Map the following fields to other names.
        self.map_fields = {}

        # apply overridden fields from 'class Meta'.
        self.apply_overrides(meta)

        if self.name is None and getattr(self, 'model', None):
            self.name = getattr(self, 'model', None)._meta.verbose_name

    def apply_overrides(self, meta):
        meta_dict = getattr(meta, '__dict__', None)
        if meta_dict:
            for opt_name in meta_dict:
                if opt_name.startswith('_'):
                    continue
                if opt_name in ALLOWED_OPTIONS:
                    setattr(self, opt_name, meta_dict[opt_name])
                else:
                    raise ConfigurationError('Invalid attribute in Meta: %s' % opt_name)


class ResourceMeta(type):
    """
    Metaclass for Resources.
    """
    def __new__(cls, name, bases, attrs):
        new_class = super(ResourceMeta, cls).__new__(cls, name, bases, attrs)
        meta = getattr(new_class, 'Meta', None)

        new_class._meta = ResourceOptions(meta)

        return new_class

class Resource(object):
    __metaclass__ = ResourceMeta

    _wrapper = BaseWrapper()

    @property
    def __name__(self):
        return type(self).__name__

    @property
    def wrapper(self):
        return self._wrapper

    @wrapper.setter
    def wrapper(self, wrapper):
        self._wrapper = wrapper

    def __init__(self, display_errors=False, name=None):
        if name:
            self._meta.name = name
        self.display_errors = getattr(settings, 'RIV_DISPLAY_ERRORS', display_errors)

    # URL names have the form: (list|object|multiple)-<api_name>-(<model_name>|<resource_name>)
    # When we try to reverse-resolve the URLs for a related object we only know the name of the 
    # object class and the apiname. Thus, we must be able to find the URL using these two 
    # parameters.
    # However, if two resources have NO model attached, they would end up with the same url-name.
    # Thus, in this case we have to use the "name" instead of the "model" to obtain a clean naming
    # scheme.
    def _get_urls(self, reverse=None):
        name = self._meta.name
        reverse = self._meta.reverse or reverse
        if self._meta.model and reverse:
            name = str(self._meta.model._meta)
        return patterns('',
            url(r'^%s/?$' % (self._meta.name), self.handle_request, name='list-%s-%s' % (self._meta.api_name, name)),
            url(r'^%s/(?P<id>\d+)/?$' % (self._meta.name), self.handle_request, name='object-%s-%s' % (self._meta.api_name, name)),
            url(r'^%s/(?P<id_list>\d[;\d]+)/?$' % (self._meta.name), self.handle_request, name='multiple-%s-%s' % (self._meta.api_name, name))
        )
    urls = property(_get_urls)
    # TODO set reverse to True for this one.
    urls_with_reverse = property(_get_urls)

    @csrf_exempt
    def handle_request(self, request, *args, **kwargs):
        rest_info = RestInformation(self._meta)

        req_meth = request.method.upper()
        req_type = self._get_request_type(req_meth, kwargs)

        rest_info.request_method  = req_meth
        rest_info.request_type    = req_type
        rest_info.allowed_methods = self._http_allowed_methods(req_type)
        rest_info.format          = get_available_format(request)

        if not rest_info.format:
            if self._meta.fallback_on_unsupported_format:
                # TODO global constant
                rest_info.format = 'json'
            else:
                return HttpResponseNotAcceptable()


        # TODO Whats happens e.g. if a PUT request does not point to any resource.
        # Who handles this?

        if not self._check_method(req_meth, req_type):
            return HttpResponseNotAllowed(allow_headers=rest_info.allowed_methods)

        # Add an is_rest() method to the request (returning True)
        request.is_rest = lambda: True

        # Make the RestInformation object available in the views.
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

        # TODO delete -- start
        import inspect
        print "%s (%s): %s" % (inspect.getframeinfo(inspect.currentframe()).filename, inspect.getframeinfo(inspect.currentframe()).lineno, handling_method)
        # TODO delete -- end

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
            handling_exception = e

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
        if not request.method in ['POST', 'PUT']:
            request._post, request._files = QueryDict('', encoding=request._encoding), MultiValueDict()
        else:
            # TODO multipart (files) not supported.
            q = QueryDict('', encoding=request._encoding).copy()
            d = self._raw_data_to_dict(request)
            for key in d.keys():
                if isinstance(d[key], list):
                    q.setlist(key, d.pop(key))
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

        if not response and not exception:
            return HttpResponseServerError()

        if isinstance(response, RestResponse):
            response = self._rest_to_http_response(request, response)

        # TODO decide for a variable name
        #if self._sloppy_response:
        if False:
            if response:
                return response
            else:
                raise exception

        if (exception and isinstance(exception, Http404)) or \
        (response and response.status_code == 404):
            return HttpResponseNotFound()

        if exception:
            if settings.DEBUG and self.display_errors:
                raise
            else:
                return HttpResponseServerError()

        if response and response.status_code == 500:
            return HttpResponseServerError()

        # A view should always return a valid HttpResponse. However, it is up
        # to the user if he requires a valid response or not. Otherwise
        # we just return an empty response.
        if response and not isinstance(response, HttpResponse):
            if settings.DEBUG and self.display_errors:
                return response
            else:
                return HttpResponseServerError()
            #if self._meta.valid_response_required:
            #   # TODO: error!
            #   return HttpResponseNoContent()
            #else:
            #   return HttpResponseNoContent()

        if response.status_code >= 300 and response.status_code < 400:
            if self._meta.redirect_as_error:
                if not self._meta.redirect_as_error_code:
                    if settings.DEBUG and self.display_errors:
                        raise ConfigurationError('redirect_as_error defined without redirect_as_error_code')
                    else:
                        raise HttpResponseServerError()
                return HttpResponse(status=self._meta.redirect_as_error_code)

        if request.rest_info.request_method == 'DELETE':
                if response.status_code == 200 and not self._meta.render_object_after_post:
                    return HttpResponseNoContent()
        elif request.rest_info.request_method in ['POST', 'PUT']:
                if response.status_code == 200:
                    # This indicates a new object has been created
                    if request.rest_info.request_type == 'list':
                        response.status_code = 201
                    elif response.content == '':
                        return HttpResponseNoContent()

        # Responses with 1xx do not make sense. And the HttpRequest class of Django
        # has no ability to check for the protocol version. Which is required, as
        # Http/1.0 does not now about 1xx codes.
        if response.status_code >= 100 and response.status_code < 200:
            return HttpResponseServerError()

        # The following response codes do not require any content (however, most of them should contain information). Thus,
        # we clear the content and forward the response. In case the user wants to return content he should take care of
        # that manually.
        # TODO why?
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
            # TODO Check on a if the content-type matches the requested one on a code 200.
            return response

        return response

    def _http_allowed_methods(self, req_type):
        return list(set(i.split('_')[0] for i in self._meta.allowed_methods if len(i.split('_')) == 1 or i.split('_')[1] == req_type))

    def _raw_data_to_dict(self, request):
        try:
            format = formats[request.META.get('CONTENT_TYPE', 'application/json')]
        except KeyError:
            if settings.DEBUG and self.display_errors:
                raise UnsupportedFormat('Format %s is not supported. Check if you included the serializers in the settings file.' % (request.META.get('CONTENT_TYPE', 'application/json')))
            else:
                return HttpResponseUnsupportedMediaType()
        try:
            Loader = serializers.get_serializer('rest%s' % format)().get_loader()
        except serializers.base.SerializerDoesNotExist:
            if settings.DEBUG and self.display_errors:
                raise UnsupportedFormat('Format %s is not supported. Check if you included the serializers in the settings file.' % (format,))
            else:
                return HttpResponseUnsupportedMediaType()
        if django.VERSION[0] == 1 and django.VERSION[1] >= 4:
            data = request.body
        else:
            data = request.raw_post_data
        loader = Loader()
        loader.load(data,
                map_fields=self._meta.map_fields,
                model=self._meta.model,
                fields=self._optionlist_for_type(request.rest_info.request_method, self._meta.fields),
                exclude=self._optionlist_for_type(request.rest_info.request_method, self._meta.exclude)
        )
        if request.rest_info.request_type == 'list':
            return loader.get_querydict(force_batch=self._meta.allow_batch_creation)
        else:
            return loader.get_querydict()

    # TODO this is a helper. should it be here?
    def _optionlist_for_type(self, method, optlist):
        x = lambda e, t: isinstance(e, dict) and not t in e.values()[0]
        obj_or_key = lambda e: isinstance(e, dict) and e.keys()[0] or e
        if isinstance(optlist, list):
            return [obj_or_key(i) for i in optlist if not x(i, method)]
        else:
            return optlist

    def _check_method(self, method, req_type):
        """
        Checks if the request method is allowed.
        """
        full_req_type = "%s_%s" % (method, req_type)
        return (
            full_req_type in self._meta.allowed_methods or \
            method in self._meta.allowed_methods
        )

    def _get_request_type(self, method, kwargs):
        req_type = None
        if 'id' in kwargs:
            req_type = 'object'
        elif 'id_list' in kwargs:
            req_type = 'multiple'
        else:
            req_type = 'list'
            # Batch update/delete is currently not supported, only
            # GET is allowed.
            #if method == 'GET':
            #    req_type = 'multiple'
            #elif method == 'POST':
            #    # A POST without an id creates a new object.
            #    req_type = 'object'
        return req_type

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
        format = request.rest_info.format
        if not format:
            if settings.DEBUG and self.display_errors:
                raise ConfigurationError('No format for the response specified')
            else:
                return HttpResponseServerError()

        response = HttpResponse(content_type=get_mime_for_format(format))

        if restresponse.form and restresponse.form.errors:
            data = {'error': restresponse.form.errors}
            response.status_code = 400
            render_only = True

        if restresponse.content:
            data = restresponse.content
            render_only = not (self._meta.model or False)
            if self._meta.model:
                if isinstance(data, QuerySet):
                    if data.model != self._meta.model:
                        if settings.DEBUG and self.display_errors:
                            raise ConfigurationError('The returned model %s is not compatible with the resources\' model %s' % (data.model, self._meta.model))
                        else:
                            return HttpResponseServerError()
                elif isinstance(data, list):
                    if not all(map(lambda x: isinstance(x, self._meta.model), data)):
                        if settings.DEBUG and self.display_errors:
                            raise ConfigurationError('At least one model in the returned list is not compatible with the resources\' model %s' % (self._meta.model,))
                        else:
                            return HttpResponseServerError()
                elif not isinstance(data, self._meta.model):
                    if settings.DEBUG and self.display_errors:
                        raise ConfigurationError('The returned object\'s model %s is not compatible with the resource model %s' % (type(data), self._meta.model))
                    else:
                        return HttpResponseServerError()

        print data
        print self._meta.fields
        print self._meta.exclude
        print self._optionlist_for_type(request.rest_info.request_method, self._meta.exclude)
        print self._meta.reverse_fields
        print self._meta.inline
        print self._meta.map_fields
        try:
            s = serializers.serialize('rest%s' % (format), 
                data, 
                related_as_ids=self._meta.related_as_ids, 
                api_name=self._meta.api_name, 
                fields=self._optionlist_for_type(request.rest_info.request_method, self._meta.fields),
                exclude=self._optionlist_for_type(request.rest_info.request_method, self._meta.exclude),
                reverse_fields=self._meta.reverse_fields, 
                inline=self._meta.inline, 
                map_fields=self._meta.map_fields, 
                extra=self._meta.extra_fields,
                render_only=render_only
            )
        except serializers.base.SerializerDoesNotExist:
            if settings.DEBUG and self.display_errors:
                raise UnsupportedFormat('Format %s is not supported. Check if you included the serializers in the settings file.' % (format,))
            else:
                return HttpResponseUnsupportedMediaType()
        response.content = s
        return response
