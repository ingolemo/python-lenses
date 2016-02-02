from .lens import Lens
from .simplelens import SimpleLens


class MethodLens:
    '''Allows defining a lens directly inside a class'''

    def __init__(self, fget, fset=None, doc=''):
        if not doc:
            doc = fget.__doc__

        self.doc = doc
        self.fget = fget
        self.fset = fset

    def _make_lens(self, obj):
        def _(*args, **kwargs):
            def getter(state):
                return self.fget(state, *args, **kwargs)

            def setter(value, state):
                return self.fset(state, value, *args, **kwargs)

            return Lens(obj, SimpleLens.from_getter_setter(getter, setter))
        return _

    def __call__(self, obj):
        return self._make_lens(obj)()

    def __get__(self, obj, objtype=None):
        return self._make_lens(obj)

    def setter(self, fset):
        self.fset = fset
        return self
