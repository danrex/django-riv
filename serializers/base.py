from django.db.models import Model
from django.core.serializers import python, json
from django.utils.encoding import smart_unicode, is_protected_type
from django.utils import simplejson

from riv.utils import traverse_dict

class Serializer(python.Serializer):
	"""
	This is the base for all REST serializers.
	"""
	internal_use_only = False	
	separator = '__'

	def serialize(self, queryset, **options):
		# The "fields" option is handled by the superclass serializer.
		#
		# We added the possibility to exclude fields. The handling is done
		# in the start_object method.
		self.excluded_fields = options.pop('exclude', None)
		self.map_fields = options.pop('map_fields', None) # "map" is reserved!
		self.extra_fields = options.pop('extra', None)
		self.inline = options.pop('inline', [])
		self.reverse_fields = options.pop('reverse_fields', [])

		# If inline is True, each ForeignKey and ManyToMany field is 
		# serialized using a new Serializer. 
		# Reverse relationships include a ForeignKey/M2M back to the current
		# object which is then serialized again. That results in an infinte
		# loop. Thus, we only serialize FK/M2M/REV relationships, if reverse
		# is set to False.
		#self.reverse = options.pop('reverse', None)
		
		serializee = None
		try:
			iter(queryset)
		except TypeError:
			# We are asked to serialize an object instead of an iterable.
			self.single_object = True
			serializee = [queryset,]
		else:
			self.single_object = False
			serializee = queryset
		return super(Serializer, self).serialize(serializee, **options)

	def start_serialization(self):
		super(Serializer, self).start_serialization()
		if self.selected_fields and self.excluded_fields:
			# Remove the excluded fields from the list of selected fields.
			self.selected_fields = list(
				set(self.selected_fields).difference(set(self.excluded_fields))
			)

	def start_object(self, obj):
		super(Serializer, self).start_object(obj)
		try:
			self.serialize_reverse_fields(obj)
		except AttributeError:
			# fail silently. This method will be applied to all foreignkeys
			# and many-to-many items as well (when asked for inline serialization)
			# Thus, we have to ensure to fail silently because most likely
			# they will not have the same reverse many-to-many relationship.
			pass
		# We have no fields defined but we want to exclude fields. Thus, we
		# have to grab the list of all fields and exclude the required ones.
		if not self.selected_fields and self.excluded_fields:
			self.selected_fields = list(
				set(obj._meta.get_all_field_names()).difference(set(self.excluded_fields))
			)

	def end_object(self, obj):
		# Add the primary key with its proper field name to the list of fields.
		self._current[obj._meta.pk.name] = smart_unicode(obj._get_pk_val(), strings_only=True)
		if self.extra_fields:
			for field in self.extra_fields:
				if getattr(obj, field, None):
					self._current[field] = getattr(obj, field, None)
		if self.map_fields:
			for key,value in self.map_fields.iteritems():
				if self._current.has_key(key):
					self._current[value] = self._current[key]
					del self._current[key]
				elif self.separator in key and self._current.has_key(key.split(self.separator)[0]):
					if self.separator in value:
						# Crossmapping between different ForeignKey objects
						# is currently not supported.
						continue
					key_list = key.split(self.separator)
					try:
						# Walk down the dictionaries and return the value.
						self._current[value] = traverse_dict(self._current, key_list)
						# Then, walk down the dictionaries and remove the key.
						print "-------"
						print self._current
						print key_list
						print traverse_dict(self._current, key_list, return_parent=True)
						del traverse_dict(self._current, key_list, return_parent=True)[key_list[-1]]
					except KeyError:
						# TODO also fail silently if Debug==True?
						pass
		super(Serializer, self).end_object(obj)
		
	def end_serialization(self):
		super(Serializer, self).end_serialization()
		self.objects = [i['fields'] for i in self.objects]

		if self.single_object:
			self.objects = self.objects[0]

	def handle_fk_field(self, obj, field):
		if field.name in self.inline:
			tmpserializer = Serializer()
			fields, exclude, maps, inline = self._get_serialize_options_for_subfield(field.name)
			self._current[field.name] = tmpserializer.serialize(
				getattr(obj, field.name), 
				inline=inline, 
				fields=fields, 
				exclude=exclude, 
				map_fields=maps,
			)
		else:
			super(Serializer, self).handle_fk_field(obj, field)


	def handle_m2m_field(self, obj, field):
		print field.name
		print self.inline
		if field.name in self.inline:
			tmpserializer = Serializer()
			fields, exclude, maps, inline = self._get_serialize_options_for_subfield(field.name)
			self._current[field.name] = [tmpserializer.serialize(
				related,
				inline=inline, 
				fields=fields, 
				exclude=exclude, 
				map_fields=maps,
			) for related in getattr(obj, field.name).iterator()]
		else:
			super(Serializer, self).handle_m2m_field(obj, field)

	def serialize_reverse_fields(self, obj):
		for fieldname in self.reverse_fields:
			if fieldname in self.inline:
				tmpserializer = Serializer()
				fields, exclude, maps, inline = self._get_serialize_options_for_subfield(fieldname)
				#self._current[fieldname] = []
				#for related in getattr(obj, fieldname).iterator():
				#	# Get all fields from the "related" object that have a relation
				#	# to the current "obj" and exlude this field. Otherwise we will 
				#	# end up in an infinite loop. 
				#	rel_exclude = [x.name for x in related._meta.local_fields if x.rel and isinstance(obj, x.rel.to)]
				#	if exclude and rel_exclude:
				#		exclude.extend(rel_exclude)
				#	else:
				#		exclude = rel_exclude
				#	print exclude
				if isinstance(getattr(obj, fieldname), Model):
					self._current[fieldname] = tmpserializer.serialize(
						getattr(obj, fieldname),
						inline=inline, 
						fields=fields, 
						exclude=exclude,
						map_fields=maps,
					)
				else:
					self._current[fieldname] = [tmpserializer.serialize(
						related,
						inline=inline, 
						fields=fields, 
						exclude=exclude,
						map_fields=maps,
					) for related in getattr(obj, fieldname).iterator()]
			else:
				if isinstance(getattr(obj, fieldname), Model):
					self._current[fieldname] = getattr(obj, fieldname)._get_pk_val()
				else:
					self._current[fieldname] = [related._get_pk_val() for related in getattr(obj, fieldname).iterator()]
			

	def _get_serialize_options_for_subfield(self, name):
			fields, exclude, maps, inline = None, None, {}, []
			field_option_name = name + self.separator
			if self.selected_fields:
				fields = [i.replace(field_option_name,'') for i in self.selected_fields if i.startswith(field_option_name)]
			if self.excluded_fields:
				exclude = [i.replace(field_option_name,'') for i in self.excluded_fields if i.startswith(field_option_name)]
			if self.inline:
				inline = [i.replace(field_option_name,'') for i in self.inline if i.startswith(field_option_name)]
			if self.map_fields:
				for k,v in self.map_fields.items():
					if k.startswith(field_option_name) and v.startswith(field_option_name):
						# Remove the key from the original list of fields. It
						# has been handled here.
						del self.map_fields[k]
						maps[k.replace(field_option_name, '')] = v.replace(field_option_name, '')
			return fields or None, exclude or None, maps, inline
