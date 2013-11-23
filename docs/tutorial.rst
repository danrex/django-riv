.. _ref-tutorial:

========
Tutorial
========

In this tutorial we will build a full featured REST API for the poll application
built in the `Django tutorial`_.

.. _Django tutorial: https://docs.djangoproject.com/en/1.4/intro/tutorial01/

Starting point
==============

Models
------

We will add a ManyToMany relation to the Poll model to add one or more tags
to a poll object. Our models.py file will look like this::

    # poll/models.py
    import datetime
    from django.contrib.auth.models import User
    from django.db import models

    class Tag(models.Model):
        name = models.CharField(max_length=100)

    class Poll(models.Model):
        question = models.CharField(max_length=200)
        pub_date = models.DateTimeField('date published')
        tags = models.ManyToManyField(Tag)

        def was_published_today(self):
            return self.pub_date.date() == datetime.date.today()

        def __unicode__(self):
            return self.question

    class Choice(models.Model):
        poll = models.ForeignKey(Poll)
        choice = models.CharField(max_length=200)
        votes = models.IntegerField()

        def __unicode__(self):
            return self.choice

Views
-----

We will use the following basic views to read, create/update and
delete polls::

    # polls/views.py

    # ...

    def poll_index(request):
        poll_list = Poll.objects.all().order_by('-pub_date')
        return render_to_response('index.html',  {
            'poll_list': poll_list,
        })

    def poll_detail(request, id):
        p = get_object_or_404(Poll, pk=id)
        return render_to_response('detail.html', {'poll': p})

    def poll_create_or_update(request, id=None):
        if id:
            p = get_object_or_404(Poll, pk=id)
        if request.method == 'POST':
            if id:
                form = PollForm(request.POST, instance=p)
            else:
                form = PollForm(request.POST)
            if form.is_valid():
                obj = form.save()
        else:
            if id:
                form = PollForm(instance=p)
            else:
                form = PollForm()

        return render_to_response('update.html', {
            'form': form,
        }, context_instance=RequestContext(request))

    def poll_delete(request, id):
        p = get_object_or_404(Poll, pk=id)
        p.delete()
        return render_to_response('deleted.html')

Additionally we have one view to cast votes which differs from
the corresponding view you can find in the Django tutorial. The
reason is that we want to use a form as we will explain later::

    def vote(request):
        if request.method == 'POST':
            form = VoteForm(request.POST)
            if form.is_valid():
                choice = form.cleaned_data.get('choice')
                choice.votes += 1
                choice.save()
                return HttpResponse("ok")
        return render_to_response('results.html', {
            'form': form
        }, context_instance=RequestContext(request))

Finally we will make the view to see the results of a poll only
available to logged in users to demonstrate how authentication works
with RiV (in fact this single line of code is all you have to do)::

    @login_required
    def results(request, id):
        poll = get_object_or_404(Poll, pk=id)
        return render_to_response('results.html', {
            'poll': poll,
        }, context_instance=RequestContext(request))

You can also allow the creation of multiple objects at once by
setting the :ref:`ref-allow-batch-creation` option in your resource. In that case 
you have to work with formsets::

    def poll_create_multiple(request):
        PollFormSet = modelformset_factory(Poll)
        if request.method == 'POST':
            formset = PollFormSet(request.POST)
            if formset.is_valid():
                objects = formset.save()
        else:
            formset = PollFormSet()

        return render_to_response('create.html', {
            'formset': formset,
        }, context_instance=RequestContext(request))

Forms
-----

