from .typeclass import fmap


class Functorisor(object):
    """A Functorisor is a wrapper around an ordinary function that carries
    information about the return type of that function. Specifically
    it wraps functions that return an applicative functor. In haskell
    notation:

        func :: a -> Applicative b

    This is neccessary because some functions want to access the result of
    `pure :: b -> Applicative b` without having an `a` to call the function
    with (and thereby being unable to determine which `b` to call `pure` on,
    which the Python implementation requires).

    The Functorisor solves this problem by carrying around a `pure`
    function. It's a hack, but it works well enough."""

    __slots__ = ("pure", "func")

    def __init__(self, pure_func, func):
        self.pure = pure_func
        self.func = func

    def __call__(self, arg):
        return self.func(arg)

    def map(self, f):
        def new_f(a):
            return fmap(self.func(a), f)

        return Functorisor(self.pure, new_f)

    def update(self, fn):
        return Functorisor(self.pure, lambda state: fn(self, state))
