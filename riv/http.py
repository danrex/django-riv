from django.http import HttpResponse

class HttpResponseCreated(HttpResponse):
    status_code = 201

class HttpResponseNoContent(HttpResponse):
    status_code = 204

class HttpResponseNotAllowed(HttpResponse):
    status_code = 405

    def __init__(self, allow_headers):
        """
        RFC2616: The response MUST include an Allow header containing 
        a list of valid methods for the requested resource. 
        """
        super(HttpResponseNotAllowed, self).__init__()
        try:
            iter(allow_headers)
        except TypeError:
            self['Allow'] = allow_headers   
        else:
            self['Allow'] = ", ".join(allow_headers)

class HttpResponseNotAcceptable(HttpResponse):
    status_code = 406

class HttpResponseConflict(HttpResponse):
    status_code = 409

class HttpResponseUnsupportedMediaType(HttpResponse):
    status_code = 415

class HttpResponseNotImplemented(HttpResponse):
    status_code = 501