We use a simple ModelForm for editing the polls and we use a form
to allow the user to vote. It let's the user choose a poll and
a choice and adds a little check if the chosen choice belongs to the
chosen poll. This form is usually not what one would use to create
a browser-based UI, but it becomes useful for our API as we will see 
later::

    # polls/forms.py

    # ...

    class PollForm(forms.ModelForm):
        class Meta:
            model = Poll

    class VoteForm(forms.Form):
        poll = forms.ModelChoiceField(queryset=Poll.objects.all())
        choice = forms.ModelChoiceField(queryset=Choice.objects.all())

        def clean(self):
            cd = super(VoteForm, self).clean()
            poll = cd.get('poll')
            choice = cd.get('choice')

            if poll and choice:
                try:
                    Choice.objects.get(id=choice.id, poll=poll.id)
                except Choice.DoesNotExist:
                    msg = u"Invalid choice for the given poll."
                    self._errors['choice'] = self.error_class([msg])
                    del cd['choice']

            return cd

Create the model-based resources
================================

As a first step we will create resources for our models Poll, Choice and 
Tag. We will write our own wrapper to link the views defined above to the
PollResource. For the Choice and Tag models we don't have any views so 
will we use the :ref:`ref-standalonewrapper` class to make these models available as 
resources without having to write views.

We will allow the user to view, create, and update tags
but we will not allow to delete tags by removing the "DELETE" HTTP method
from the :ref:`ref-allowed-methods` option. We will make the Choice resource
entirely read-only by only specifying the "GET" method.

As basic set of resources will look like this::

    # polls/resources.py
    from riv.resources import Resource
    from riv.wrappers import StandaloneWrapper
    from polls.wrappers import PollWrapper
    from polls.models import Poll, Choice, Tag

    class PollResource(Resource):
        _wrapper = PollWrapper()
        class Meta:
            name = 'poll'
            model = Poll
            allow_batch_creation = True

    class TagResource(Resource):
        _wrapper = StandaloneWrapper()
        class Meta:
            name = 'tag'
            model = Tag
            allowed_methods = ['GET', 'POST', 'PUT']

    class ChoiceResource(Resource):
        _wrapper = StandaloneWrapper()
        class Meta:
            name = 'choice'
            model = Choice
            allowed_methods = ['GET']


Implement the PollWrapper
=========================

As the Choice and Tag models use the :ref:`ref-standaloneWrapper` we only need to write
a wrapper class for the Poll model. We use the ``call_view`` helper method
to link our existing views to the corresponding HTTP methods::

    # polls/wrappers.py
    from riv.wrappers import BaseWrapper
    from riv.helpers import call_view
    from polls import views

    class PollWrapper(BaseWrapper):
        read = call_view(views.poll_detail)
        read_multiple = call_view(views.poll_index)
        delete = call_view(views.poll_delete)
        update = call_view(views.poll_create_or_update)
        create = call_view(views.poll_create_or_update)
        create_multiple = call_view(views.poll_create_multiple)

Adjusting the Views
===================

Now we need to adjust the views to return data in a way RiV can understand. For
this purpose the ``RivMiddleware`` adds a ``HttpRequest.is_rest()`` method to the 
HttpRequest object in analogy to the django built-in ``HttpRequest.is_ajax()`` method.

GET methods
-----------

In anology to the ``render_to_response`` shortcut RiV provides the ``render_to_rest`` 
shortcut to return a ``QuerySet``, a list of objects or a simple object::

    # polls/views.py

    # ...

    def poll_index(request):
        poll_list = Poll.objects.all().order_by('-pub_date')
        if request.is_rest():
            # Return a QuerySet
            return render_to_rest(poll_list)
        return render_to_response('index.html',  {
            'poll_list': poll_list,
        })

    def poll_detail(request, id):
        p = get_object_or_404(Poll, pk=id)
        if request.is_rest():
            # Return a single object
            return render_to_rest(p)
        return render_to_response('detail.html', {'poll': p})

POST and PUT methods
--------------------

