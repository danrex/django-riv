from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.importlib import import_module
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseServerError, HttpResponseNotFound, HttpResponseBadRequest
from django.forms.models import modelform_factory, modelformset_factory
from django.utils import simplejson
from django.shortcuts import get_object_or_404
from riv.http import HttpResponseConflict, HttpResponseNotImplemented, HttpResponseNotAllowed, HttpResponseNoContent


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


class StandaloneWrapper(BaseWrapper):

	def read(self, request, *args, **kwargs):
		rest_info = request.rest_info
		if not rest_info:
			# This should never happen.
			return HttpResponseServerError()
		if not getattr(rest_info, 'model') or not rest_info.model:
			# This is a misconfiguration.
			return HttpResponseServerError()
		else:
			model = rest_info.model

		if 'id' in kwargs:
			try:
				q = model.objects.get(pk=kwargs.get('id'))
			except ObjectDoesNotExist:
				return HttpResponseNotFound('An object with id %s does not exist.' % (kwargs.get('id')))
			except MultipleObjectsReturned:
				# Should never happen, as we are looking for the primary key.
				return HttpResponseServerError()
		elif 'id_list' in kwargs:
			q = model.objects.filter(id__in=kwargs.get('id_list').split(';'))
		else:
			q = model.objects.all()

		# TODO: Who takes care if the queryset is empty? 404..
		rest_info.queryset = q
		# TODO: return type? always json?!
		return HttpResponse(request.tmp_resource.as_json(q), content_type='application/json; charset=utf-8')
		# TODO. (1) shortcut to add queryset in call, e.g. resource.as_json(queryset)
		# TODO. (2) shortcut. leave format to resource: resource.return(queryset)

	# TODO: What if the users wants to create 2 similar objects? Shouldn't we allow it?
	def create(self, request, *args, **kwargs):
		rest_info = request.rest_info
		if not rest_info:
			# This should never happen.
			return HttpResponseServerError()
		if not getattr(rest_info, 'model') or not rest_info.model:
			# This is a misconfiguration.
			return HttpResponseServerError()
		else:
			model = rest_info.model

		ModelFormSet = modelformset_factory(model)

		if not request.method == 'POST':
			# This is actually a misconfiguration. If this method is
			# called without POST someone played around with the
			# BaseWrapper.handler_methods dictionary.
			return HttpResponseNotAllowed(rest_info.allowed_methods)

		formset = ModelFormSet(request.POST, request.FILES)
		print formset.is_valid()
		print formset.errors
		if formset.is_valid():
			objects = formset.save()
			url_list = []
			for obj in objects:
				print obj
				url_list.append("%s%s" % (request.get_full_path(), obj.id))
				print url_list
			#format = resource.get_format(request) # TODO...
			format = 'json'
			if format == 'json':
				return HttpResponse(simplejson.dumps(url_list))
			else:
				return # TODO
		else:
			rest_info.error_by_form(formset)
			return HttpResponse()

	def update(self, request, *args, **kwargs):
		rest_info = request.rest_info
		if not rest_info:
			# This should never happen.
			return HttpResponseServerError()
		if not getattr(rest_info, 'model') or not rest_info.model:
			# This is a misconfiguration.
			return HttpResponseServerError()
		else:
			model = rest_info.model

		# Put requests have to point to a resource entity and not to
		# a handler resource. Thus, the indication of an id is
		# mandatory.
		try:
			entity_id = int(kwargs['id'])
		except KeyError, e:
			return HttpResponseNotAllowed(rest_info.allowed_methods)
		except (ValueError, TypeError), e:
			return HttpResponseBadRequest()

		ModelForm = modelform_factory(model)

		if not request.method == 'POST':
			# This is actually a misconfiguration. If this method is
			# called without POST(*) someone played around with the
			# BaseWrapper.handler_methods dictionary.
			#
			# (*) Actually this handler is called via "PUT" but Django
			# is not capable of handling PUT requests. Thus, we 
			# changed the request type to POST for views.
			return HttpResponseNotAllowed(rest_info.allowed_methods)

		# TODO: Here it has to be decided whether the application
		# wants to allow the creation of a new entity with a given
		# id from the outside world.
		#entity = model.objects.get(pk=entity_id)
		entity = get_object_or_404(model, pk=entity_id)

		form = ModelForm(request.POST, instance=entity)

		if form.is_valid():
			e = form.save()
			# TODO: Should we leave this to the Resource?
			if rest_info.include_object_in_response:
				# TODO: format = resource.get_format(request)
				format = 'json'
				if format == 'json':
					# TODO: very temporary... no serializer available, yet.
					from django.core import serializers
					return HttpResponse(serializers.serialize("json", [ e, ]))
				else:
					return # TODO
			else:
				return HttpResponseNoContent() # according to rfc2616
		else:
			rest_info.error_by_form(form)
			return HttpResponse()

	def update_multiple(self, request, *args, **kwargs):
		# TODO: This has to be implemented. ModelFormSets now if they
		# have to create or update an entity by the hidden submission
		# of the id: <input type="hidden" name="form-0-id" id="id_form-0-id" />
		# Thus, we have to add the ids from the URI as POST values or
		# as the sender to include the id in each entity (which makes more
		# sense. But is against the HTTP-PUT specification.
		#
		# TODO: Review (incomplete) code below.
		#
		rest_info = request.rest_info
		if not rest_info:
			# This should never happen.
			return HttpResponseServerError()
		if not getattr(rest_info, 'model') or not rest_info.model:
			# This is a misconfiguration.
			return HttpResponseServerError()
		else:
			model = rest_info.model

		# Put requests have to point to a resource entity and not to
		# a handler resource. Thus, the indication of an id is
		# mandatory.
		if not kwargs.get('id') or not kwargs.get('id_list'):
			return HttpResponseNotAllowed(rest_info.allowed_methods)

		ModelFormSet = modelformset_factory(model)

		if not request.method == 'POST':
			# This is actually a misconfiguration. If this method is
			# called without POST* someone played around with the
			# BaseWrapper.handler_methods dictionary.
			#
			# * Actually this handler is called via "PUT" but Django
			# is not capable of handling PUT requests. Thus, we 
			# changed the request type to POST for views.
			return HttpResponseNotAllowed(rest_info.allowed_methods)

		formset = ModelFormSet(request.POST, request.FILES)
		print formset.is_valid()
		print formset.errors
		if formset.is_valid():
			objects = formset.save()
			url_list = []
			for obj in objects:
				print obj
				url_list.append("%s%s" % (request.get_full_path(), obj.id))
				print url_list
			#format = resource.get_format(request) # TODO.
			format = 'json'
			if format == 'json':
				return HttpResponse(simplejson.dumps(url_list))
			else:
				return # TODO
		else:
			rest_info.error_by_form(formset)
			return HttpResponse()

	def delete(self, request, *args, **kwargs):
		rest_info = request.rest_info
		if not rest_info:
			# This should never happen.
			return HttpResponseServerError()
		if not getattr(rest_info, 'model') or not rest_info.model:
			# This is a misconfiguration.
			return HttpResponseServerError()
		else:
			model = rest_info.model

		if 'id' in kwargs:
			try:
				q = model.objects.get(pk=kwargs.get('id'))
			except ObjectDoesNotExist:
				return HttpResponseNotFound('An object with id %s does not exist.' % (kwargs.get('id')))
			except MultipleObjectsReturned:
				# Should never happen, as we are looking for the primary key.
				return HttpResponseServerError()
		elif 'id_list' in kwargs:
			q = model.objects.filter(id__in=kwargs.get('id_list').split(';'))
		else:
			q = model.objects.all()

		q.delete()
		return HttpResponse()
	

	read_multiple = read
	#create_multiple = create # TODO: This is missing.
	delete_multiple = delete
