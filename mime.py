from django.core import serializers

formats = {
    'application/json'  : 'json',
    'application/xml'   : 'xml',
    'text/xml'          : 'xml',
    'text/yaml'         : 'yaml',
    'text/x-yaml'       : 'yaml',
    'application/x-yaml': 'yaml',
}

def get_mime_for_format(format):
    for k,v in formats.items():
        if v == format:
            return k

def get_available_format(request):
    """
    Trys to determine the requestes format from the current request and returns it
    if a suitable serializer for the found format is available.
    """
    # Get a list of registered REST serializers
    serializers = get_serializers()

    # Helper method to make the code more readable.
    has_serializer_for = lambda f: 'rest%s'  % (f,) in serializers

    # Try to detect the requested format
    requestformats = detect_format(request)

    if not requestformats:
        return None

    # If the format has been specified using the "format" query variable 
    # return it directly.
    if has_serializer_for(requestformats[0]):
        return requestformats[0]

    for f in requestformats:
        if '*' in f:
            # If the format is a wildcard format, we try to match it against the content_type
            # used to establish the request. If that fails we
            # try to find a suitable format in the list of formats.
            major, minor = f.split('/')
            content_type = request.META.get('CONTENT_TYPE', '').split(';')[0]
            if content_type:
                c_major, c_minor = content_type.split('/')
                if (major == '*' or major == c_major) and (minor == '*' or minor == c_minor):
                    # The content_type used to send the request matches the accepted formats.
                    # Check if the format is supported.
                    if formats.get(content_type, None):
                        if has_serializer_for(formats.get(content_type)):
                            return formats.get(content_type)
            # The content_type format is not available or supported. Look for the first format
            # that matches the wildcard format request.
            if major == '*':
                # This is our general fallback.
                # TODO put this in a global constant.
                return 'json'
            else:
                for k in formats.keys():
                    m = k.split('/')[0]
                    if major == m and has_serializer_for(formats.get(k)):
                        return formats.get(k)

        if formats.get(f, None) and has_serializer_for(formats.get(f)):
            # We assume the first given format is the default format.
            return formats.get(f)

    return None

#def detect_format(request, default_format='application/json'):
def detect_format(request):
    """
    Detects the format requested by the user.
    """
    if request.GET.get('format', None):
        return [request.GET['format']]

    format_list = media_by_accept_header(request)
    #return format_list or [default_format]
    return format_list


def get_serializers():
	return [s for s in serializers.get_serializer_formats() if s.startswith('rest')]


def media_by_accept_header(request):
    """
    Returns a list of media types according to the preference given
    in the HTTP Accept header. It does not fix the Webkit problem
    having XML headers in front, as this is ok for our RESTful
    interface.

    See for further details:
    http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
    http://www.gethifi.com/blog/browser-rest-http-accept-headers
    """

    media_list = []
    media_range = request.META.get('HTTP_ACCEPT', '*/*').split(',')

    for m in media_range:
        q_val = 1
        parts = m.split('q=')
        media_type = parts.pop(0).rstrip(' ;')
        # what accept extensions are possible? We ignore them
        # for now.
        try:
            q_val = float(parts.pop(1).split(';', 1)[0].rstrip())
        except IndexError:
            pass
        media_list.append( (media_type, q_val) )

    return [i[0] for i in sorted(media_list, key=lambda x: x[1], reverse=True)] 


