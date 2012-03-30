class RestfulAPIError(Exception):
    pass

class UnsupportedFormat(RestfulAPIError):
    pass