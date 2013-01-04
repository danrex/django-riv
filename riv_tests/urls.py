from django.conf.urls.defaults import patterns, include, url
from polls.resources import StandaloneReadOnlyChoiceResource, ReadOnlyPollResource, ReadWritePollResource, \
        StandaloneReadOnlyPollResource, StandaloneReadWritePollResource, StandaloneReadWritePollResource2, \
        StandaloneExcludeGetOnly, StandaloneExcludePostOnly, StandaloneExcludePutOnly, StandaloneTagResource, \
        VoteResource, PutOnlyPollResource, PostOnlyPollResource, DeleteOnlyPollResource, \
        StandalonePutOnlyPollResource, StandalonePostOnlyPollResource, StandaloneDeleteOnlyPollResource, \
        BatchPostPollResource, BatchDeletePollResource, ReadWriteRenderPollResource, ResultResource, \
		NoFallbackPollResource, RelatedAsIdsPollResource, FieldsPollResource, ExcludePollResource, \
		InlinePollResource, ExtraPollResource, MapPollResource

from riv.api import Api

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

api = Api(name='rest1')

api.register(RelatedAsIdsPollResource(name='raipr'))
api.register(NoFallbackPollResource(name='nfpr'))
api.register(ReadOnlyPollResource(name='ropr'))
api.register(PutOnlyPollResource(name='puopr'))
api.register(PostOnlyPollResource(name='poopr'))
api.register(DeleteOnlyPollResource(name='dopr'))
api.register(ReadWritePollResource(name='rwpr'))
api.register(ReadWriteRenderPollResource(name='rwrpr'))
api.register(BatchDeletePollResource(name='bdpr'))
api.register(BatchPostPollResource(name='bppr'))
api.register(FieldsPollResource(name='fpr'))
api.register(ExcludePollResource(name='excpr'))
api.register(InlinePollResource(name='ipr'))
api.register(ExtraPollResource(name='extpr'))
api.register(MapPollResource(name='mpr'))
api.register(StandaloneReadOnlyPollResource(name='srpr'))
api.register(StandalonePutOnlyPollResource(name='spuopr'))
api.register(StandalonePostOnlyPollResource(name='spoopr'))
api.register(StandaloneDeleteOnlyPollResource(name='sdopr'))
api.register(StandaloneReadWritePollResource(name='srwpr'))
api.register(StandaloneReadWritePollResource2(name='srwpr2'))
api.register(StandaloneReadOnlyChoiceResource(name='scr'))
api.register(StandaloneExcludeGetOnly(name='sego'))
api.register(StandaloneExcludePostOnly(name='sepo'))
api.register(StandaloneExcludePutOnly(name='sepuo'))
api.register(StandaloneTagResource(name='str'))
api.register(VoteResource(name='vote'))
api.register(ResultResource(name='result'))

urlpatterns = patterns('',
	(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    (r'^polls/', include('polls.urls')),
    (r'^rest/', include(api.urls)),
)
