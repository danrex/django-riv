from django.conf.urls.defaults import patterns, include, url
import views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('polls.views',
    (r'^$', 'poll_index'),
    (r'^(?P<id>\d+)/$', 'poll_detail'),
    (r'^(?P<id>\d+)/update/$', 'poll_update'),
    (r'^(?P<id>\d+)/delete/$', 'poll_delete'),
    (r'^(?P<id>\d+)/results/$', 'results'),
    (r'^(?P<id>\d+)/vote/$', 'vote'),
    (r'^add/$', 'add'),
    # Examples:
    # url(r'^$', 'riv_tests.views.home', name='home'),
    # url(r'^riv_tests/', include('riv_tests.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
