from django.core.serializers import python, json
from django.utils.encoding import smart_unicode, is_protected_type
from django.utils import simplejson

class Serializer(python.Serializer):
	"""
	This is the base for all REST serializers.
	"""
	internal_use_only = False	

	def serialize(self, queryset, **options):
		# We added the possibility to exclude fields. The handling is done
		# in the start_object method.
		self.excluded_fields = options.pop('exclude', None)
		self.map_fields = options.pop('mapfields', None) # "map" is reserved!
		self.inline = options.pop('inline', None)
		
		try:
			iter(queryset)
		except TypeError:
			# We are asked to serialize an object instead of an iterable.
			self.single_object = True
			return super(Serializer, self).serialize([queryset,], **options)
		else:
			self.single_object = False
			return super(Serializer, self).serialize(queryset, **options)

	def start_serialization(self):
		super(Serializer, self).start_serialization()
		if self.selected_fields and self.excluded_fields:
			# Remove the excluded fields from the list of selected fields.
			self.selected_fields = list(
				set(self.selected_fields).difference(set(self.excluded_fields))
			)

	def start_object(self, obj):
		super(Serializer, self).start_object(obj)
		# We have no fields defined but we want to exclude fields. Thus, we
		# have to grab the list of all fields and exclude the required ones.
		if not self.selected_fields and self.excluded_fields:
			self.selected_fields = list(
				set(obj._meta.get_all_field_names()).difference(set(self.excluded_fields))
			)

	def end_object(self, obj):
		# Add the primary with its proper field name to the list of fields.
		self._current[obj._meta.pk.name] = smart_unicode(obj._get_pk_val(), strings_only=True)
		if self.map_fields:
			for key,value in self.map_fields.iteritems():
				if self._current.has_key(key):
					self._current[value] = self._current[key]
					del self._current[key]
		super(Serializer, self).end_object(obj)
		
	def end_serialization(self):
		super(Serializer, self).end_serialization()
		self.objects = [i['fields'] for i in self.objects]

		if self.single_object:
			self.objects = self.objects[0]

	def handle_fk_field(self, obj, field):
		if self.inline:
			tmpserializer = self.__class__()
			fields, exclude, maps = None, None, {}
			# fields, exclude, map, inline
			field_option_name = field.name + '__'
			if self.selected_fields:
				fields = [i.replace(field_option_name,'') for i in self.selected_fields if i.startswith(field_option_name)]
			if self.excluded_fields:
				exclude = [i.replace(field_option_name,'') for i in self.excluded_fields if i.startswith(field_option_name)]
			if self.map_fields:
				for k,v in self.map_fields.iteritems():
					if k.startswith(field_option_name) and v.startswith(field_option_name):
						maps[k.replace(field_option_name, '')] = v.replace(field_option_name, '')
			print maps
				
			self._current[field.name] = tmpserializer.serialize(getattr(obj, field.name), inline=self.inline, fields=fields, exclude=exclude, mapfields=maps)
		else:
			super(Serializer, self).handle_fk_field(obj, field)

