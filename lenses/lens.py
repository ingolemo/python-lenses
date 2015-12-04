import functools
import copy

from . import functor


def _rich_setter(self, kind, key, value):
    try:
        self.lens_setter
    except AttributeError:
        return setter(self, kind, key, value)
    else:
        return self.lens_setter(kind, key, value)


@functools.singledispatch
def setter(self, kind, key, value):
    '''returns a copy of self with key replaced by value.

    kind is either 'setitem' or 'setattr' depending on how the lens
    was accessed. The default approach is to make a copy of self and
    attempt to mutate the copy.
    '''
    selfcopy = copy.copy(self)
    if kind == 'setitem':
        selfcopy[key] = value
    elif kind == 'setattr':
        setattr(selfcopy, key, value)
    return selfcopy


@setter.register(tuple)
def _(self, kind, key, value):
    if kind == 'setitem':
        return tuple(value if i == key else item
                     for i, item in enumerate(self))
    elif kind == 'setattr':
        # probably a namedtuple
        return type(self)(*(value if field == key else item
                            for field, item in zip(self._fields, self)))


class Lens:
    'A no-frills lens class. serves as the backbone of the lenses library'

    def __init__(self, func):
        # func :: (a -> f a) -> s -> f s
        self.func = func

    def get(self, state):
        return self.func(lambda a: functor.Const(a), state).item

    def modify(self, state, fn):
        return self.func(lambda a: functor.Identity(fn(a)), state).item

    def set(self, state, newitem):
        return self.func(lambda a: functor.Identity(newitem), state).item

    def compose(self, other):
        def new_func(fn, state):
            return self.func((lambda state2: other.func(fn, state2)), state)

        return Lens(new_func)
