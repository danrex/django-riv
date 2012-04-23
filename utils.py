def detect_format(request, default_format='application/json'):
	"""
	Detects the format the user hast requested.
	"""
	if request.GET.get('format', None):
		return request.GET['format']

	format_list = media_by_accept_header(request)
	return format_list or default_format
	

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

	return [i[0] for i in sorted(tl, key=lambda x: x[1], reverse=True)]	


def dictionize_list_for_formsets(l):
	d = {}
	for (counter, data) in enumerate(l):
		d.update(dict([(unicode("form-"+str(counter)+"-"+str(k)), v) for (k,v) in data.items()]))
	d.update({'form-TOTAL_FORMS': unicode(counter+1), 'form-INITIAL_FORMS': u'0', 'form-MAX_NUM_FORMS': u''})
	return d
