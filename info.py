class RestInformation(object):
	"""
	Contains additional information about the current request and the
	processing state, that can be useful to the REST handling classes.

	TODO: Why? -- RestInformation is a dictionary-like object.
	"""

	def __init__(self, meta):
		self._resource_meta = meta
		self._queryset = None
		self._has_errors = False
		self._error_dict = {}

		self.request_method = None
		# None, 'object', or 'multiple
		self.request_type = None
		self.allowed_methods = []

	@property
	def queryset(self):
		return self._queryset

	@queryset.setter
	def queryset(self, queryset):
		from django.db.models import Model
		from django.db.models.query import QuerySet
		if getattr(self._resource_meta, 'readonly_queryset', None):
			raise AttributeError('attribute is read only')

		if not isinstance(queryset, Model) and not isinstance(queryset, QuerySet):
			raise AttributeError('invalid type: %s' % queryset.__class__)

		if self._resource_meta.model:
			if isinstance(queryset, QuerySet):
				cls = queryset.model
			else:
				cls = type(queryset)

			self._check_model_type(cls)
		self._queryset = queryset

	@queryset.deleter
	def queryset(self):
		del _queryset

	@property
	def model(self):
		return self._resource_meta.model

	@property
	def include_object_in_response(self):
		return self._resource_meta.include_object_in_response

	@property
	def error(self):
		return self._has_errors

	@error.setter
	def error(self, err):
		self._has_errors = err

	def _clean_error_variables(self):
		self._has_errors = False
		self._error_dict = {}

	def error_by_list(self, list):
		self._has_errors = True
		self._error_dict = {'errors': list}
		return

	def error_by_form(self, form):
		self._has_errors = True
		self._error_dict = form.errors
		return

	def _check_model_type(self, m):
		if m.__name__.lower() != self._resource_meta.model.__name__.lower():
			raise ValueError('Invalid object-type: %s. Required type is: %s.' % (m.__name__, self._resource_meta.model.__name__))

	#def __getitem__(self, key):
	#	pass

	#def __setitem__(self, key, value):
	#	pass

	#def __delitem__(self, key):
	#	pass

	#def __contains__(self, key):
	#	pass

	#def get(self, key, default=None):
	#	pass

	#def pop(self, key):
	#	pass

	#def keys(self):
	#	pass

	#def items(self):
	#	pass

	#def setdefault(self):
	#	pass
