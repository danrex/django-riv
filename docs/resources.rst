.. _ref-resources:

=========
Resources
=========

Resource Options
================

.. _ref-resource-name:

name
----

This is an arbitrary string that will be used to include
your resource in the URLconf.

.. _ref-resource-model:

model
-----

Tell the resource to that each entity is an object of this
model class.

.. _ref-reverse:

reverse
-------

You can register multiple resources (having different names)
linking to the same model in your API. However, RiV has to know
which of these resources it should use to build resource URIs.

If you register multiple resources linking to the same model
in your API you have to set ``reverse=true`` on **exactly**
one of them. If you have only one resource for a model you can
skip this option.

.. _ref-allowed-methods:

allowed_methods
---------------

Tells RiV which HTTP methods it should provide for this resource. 
Valid options are ``GET``, ``POST``, ``PUT`` and ``DELETE``.

.. _ref-allow-batch-creation:

allow_batch_creation
--------------------

You can allow the creation of multiple objects through a single
``POST`` request. If you set this option to ``true`` you have
to implement the ``create_multiple`` method in your wrapper.

.. _ref-render-object-after-creation:

render_object_after_creation
----------------------------

If you return any objects in your view using the ``render_to_rest``
shortcut RiV will include these objects in the response.

However, for a ``POST`` request you ALWAYS should return the created
object no matter whether you want to display it or not. The reason is
that after a new object has been created through a successful ``POST``
request the HTTP location header should point to that object. RiV 
therefore has to know where to find this object.

As you always return an object from your view you have to use this
option to tell RiV if you also want to include a representation of
this object in the response body.

.. _ref-redirect-as-error:

redirect_as_error
-----------------

Sometimes your view might return a HTTP redirect (3xx) code. Most of
the time this does not make much sense for an API call. Using this 
option you can tel RiV to treat an 3xx code as an error and return
a ``401`` instead.

.. _ref-redirect-as-error-code:

redirect_as_error_code
----------------------

If you set :ref:`ref-redirect-as-error` to ``true`` you can 
specify an alternative error code here.

.. _ref-fallback-on-unsupported-format:

fallback_on_unsupported_format
------------------------------

If the client requests a format that is not supported by RiV an
error code ``415`` is returned to signal that this media type
is not supported. Setting this option to ``true`` you can tell
RiV to return JSON instead.

.. _ref-related-as-ids:

related_as_ids
--------------

Related objects are serializerd as resource URIs if a resource
is registered at your API for that model. Setting this option
to ``true`` RiV will always return just the id of that object.

.. _ref-fields:

fields
------

Explicity define a list of fields you want to show in your API.

Consider you have the following model::

    class MyModel(models.Model):
        user = models.ForeignKey('auth.User')
        name = models.CharField(max_length=200)
        description = models.CharField(max_length=400)
        pub_date = models.DateTimeField('date published')
        public = models.BooleanField()

        def was_published_today(self):
            return self.pub_date.date() == datetime.date.today()

A request might look like this::

    # http://localhost:8000/riv/mymodel/1?format=json
    {
      "user": '/riv/user/1',
      "name": "This is the name",
      "description": "And this is the description field",
      "pub_date": "2011-10-20T19:30:00", 
      "public": true,
      "id": 1, 
    }

Setting::

    fields = ['name', 'pub_date']

Will not display the ``user``, ``description``, ``public``, and 
``id`` fields::

    # http://localhost:8000/riv/mymodel/1?format=json
    {
      "name": "This is the name",
      "pub_date": "2011-10-20T19:30:00", 
    }


.. _ref-exclude:

exclude
-------

Using this option you can explictly remove fields from your data
representation. 

Consider the example in the :ref:`ref-fields`
section. With the setting::

    exclude = ['user', 'pub_date', 'public']

Will exclude these fields and display all others::

    # http://localhost:8000/riv/mymodel/1?format=json
    {
      "name": "This is the name",
      "description": "And this is the description field",
      "id": 1, 
    }


.. _ref-inline:

inline
------

Foreign keys or many-to-many fields will be included either as
ids or resource URIs. However, you can tell RiV to include
a fully serialized version of that object as well.

**Important**: ``ref-inline`` requires you to create a resource for
the object you want to include because RiV needs to know how
to serialize that object.

Consider the example in the :ref:`ref-fields`
section with the setting::

    inline = ['user']

The call will result in::

    # http://localhost:8000/riv/mymodel/1?format=json
    {
      "user": {
        "first_name": "Paul",
        "last_name": "Peters",
        # ...
      },
      "name": "This is the name",
      "description": "And this is the description field",
      "pub_date": "2011-10-20T19:30:00", 
      "public": true,
      "id": 1, 
    }

.. _ref-reverse-fields:

reverse_fields
--------------

If your model is used as a foreign key in another model you
can also add reverse relationships by adding the name of the
corresponding model to ``reverse_fields``.

.. _ref-extra-fields:

extra_fields
------------

You can tell RiV to include the string representation of fields
that are not part of your model definition. If the specified
field is a callable RiV will call that method and include
the result.

Consider the example in the :ref:`ref-fields`
section with the setting::

    extra_fields = ['was_published_today']

The call will result in::

    # http://localhost:8000/riv/mymodel/1?format=json
    {
      "user": '/riv/user/1',
      "name": "This is the name",
      "description": "And this is the description field",
      "pub_date": "2011-10-20T19:30:00", 
      "public": true,
      "was_published_today": false,
      "id": 1, 
    }

.. _ref-map-fields:

map_fields
----------

One of the most powerful options in RiV is ``map_fields``. It
can serve various purposes. 

You can simply rename fields. Consider the example in the :ref:`ref-fields`
section with the setting::

    map_fields = {'user': 'owner'}

The call will result in::

    # http://localhost:8000/riv/mymodel/1?format=json
    {
      "owner": '/riv/user/1',
      "name": "This is the name",
      "description": "And this is the description field",
      "pub_date": "2011-10-20T19:30:00", 
      "public": true,
      "was_published_today": false,
      "id": 1, 
    }

If you used :ref:`ref-inline` to include a full representation
of an foreign key or m2m object you can use ``map_fields``
to rename attributes of that object as well.

Consider the example in the :ref:`ref-fields`
section with the setting::

    # This is required!
    inline = ['user']
    map_fields = {'user__first_name': 'user__preferred_name'}

The call will result in::

    # http://localhost:8000/riv/mymodel/1?format=json
    {
      "user": {
        "preferred_name": "Paul",
        "last_name": "Peters",
        # ...
      },
      "name": "This is the name",
      "description": "And this is the description field",
      "pub_date": "2011-10-20T19:30:00", 
      "public": true,
      "was_published_today": false,
      "id": 1, 
    }

If you used :ref:`ref-inline` to include a full representation
of an foreign key or m2m object you can use ``map_fields``
to move fields between any related object and your main object.

Consider the example in the :ref:`ref-fields`
section with the setting::

    # This is required!
    inline = ['user']
    map_fields = {'user__first_name': 'username'}

The call will result in::

    # http://localhost:8000/riv/mymodel/1?format=json
    {
      "user": {
        "last_name": "Peters",
        # ...
      },
      "username": "Paul",
      "name": "This is the name",
      "description": "And this is the description field",
      "pub_date": "2011-10-20T19:30:00", 
      "public": true,
      "was_published_today": false,
      "id": 1, 
    }

