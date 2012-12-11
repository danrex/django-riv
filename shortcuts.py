from riv import RestResponse

def render_to_rest(data):
    return RestResponse(content=data)

def render_form_error(form):
    return RestResponse(form=form)