RiV encourages you to re-use your Django forms to modify objects
through the REST API. Hence, incoming data sent via POST or PUT (formatted 
in JSON, XML other other supported serialization formats) will be rearranged
in order to be parseable using Django forms. In case of
a failure you can return the error messages to the user simply by passing the
form instance to the ``render_form_error_to_rest`` shortcut::

    def poll_create_or_update(request, id=None):
        if id:
            p = get_object_or_404(Poll, pk=id)
        if request.method == 'POST':
            if id:
                form = PollForm(request.POST, instance=p)
            else:
                form = PollForm(request.POST)
            if form.is_valid():
                obj = form.save()
                if request.is_rest():
                    return render_to_rest(obj)
            else:
                if request.is_rest():
                 return render_form_error_to_rest(form)
        else:
            if id:
                form = PollForm(instance=p)
            else:
                form = PollForm()

        return render_to_response('update.html', {
            'form': form,
            }, context_instance=RequestContext(request)
        )

    def poll_create_multiple(request):
        PollFormSet = modelformset_factory(Poll)
        if request.method == 'POST':
            formset = PollFormSet(request.POST)
            if formset.is_valid():
                objects = formset.save()
                if request.is_rest():
                    return render_to_rest(objects)
                else:
                    return HttpResponse("ok")
            else:
                if request.is_rest():
                    return render_form_error_to_rest(formset)
        else:
            formset = PollFormSet()

        return render_to_response('create.html', {
            'formset': formset,
            }, context_instance=RequestContext(request)
        )

DELETE methods
--------------

No adjustments are required to handle DELETE requests.
However, if you want to return the entities that have been deleted 
back to the user you can use the ``render_to_rest`` shortcut to return
the objects in question.


Join your resources to build an API
===================================

Now we have to register all resources to an instance of the API class and 
add it to our URLconf to make the API public::

    # polls/urls.py
    from riv.api import Api
    from polls.resources import PollResource, ChoiceResource, TagResource

    # The name is only used internally and will not be part of your URL
    api = Api(name='rest1')

    api.register(PollResource())
    api.register(ChoiceResource())
    api.register(TagResource())

    urlpatterns = patterns('polls.views',
        url(r'^$', 'poll_index'),
        url(r'^vote/$', 'vote'),
        url(r'^(?P<id>\d+)/$', 'poll_detail'),
        url(r'^create/$', 'poll_create_or_update', name='poll_create'),
        url(r'^(?P<id>\d+)/update/$', 'poll_create_or_update', name='poll_update'),
        url(r'^(?P<id>\d+)/delete/$', 'poll_delete'),
        url(r'^(?P<id>\d+)/results/$', 'results'),
        url(r'^(?P<id>\d+)/vote/$', 'vote'),
        url(r'^rest/', include(api.urls)),
    )

Testing the API
================

The API is now up and running. Fill your database with some data you should get 
something like this::

    # http://localhost:8000/polls/rest/poll?format=json
    [
      {
        "pub_date": "2011-10-20T19:30:00", 
        "question": "How is the weather?", 
        "id": 1, 
        "tags": ["/polls/rest/tag/1"]
      },
      {
        "pub_date": "2011-10-20T19:30:00", 
        "question": "How are you?", 
        "id": 2, 
        "tags": ["/polls/rest/tag/1"]
      }
    ]

    # http://localhost:8000/polls/rest/tag?format=json
    [
      {
        "name": "Fun", 
        "id": 1
      }, 
      {
        "name": "Serious", 
        "id": 2
      }
    ]

    # http://localhost:8000/polls/rest/choice?format=json
    [
      {
        "votes": 3, 
        "poll": "/polls/rest/poll/1", 
        "id": 1, 
        "choice": "Rainy"
      }
    ]


Adjusting the data representation
=================================

The design concept of RiV aims to maintain Django's MVC structure while building
a RESTful API. 

In Django the views describe *which data you see* while the templates
are responsible for *how you see it*. An API built with RiV keeps that structure by
replacing the role of templates with resources. Thus, RiV provides a large set of methods
like :ref:`ref-exclude`, :ref:`ref-map-fields`, :ref:`ref-inline`, :ref:`ref-extra-fields` 
and more which allow you to adjust the way you want to represent your data to the user. We will 
demonstrate some of them in this section.

Renaming fields
---------------

