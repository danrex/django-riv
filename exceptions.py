class RestfulAPIError(Exception):
    pass

class ConfigurationError(Exception):
    pass

class UnsupportedFormat(RestfulAPIError):
    pass
