from .typeclass import fmap


class Functorisor:
    '''A Functorisor encaptulates a function that returns a applicative
    functor. We sometimes need to get a pure version of the result of
    said function, and the functorisor allows us to carry that
    information around as an attribute.

    This makes it possible to traverse empty sequences.'''

    def __init__(self, pure_func, func):
        self.get_pure = pure_func
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def fmap(self, f):
        def new_f(a):
            return fmap(self.func(a), f)
        return Functorisor(self.get_pure, new_f)

    def replace_func(self, fn):
        return Functorisor(self.get_pure, fn)
