# RiV #

RiV (Rest-In-Views) is a REST framework for 
[Django](http://www.djangoproject.com). The aim of RiV is to integrate
smoothly into the Django concepts and make as much of your existing
code reusable as possible.

RiV aims to maintain Django's MVC structure while extending your
existing application with a RESTful API.

In Django the views describe *which data you see* while the templates
are responsible for *how you see it*. An API built with RiV keeps that structure by
replacing the role of templates with resources. Thus, RiV provides a large set of methods
to exclude fields, rename fields, include a full representation of 
foreign keys and m2m fields, move fields between foreign keys and
your main object and many more.

Documentation on Read the Docs: [RiV](https://riv.readthedocs.org/en/latest/)

## Requirements ##

RiV does not require any additional third party modules. The serializers
are built on top of the built-in Django serializers and therefore 
share the same requirements.

## Getting started ##

### Setup ###

Add RiV to the list of your installed apps:

```python
# settings.py
INSTALLED_APPS = (
  ...
  'riv',
)
```

Add the RivMiddleware to the end of your middleware classes 

```python
# settings.py
MIDDLEWARE_CLASSES = (
  'django.middleware.common.CommonMiddleware',
  ...
  'riv.middleware.RivMiddleware',
)
```

The RiV serializers extend the builtin Django serializers. So you have
to add the serializers you want to use to the settings.

```python
# settings.py
SERIALIZATION_MODULES = {
  'restjson': 'riv.serializers.json_serializer',
  'restxml':  'riv.serializers.xml_serializer',
}
```

For debugging purposes you can tell RiV to display errors. However, 
for security reasons this setting only has an effect if Django is 
running in debug mode.

```python
# settings.py
RiV_DISPLAY_ERRORS = True
```

### Add Resources ###

Add a resources.py file to your application and add a resource for your
model. Each resource needs to define a wrapper to wrap view functions
into your resource (If you don't have any views you can simply use the 
StandaloneWrapper class).

```python
# myapp/resources.py
from riv.resources import Resource
from myapp.models import MyModel

class MyModelResource(Resource):
  _wrapper = MyModelWrapper()
  class Meta:
    name = 'mymodel'
    model = MyModel
```

The wrapper class tells RiV where to find the views to handle the
different HTTP methods.

```python
# myapp/wrappers.py
from riv.wrappers import BaseWrapper
from riv.helpers import call_view
from myapp import views

class MyModelWrapper(BaseWrapper):
    read_multiple = call_view(views.index)    # GET
    read          = call_view(views.detail)   # GET with id
    create        = call_view(views.create)   # POST
    update        = call_view(views.update)   # PUT
    delete        = call_view(views.delete)   # DELETE
```

Create an API, add the resource, and make the URLs public. Add the
following lines to your URLconf

### Create an API for your resources ###

```python
# myapp/urls.py
from riv.api import Api
from myapp.resources import MyModelResource

# The api name is only used internally. It does not become part
# of your URL
myapi = Api(name='myapi')
myapi.register(MyModelResource())

urlpatterns += patterns('',
  (r'api/', include(myapi.urls)),
)
```

### Try it ###

You can now access the resource at http://<yourhost>/myapp/api/mymodel/.

# Documentation #

You can find the documentation [here](https://riv.readthedocs.org/en/latest/).

Have a look at the [tutorial](https://riv.readthedocs.org/en/latest/tutorial.html).

# Comparision to existing solutions #

There are a couple of different REST frameworks for Django. The most
well-known are Piston and Tastypie. Both of them are well-written and
used in various web applications.

Both frameworks work really well if you want to build an API that is
completely separated from your web application and if your data
representation is not too different from the structure of your models.
If this is your use case you might probably want to have a look at 
Tastypie. 

However, if you already have an existing Django web application and you
want to enrich it with an API because for example you want to write a
native mobile app you will probably see the advantages of RiV quickly.

# Design concept #

The focus of RiV is to make your views completely resusable. Therefore:

* Data preparation and access control happens in your views
* RiV ensures your response is conform to the HTTP protocol definitions
* RiV helps you to change the representation of your data
* If you don't have views RiV can run in a standalone mode

# Known Issues #

* The HTTP methods OPTIONS, HEAD, TRACE and PATCH are not implemented
* RiV currently supports only integers as primary keys
* Foreign keys have to be supplied as ids and not as URIs
* Changing foreign key (or m2m) fields inline is not supported

# Bugs #

Please report bugs as you find them and I will add them here until they
have been fixed.

# License #

See the LICENSE file in the repository.

