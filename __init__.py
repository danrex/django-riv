class RestResponse(object):

	def __init__(self, content=None, form=None):
		self.data = content
		self.form = form
