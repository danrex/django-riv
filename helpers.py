def call_view(view):
    def selffunc(self, *args, **kwargs):
        return view(*args, **kwargs)
    return selffunc
