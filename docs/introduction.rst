.. _ref-introduction:

============
Introduction
============

Idea
====

The design concept of RiV aims to maintain Django's MVC structure while extending your
existing application with a RESTful API.

In Django the views describe *which data you see* while the templates
are responsible for *how you see it*. An API built with RiV keeps that structure by
replacing the role of templates with resources. Thus, RiV provides a large set of methods
like :ref:`ref-exclude`, :ref:`ref-map-fields`, :ref:`ref-inline`, :ref:`ref-extra-fields` 
and more which allow you to adjust the way you want to represent your data to the user.

The key concepts are:

* Data preparation and access control happens in your views
* RIV ensures your response is conform to the HTTP protocol definitions
* RIV uses resource options you to change the representation of your data

However, if you don't have any views to manipulate model you can also run a RiV API
in standalone mode.

Comparison to existing solutions
================================

There are a couple of different REST frameworks for Django. The most
well-known are Piston and Tastypie. Both of them are well-written and
used in various web applications.

Both frameworks work really well if you want to build an API that is
completely separated from your web application and if your data
representation is not too different from the structure of your models.
If this is your use case you might probably want to have a look at 
Tastypie. 

However, if you already have an existing Django web application and you
want to enrich it with an API, because for example you want to write a
native mobile app, you will probably see the advantages of RIV quickly.