To rename fields in our data representation we can use the :ref:`ref-map-fields` option in the
resource definition. Let's say we want to rename ``pub_date`` to the more speaking name
``publication_date``. Thus, we tell the resource to map the field ``pub_date`` to 
``publication_date``::

    # polls/resources.py

    # ...

    class PollResource(Resource):
        _wrapper = PollWrapper()
        class Meta:
            name = 'poll'
            model = Poll
            allow_batch_creation = True
            map_fields = {'pub_date': 'publication_date'}

Accessing the API will now show the following result::

    # http://localhost:8000/polls/rest/poll/1?format=json
    {
      "publication_date": "2011-10-20T19:30:00", 
      "question": "How is the weather?", 
      "id": 1, 
      "tags": ["/polls/rest/tag/1"]
    }

Adding extra information
------------------------

We can augment the output of our objects by adding additional fields that are not part
of the model's field definition. RiV will simply add the string representation of the fields specified
using :ref:`ref-extra-fields` or if the field is a callable it will call the method and include the return value
into the result. We added a method ``was_published_today`` to the Poll model class. Let's add this
method to our API::

    # polls/resources.py

    # ...

    class PollResource(Resource):
        _wrapper = PollWrapper()
        class Meta:
            name = 'poll'
            model = Poll
            allow_batch_creation = True
            map_fields = {'pub_date': 'publication_date'}
            extra_fields = ['was_published_today']

Accessing the API will now show the following result::

    # http://localhost:8000/polls/rest/poll?format=json
    [
      {
        "publication_date": "2011-10-20T19:30:00", 
        "question": "How is the weather?", 
        "id": 1, 
        "tags": ["/polls/rest/tag/1"], 
        "was_published_today": false
      }, 
      {
        "publication_date": "2011-10-20T19:30:00", 
        "question": "How are you?", 
        "id": 2, 
        "tags": ["/polls/rest/tag/1"], 
        "was_published_today": false
      }
    ]

Include foreign key or m2m objects
----------------------------------

Foreign keys and m2m relations are shown as resource URIs in your data representation if your
API contains a resource for the foreign key model. However, you can also include the object
directly into the result by using the :ref:`ref-inline` option. Let's consider we want to
include the tags into our data display::

    # polls/resources.py

    # ...

    class PollResource(Resource):
        _wrapper = PollWrapper()
        class Meta:
            name = 'poll'
            model = Poll
            allow_batch_creation = True
            map_fields = {'pub_date': 'publication_date'}
            extra_fields = ['was_published_today']
            inline = ['tags']

Accessing the API will now show the following result::

    # http://localhost:8000/polls/rest/poll?format=json
    [
      {
        "publication_date": "2011-10-20T19:30:00", 
        "question": "How is the weather?", 
        "id": 1, 
        "tags": [
          {
            "name": "Fun",
            "id": 1
          }
        ],
        "was_published_today": false
      }, 
      {
        "publication_date": "2011-10-20T19:30:00", 
        "question": "How are you?", 
        "id": 2, 
        "tags": [
          {
            "name": "Fun",
            "id": 1
          }
        ],
        "was_published_today": false
      }
    ]

map_fields again
----------------

In the preceding section we used :ref:`ref-map-fields` to rename fields. But :ref:`ref-map-fields`
is more powerful. We can also rename fields in any m2m and foreign key object and we can 
even move fields around freely between the main model and the related objects. 

To access attributes of related objects use the "__" syntax just as you do querying objects.
To demonstrate this let's say we want to add the ``name`` field of the tag object as an attribute 
``tagname`` to our model::

    # polls/resources.py

    # ...

    class PollResource(Resource):
        _wrapper = PollWrapper()
        class Meta:
            name = 'poll'
            model = Poll
            allow_batch_creation = True
            map_fields = {
                'pub_date': 'publication_date',
                'tags__name': 'tagname'
            }
            extra_fields = ['was_published_today']
            inline = ['tags']

