from django.http import HttpResponse

class HttpResponseCreated(HttpResponse):
	status_code = 201

class HttpResponseNoContent(HttpResponse):
	status_code = 204

class HttpResponseNotAllowed(HttpResponse):
	status_code = 405

	def __init__(self, allow_headers):
		super(HttpResponseNotAllowed, self).__init__()
		try:
			iter(allow_headers)
		except TypeError:
			self['Allow'] = allow_headers	
		else:
			self['Allow'] = ", ".join(allow_headers)

class HttpResponseNotAcceptable(HttpResponse):
	status_code = 406

class HttpResponseNotImplemented(HttpResponse):
	status_code = 501
