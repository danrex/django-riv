from django.utils.importlib import import_module
from django.http import Http404
from django.db import transaction

class BaseWrapper(object):

	exclude_create = ['id',]
	fields = []

	handler_methods = {
		'GET': 'read',
		'POST': 'create',
		'PUT': 'update',
		'DELETE': 'delete',
		'GET_multiple': 'read_multiple',
		'POST_multiple': 'create_multiple',
		'PUT_multiple': 'update_multiple',
		'DELETE_multiple': 'delete_multiple',
	}

	def get_handler_for(self, full_req_meth):
		"""
		Tries to find the handler for the given request method. If no 
		specific handler for 'object' or 'multiple' is defined it
		tries to find a common fallback handler for the given
		request method.
		"""
		try:
			view_name = self.handler_methods[full_req_meth]
		except KeyError:
			try:
				# if req_meth does not contain the '_' this results in the
				# same call as above leading to a KeyError.
				view_name = self.handler_methods[full_req_meth.split('_')[0]]
			except KeyError:
				raise AttributeError('Invalid request method: %s' % full_req_meth)

		try:
			callback = self._get_callable(view_name)
		except:
			raise NotImplementedError()
		return callback

	def read(self, request, *args, **kwargs):
		raise Http404()
		from django.contrib import auth
		# This is temporary testing!!
		#user = auth.authenticate(username='cgraf', password='hallo')
		#auth.login(request, user)
		#if 'id' in kwargs:
		#	return client.project(request, projectid=kwargs['id'])
		#else:
		#	return client.list_projects(request)

	def create(self, request, *args, **kwargs):
		raise Http404()

	def update(self, request, *args, **kwargs):
		raise Http404()

	def delete(self, request, *args, **kwargs):
		raise Http404()
	
	# TODO handling of multiple ids. Idea:
	@transaction.commit_manually		
	def create_multiple(self, request, *args, **kwargs):
		#foreach id in ids:
		#   self.create(...)
		#   check_for_error...
		# if error:
		#   transaction.rollback()
		#   return error
		# else:
		#   transaction.commit()
		# ...
		pass

	read_multiple = read
	update_multiple = update
	delete_multiple = delete

	def _get_callable(self, view):
		"""
		This is basically a copy of django.core.urlresolvers.get_callable.
		But this function does not fail on an UnicodeEncodeError. We do.
		"""
		if not callable(view):
			try:
				view = view.encode('ascii')
			except UnicodeEncodeError:
				raise AttributeError, "View %s is non-ascii." % (view,)

			mod_name, func_name = self._get_mod_func(view)
			if func_name == '':
				raise AttributeError, "No function found."

			try:
				if mod_name != '':
					view = getattr(import_module(mod_name), func_name)
				else:
					view = getattr(self, func_name)
				if not callable(view):
					raise AttributeError, "%s.%s is not callable" % (mod_name, func_name)
			except (ImportError, AttributeError):
				raise AttributeError, "Unable to load %s" % view
		return view

	def _get_mod_func(self, mod_func):
		"""
		The get_mod_func function from django.core.urlresolvers converts 'func'
		to ['func', ''] whereas we want ['', 'func'].
		"""
		try:
			dot_pos = mod_func.rindex('.')
		except ValueError:
			return '', mod_func
		return mod_func[:dot_pos], mod_func[dot_pos+1:]

