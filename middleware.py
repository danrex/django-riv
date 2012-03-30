class RivMiddleware(object):

	def process_view(self, request, view_func, view_args, view_kwargs):
		request.is_rest = lambda: False
