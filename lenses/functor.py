import functools


class Functor:
    pass


class Identity(Functor):
    def __init__(self, item):
        self.item = item

    def fmap(self, fn):
        return Identity(fn(self.item))


class Const(Functor):
    def __init__(self, item):
        self.item = item

    def fmap(self, func):
        return Const(self.item)


@functools.singledispatch
def fmap(functor, func):
    '''Applies a function to the data 'inside' a functor.

    Uses functools.singledispatch so you can write your own functors
    for use with the library.'''
    raise NotImplementedError


@fmap.register(Functor)
def _(functor, func):
    return functor.fmap(func)
