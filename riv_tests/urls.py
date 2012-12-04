from django.conf.urls.defaults import patterns, include, url
from polls.resources import StandaloneReadOnlyChoiceResource, ReadOnlyPollResource, ReadWritePollResource, StandaloneReadOnlyPollResource, StandaloneReadWritePollResource, StandaloneReadWritePollResource2

from riv.api import Api

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

ropr = ReadOnlyPollResource(name='ropr')
rwpr = ReadWritePollResource(name='rwpr')
srpr = StandaloneReadOnlyPollResource(name='srpr')
srwpr = StandaloneReadWritePollResource(name='srwpr')
srwpr2 = StandaloneReadWritePollResource2(name='srwpr2')
scr = StandaloneReadOnlyChoiceResource(name='scr')

api = Api(name='rest1')
api.register(ropr)
api.register(rwpr)
api.register(scr)

urlpatterns = patterns('',
    (r'^polls/', include('polls.urls')),
	(r'^rest/', include(ropr.urls)),
	(r'^rest/', include(rwpr.urls)),
	(r'^rest/', include(srpr.urls)),
	(r'^rest/', include(srwpr.urls)),
	(r'^rest/', include(srwpr2.urls)),
    (r'^api/', include(api.urls)),
)
