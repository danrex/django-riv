from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse
from django.template import RequestContext
from forms import PollForm
from models import Poll

from riv.shortcuts import render_to_rest, render_form_error

def poll_index(request):
	poll_list = Poll.objects.all().order_by('-pub_date')
	if request.is_rest():
		return render_to_rest(poll_list)
		#request.rest_info.queryset = poll_list
		# TODO: Rewrite required.
		#return HttpResponse(request.tmp_resource.as_json(poll_list), content_type='application/json; charset=utf8')
	return render_to_response('index.html',  {
		'poll_list': poll_list,
	})

def poll_detail(request, id):
	p = get_object_or_404(Poll, pk=id)
	if request.is_rest():
		return render_to_rest(p)
		#request.rest_info.queryset = p
		# TODO: Rewrite required.
		#return HttpResponse(request.tmp_resource.as_json(p), content_type='application/json; charset=utf8')
	return render_to_response('detail.html', {'poll': p})

def poll_update(request, id):
	p = get_object_or_404(Poll, pk=id)
	if request.method == 'POST':
		form = PollForm(request.POST, instance=p)
		if form.is_valid():
			form.save()
			return HttpResponse("ok")
		else:
			if request.is_rest():
				return render_form_error(form)
				#request.rest_info.error_by_form(form)
				#return HttpResponse()
	else:
		form = PollForm(instance=p)

	return render_to_response('update.html', {
		'form': form,
		}, context_instance=RequestContext(request)
	)

def poll_delete(request, id):
	p = get_object_or_404(Poll, pk=id)
	p.delete()
	if request.is_rest():
		return HttpResponse(status=204)
	return render_to_response('deleted.html')

def results(request, id):
	pass

def vote(request, id):
	pass

def add(request):
	pass
