from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.template import RequestContext
from django.forms.models import modelformset_factory
from forms import PollForm, VoteForm
from models import Poll, Choice

from riv.shortcuts import render_to_rest, render_form_error_to_rest

def poll_index(request):
    poll_list = Poll.objects.all().order_by('-pub_date')
    if request.is_rest():
        return render_to_rest(poll_list)
    return render_to_response('index.html',  {
        'poll_list': poll_list,
    })

def poll_detail(request, id):
    p = get_object_or_404(Poll, pk=id)
    if request.is_rest():
        return render_to_rest(p)
    return render_to_response('detail.html', {'poll': p})

def poll_create_or_update(request, id=None):
    if id:
        p = get_object_or_404(Poll, pk=id)
    if request.method == 'POST':
        if id:
            form = PollForm(request.POST, instance=p)
        else:
            form = PollForm(request.POST)
        if form.is_valid():
            obj = form.save()
            return render_to_rest(obj)
        else:
            if request.is_rest():
                return render_form_error_to_rest(form)
    else:
        if id:
            form = PollForm(instance=p)
        else:
            form = PollForm()

    return render_to_response('update.html', {
        'form': form,
        }, context_instance=RequestContext(request)
    )

def poll_create_multiple(request):
    PollFormSet = modelformset_factory(Poll)
    if request.method == 'POST':
        formset = PollFormSet(request.POST)
        if formset.is_valid():
            objects = formset.save()
            return render_to_rest(objects)
        else:
            if request.is_rest():
                return render_form_error_to_rest(formset)
    else:
        formset = PollFormSet()

    return render_to_response('update.html', {
        'formset': formset,
        }, context_instance=RequestContext(request)
    )

def poll_delete(request, id):
    p = get_object_or_404(Poll, pk=id)
    p.delete()
    if request.is_rest():
        return HttpResponse(status=204)
    return render_to_response('deleted.html')

@login_required
def results(request, id):
    poll = get_object_or_404(Poll, pk=id)
    if request.is_rest():
        result = {'choice': []}
        for choice in poll.choice_set.all():
            result['choice'].append({'name': choice.choice, 'votes': choice.votes})
        return render_to_rest(result)
    return render_to_response('results.html', {
        'poll': poll,
        }, context_instance=RequestContext(request)
    )
    
def vote(request):
    if request.method == 'POST':
        form = VoteForm(request.POST)
        if form.is_valid():
            choice = form.cleaned_data.get('choice')
            choice.votes += 1
            choice.save()
            return render_to_rest({'poll': choice.poll.id, 'choice': choice.id})
        else:
            return render_form_error_to_rest(form)
    raise Http404
