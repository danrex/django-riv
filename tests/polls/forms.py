from django import forms
from models import Poll, Choice

class VoteForm(forms.Form):
    poll = forms.ModelChoiceField(queryset=Poll.objects.all())
    choice = forms.ModelChoiceField(queryset=Choice.objects.all())

    def clean(self):
        cd = super(VoteForm, self).clean()
        poll = cd.get('poll')
        choice = cd.get('choice')

        if poll and choice:
            try:
                Choice.objects.get(id=choice.id, poll=poll.id)
            except Choice.DoesNotExist:
                msg = u"Invalid choice for the given poll."
                self._errors['choice'] = self.error_class([msg])
                del cd['choice']

        return cd

class PollForm(forms.ModelForm):
    class Meta:
        model = Poll
        fields = "__all__"
