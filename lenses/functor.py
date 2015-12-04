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
    raise NotImplementedError


@fmap.register(Functor)
def _(functor, func):
    return functor.fmap(func)
