class RestfulAPIError(Exception):
    pass

class ConfigurationError(RestfulAPIError):
    pass

class UnsupportedFormat(RestfulAPIError):
    pass
