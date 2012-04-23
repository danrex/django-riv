from django.conf.urls.defaults import patterns, include, url
from polls.resources import ReadOnlyPollResource, ReadWritePollResource, StandaloneReadOnlyPollResource, StandaloneReadWritePollResource, StandaloneReadWritePollResource2

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

ropr = ReadOnlyPollResource(name='ropr')
rwpr = ReadWritePollResource(name='rwpr')
srpr = StandaloneReadOnlyPollResource(name='srpr')
srwpr = StandaloneReadWritePollResource(name='srwpr')
srwpr2 = StandaloneReadWritePollResource2(name='srwpr2')

urlpatterns = patterns('',
    (r'^polls/', include('polls.urls')),
	(r'^rest/', include(ropr.urls)),
	(r'^rest/', include(rwpr.urls)),
	(r'^rest/', include(srpr.urls)),
	(r'^rest/', include(srwpr.urls)),
	(r'^rest/', include(srwpr2.urls)),
)
