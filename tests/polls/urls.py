from django.conf.urls.defaults import patterns, include, url
import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('polls.views',
    url(r'^$', 'poll_index'),
    url(r'^vote/$', 'vote'),
    url(r'^(?P<id>\d+)/$', 'poll_detail'),
    url(r'^create/$', 'poll_create_or_update', name='poll_create'),
    url(r'^(?P<id>\d+)/update/$', 'poll_create_or_update', name='poll_update'),
    url(r'^(?P<id>\d+)/delete/$', 'poll_delete'),
    url(r'^(?P<id>\d+)/results/$', 'results'),
    url(r'^(?P<id>\d+)/vote/$', 'vote'),
    # Examples:
    # url(r'^$', 'riv_tests.views.home', name='home'),
    # url(r'^riv_tests/', include('riv_tests.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
