from django.conf.urls import patterns

class Api(object):
    """
    The Api class is used to bind together different resources
    that form a full API. This is necessary to perform url
    resolution for related objects.
    It also allows to register the same resource with multiple
    different apis.
    """
    def __init__(self, name):
        self.name = name
        self._resource_list = {}

    def register(self, resource):
        name = getattr(resource, 'name')
        if not name:
            # TODO Add an error for configuration mistakes
            raise
        self._resource_list[name] = resource
        resource._meta.api_name = self.name

    def unregister(self, resource):
        name = getattr(resource, 'name')
        if not name:
            # TODO Add an error for configuration mistakes
            raise
        if name in self._resource_list:
            del self._resource_list[name]

    def _get_urls(self):
        urlpatterns = patterns('')
        for name,resource in self._resource_list.items():
            urlpatterns += resource.urls
        return urlpatterns

    urls = property(_get_urls)
