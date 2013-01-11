# RIV #

RIV (Rest-In-Views) is a REST framework for 
[Django](http://www.djangoproject.com). The aim of RIV is to integrate
smoothly into the Django concepts and make as much of your existing
code reusable as possible.

## Requirements ##

RIV does not require any additional third party modules. The serializers
are built on top of the built-in Django serializers and therefore 
share the same requirements.

## Getting started ##

### Setup ###

Add RIV to the list of your installed apps:

 # settings.py
 INSTALLED_APPS = (
   ...
   'riv',
 )

Add the RivMiddleware to the end of your middleware classes 

 # settings.py
 MIDDLEWARE_CLASSES = (
   'django.middleware.common.CommonMiddleware',
   ...
   'riv.middleware.RivMiddleware',
 )

The RIV serializers extend the builtin Django serializers. So you have
to add the serializers you want to use to the settings.

 # settings.py
 SERIALIZATION_MODULES = {
   'restjson': 'riv.serializers.json',
   'restxml':  'riv.serializers.xml',
 }

For debugging purposes you can tell RIV to display errors. However, 
for security reasons this setting only has an effect if Django is 
running in debug mode.

 # settings.py
 RIV_DISPLAY_ERRORS = True

### Add Resources ###

Add a resources.py file to your application and add a resource for your
model. Each resource needs to define a wrapper to wrap view functions
into your resource. Using the StandaloneWrapper class you don't need to
have any views set up.

 # myapp/resources.py
 from riv.resources import Resource
 from riv.wrappers import StandaloneWrapper
 from myapp.models import MyModel

 class MyModelResource(Resource):
   _wrapper = StandaloneWrapper()
   class Meta:
     name = 'mymodel'
     model = MyModel

Create an API, add the resource and make the URLs public. Add the
following lines to your URLconf

### Create an API for your resources ###

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

### Try it ###

You can now access the resource at http://<yourhost>/myapp/api/mymodel/.

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
native mobile app you will probably see the advantages of RIV quickly.

# Design concept #

The focus of RIV is to make your views completely resusable. Therefore:

* Data preparation and access control happens in your views
* RIV ensures your response is conform to the HTTP protocol definitions
* RIV helps you to change the representation of your data
* If you don't have views RIV can run in a standalone mode

# Known Issues #

* The HTTP methods OPTIONS, HEAD, TRACE and PATCH are not implemented
* RIV currently supports only integers as primary keys
* Foreign keys have to be supplied as ids and not as URIs
* Changing foreign key (or m2m) fields inline is not supported

# Bugs #

Please report bugs as you find them and I will add them here until they
have been fixed.

# License # 

See the LICENSE file in the repository.

