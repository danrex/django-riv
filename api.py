from django.conf.urls import patterns
from riv.exceptions import ConfigurationError

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
        name = getattr(resource._meta, 'name')
        if not name:
            raise ConfigurationError("Resource %s does not have a name assigned." % (resource,))
        if resource._meta.model:
            if self._resource_list.has_key(resource._meta.model):
                self._resource_list[resource._meta.model][name] = resource
            else:
                self._resource_list[resource._meta.model] = {name: resource}
        else:
            self._resource_list[name] = {name: resource}
        resource._meta.api_name = self.name

    def unregister(self, resource):
        name = getattr(resource._meta, 'name')
        if not name:
            raise ConfigurationError("Resource %s does not have a name assigned." % (resource,))
        if name in self._resource_list:
            del self._resource_list[name]

    def _get_urls(self):
        urlpatterns = patterns('')
        for model_or_name,resources in self._resource_list.items():
            multiple_reverse_counter = 0
            if len(resources) > 1:
                for name,resource in resources.items():
                    if resource._meta.reverse:
                        if multiple_reverse_counter > 0:
                            raise ConfigurationError("Multiple resources in api '%s' with 'reverse=True' for model %s found" % (self.name, resource._meta.model))
                        else:
                            multiple_reverse_counter += 1
                    # TODO add a counter here and throw an error if two resources have reverse set to True.
                    urlpatterns += resource.urls
            else:
                # TODO should not use the internal method "_get_urls" but rather a property
                urlpatterns += resources.values()[0]._get_urls(reverse=True)
        return urlpatterns

    urls = property(_get_urls)
