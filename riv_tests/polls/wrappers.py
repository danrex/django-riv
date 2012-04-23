from riv.wrappers import BaseWrapper
from riv.helpers import call_view
from polls import views

class PollWrapper(BaseWrapper):
	read = call_view(views.detail)
	read_multiple = call_view(views.index)
	delete = call_view(views.delete)
	update = call_view(views.update)

	#create = views.add
