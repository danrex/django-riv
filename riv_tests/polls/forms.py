from django.forms import ModelForm
from models import Poll, Choice

class PollForm(ModelForm):
	class Meta:
		model = Poll
