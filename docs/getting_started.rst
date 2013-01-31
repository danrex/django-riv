.. _ref-getting_started:

===============
Getting started
===============

Requirements
============

RIV does not require any additional third party modules. The serializers
are built on top of the built-in Django serializers and therefore 
share the same requirements.

Installation
============

1. Pull django-riv from GitHub
2. Install using::

    sudo python setup.py install

   This also makes sure the required modules get installed automatically

Configuration
=============

#. Add RiV to the list of your installed apps::

    # settings.py
    INSTALLED_APPS = (
      # ...
      'riv'
    )

#. Add the RivMiddleware to the end of your middleware classes::

    # settings.py
    MIDDLEWARE_CLASSES = (
      'django.middleware.common.CommonMiddleware',
      # ...
      'riv.middleware.RivMiddleware'
    )

#. The RiV serializers extend the builtin Django serializers. Add them
to the list of ``SERIALIZATION_MODULES``::

    # settings.py
    SERIALIZATION_MODULES = {
      'restjson': 'riv.serializers.json_serializer',
      'restxml':  'riv.serializers.xml_serializer'
    }


#. For debugging purposes you can tell RIV to display errors. However,
for security reasons this setting only has an effect if Django is
running in debug mode::

    # settings.py
    RIV_DISPLAY_ERRORS = True


Creating resources
==================

Add a resources.py file to your application and add a resource for each
model. Each resource needs to set a wrapper class that links your views
to the HTTP methods (will we create them in the next step)::


    # myapp/resources.py
    from riv.resources import Resource
    from myapp.models import MyModel, MyOtherModel
    from myapp.wrappers import MyModelWrapper, MyOtherModelWrapper

    class MyModelResource(Resource):
      _wrapper = MyModelWrapper()
      class Meta:
        name = 'mymodel'
        model = MyModel

    class MyOtherModelResource(Resource):
      _wrapper = MyOtherModelWrapper()
      class Meta:
        name = 'myothermodel'
        model = MyOtherModel

Using wrappers to link to views
===============================

A wrapper should be derived from the ``BaseWrapper`` class. The wrapper can 
define the following methods:

* ``read`` (for GET requests with an id)
* ``read_multiple`` (for GET requests without an id or multiple ids)
* ``create`` (for POST requests)
* ``create_multiple`` (for POST requests containing an array of objects. You have 
  to set the :ref:`ref-allow-batch-creation` option if you want to support this. See
  the :ref:`ref-resources` documentation for details)
* ``update`` (for PUT requests with an id)
* ``update_multiple`` (for PUT requests with multiple ids)
* ``delete`` (for DELETE requests with an id)
* ``delete_multiple`` (for DELETE requests without an id or multiple ids)

You can link to your existing views using the ``call_view`` method. Consider you 
have the following view::

    # myapp/views.py
    def mymodel_detail(request, id):
        m = get_object_or_404(MyModel, pk=id)
        return render_to_response('detail.html', {'mymodel': m})


Your wrapper class should look like this::

    # myapp/wrappers.py
    from riv.wrappers import BaseWrapper
    from riv.helpers import call_view
    from myapp import views

    class MyModelWrapper(BaseWrapper):
        read = call_view(views.mymodel_detail)

Now you need adjust your view to handle calls through the API properly::

    # myapp/views.py
    ...
    from riv.shortcuts import render_to_rest

    def mymodel_detail(request, id):
        m = get_object_or_404(MyModel, pk=id)
        if request.is_rest():
            return render_to_rest(m)
        return render_to_response('detail.html', {'mymodel': m})


Using the StandaloneWrapper
===========================

If you don't any special data preparation in your views or if you simply
don't have views for your model you can use the :ref:`ref-standalonewrapper` to make
your model accessible directly::

    # myapp/resources.py
    from riv.resources import Resource
    from riv.wrappers import StandaloneWrapper
    from myapp.models import MyModel, MyOtherModel

    class MyModelResource(Resource):
      _wrapper = StandaloneWrapper()
      class Meta:
        name = 'mymodel'
        model = MyModel

Setting up the API
===================

The API class is used to bundle several resources together and form a logical unit.
Adding the API to your URLconf makes the resources available::

    # myapp/urls.py
    from riv.api import Api
    from myapp.resources import MyModelResource, MyOtherModelResource

    # The api name is only used internally. It does not become part
    # of your URL
    myapi = Api(name='myapi')
    myapi.register(MyModelResource())
    myapi.register(MyOtherModelResource())

    urlpatterns += patterns('',
      (r'api/', include(myapi.urls)),
    )

Try it
======

You can now access the registered resources at::

    http://<yourhost>/myapp/api/<resource_name>

In this case::

    http://<yourhost>/myapp/api/mymodel
    http://<yourhost>/myapp/api/myothermodel
