from riv.wrappers import BaseWrapper
from riv.helpers import call_view
from polls import views

#class ChoiceWrapper(BaseWrapper):
#	read = call_view(views.choice_detail)
#	read_multiple = call_view(views.choice_index)
#	delete = call_view(views.choice_delete)
#	update = call_view(views.choice_update)

class PollWrapper(BaseWrapper):
	read = call_view(views.poll_detail)
	read_multiple = call_view(views.poll_index)
	delete = call_view(views.poll_delete)
	update = call_view(views.poll_update)

	#create = views.add