Accessing the API will now show the following result::

    # http://localhost:8000/polls/rest/poll?format=json
    [
      {
        "publication_date": "2011-10-20T19:30:00", 
        "question": "How is the weather?", 
        "id": 1, 
        "tagname": [
          "Fun"
        ],
        "tags": [
          {
            "id": 1
          }
        ],
        "was_published_today": false
      }, 
      {
        "publication_date": "2011-10-20T19:30:00", 
        "question": "How are you?", 
        "id": 2, 
        "tagname": [
          "Fun"
        ],
        "tags": [
          {
            "id": 1
          }
        ],
        "was_published_today": false
      }
    ]

Now the remanins of the ``tags`` objects seems pretty useless. We can remove the
remaining parts using the :ref:`ref-exclude` option::

    # polls/resources.py

    # ...

    class PollResource(Resource):
        _wrapper = PollWrapper()
        class Meta:
            name = 'poll'
            model = Poll
            allow_batch_creation = True
            map_fields = {
                'pub_date': 'publication_date',
                'tags__name': 'tagname'
            }
            extra_fields = ['was_published_today']
            inline = ['tags']
            exclude = ['tags']

Accessing the API will now show the following result::

    # http://localhost:8000/polls/rest/poll?format=json
    [
      {
        "publication_date": "2011-10-20T19:30:00", 
        "question": "How is the weather?", 
        "id": 1, 
        "tagname": [
          "Fun"
        ],
        "was_published_today": false
      }, 
      {
        "publication_date": "2011-10-20T19:30:00", 
        "question": "How are you?", 
        "id": 2, 
        "tagname": [
          "Fun"
        ],
        "was_published_today": false
      }
    ]

For a full list of all supported options have a look at the documentation
of the :ref:`ref-resources` class.

Non-model-based resources
=========================

You can also create resources that are not backed by a real model. Let's say 
we want to extend the API to support casting votes. We don't have a
``Vote`` model class, however, as a RESTful API is always resource based
we want to mimic the behaviour of a Vote resource.

To the user the API will feel like there is a ``Vote`` object and casting votes
means to create a new ``Vote`` object including a reference to a ``Poll`` and 
a ``Choice`` object.

Resource
--------

First we create a resource for our "virtual" Vote model. We don't link it to any model
and instead define all attributes we want to include in using the :ref:`ref-extra-fields` 
option::

    # polls/resources.py

    # ...

    class VoteResource(Resource):
        _wrapper = VoteWrapper()
        class Meta:
            name = 'vote'
            allowed_methods = ['POST',]
            extra_fields = ['poll', 'choice']

We restricted the set of :ref:`ref-allowed-methods` to "POST" as we only want to use the
resource to cast votes (i.e. create ``Vote`` objects).

Wrapper
-------

Next we have to add a wrapper class. We only need to define the ``create`` 
method as we restricted the set of :ref:`ref-allowed-methods` to "POST" (and 
we did not specify :ref:`ref-allow-batch-creation`)::

    # polls/wrappers.py

    # ...

    class VoteWrapper(BaseWrapper):
        create = call_view(views.vote)

View
----

As for the model-based resources we have to adjust the view to return data RiV
can handle properly. Instead of returning an object or a ``QuerySet`` we simple 
return a dictionary which contains the keys we defined in the :ref:`ref-extra-fields` 
option in the resource definition::

    # polls/views.py

    # ...

    def vote(request):
        if request.method == 'POST':
            form = VoteForm(request.POST)
            if form.is_valid():
                choice = form.cleaned_data.get('choice')
                choice.votes += 1
                choice.save()
                if request.is_rest():
                    return render_to_rest({'poll': choice.poll.id, 'choice': choice.id})
                else:
                    return HttpResponse("ok")
            else:
                if request.is_rest():
                    return render_form_error_to_rest(form)

        return render_to_response('results.html', {
            'form': form
        }, context_instance=RequestContext(request))

API
---

Finally we have to register the ``VoteResource`` at the API as shown above for the
model-based resources.


Try it
------

You can now send a POST request to your VoteResource specifying the id of a Poll and
a Choice object. If the Choice object belongs to the given Poll a vote will be cast.


