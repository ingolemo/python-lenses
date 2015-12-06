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
    '''Handles setting items in tuples.

    Assumes that if we try to set an attribute on a tuple then it is
    actually a namedtuple.'''
    if kind == 'setitem':
        return tuple(value if i == key else item
                     for i, item in enumerate(self))
    elif kind == 'setattr':
        return type(self)(*(value if field == key else item
                            for field, item in zip(self._fields, self)))


def make_lens(getter, setter):
    '''turns a pair of getter and setter functions into a van Laarhoven
    lens. A getter function is one that takes a state and returns a
    value derived from that state. A setter function takes a new value and
    an old state and injects the new value into the old state, returning
    a new state.

    make_lens :: getter_func, setter_func -> Lens
    getter_func :: state -> value
    setter_func :: new_value, old_state -> new_state
    '''

    def new_func(func, state):
        old_value = getter(state)
        fa = func(old_value)
        return functor.fmap(fa, lambda a: setter(a, state))

    return Lens(new_func)


class Lens:
    '''A Lens. Serves as the backbone of the lenses library. Acts as an
    object-oriented wrapper around a function that does all the hard
    work. This function is a van Laarhoven lens and has the following
    type (in ML-style notation):

    func :: (value -> functor value), state -> functor state
    '''
    __slots__ = ['func']

    def __init__(self, func):
        self.func = func

    def get(self, state):
        'Returns the value this lens is magnified on.'
        return self.func(lambda a: functor.Const(a), state).item

    def modify(self, state, fn):
        'Applies a function to the magnified value.'
        return self.func(lambda a: functor.Identity(fn(a)), state).item

    def set(self, state, newitem):
        'Sets the magnified value in the passed state.'
        return self.func(lambda a: functor.Identity(newitem), state).item

    def compose(self, other):
        '''Composes another lens with this one.

        The order of composition is technically backwards from what it
        should be. The operator is more useful and conceptually simpler
        this way around. The `other` lens is used to refine the `self`
        lens. The following two pieces of code should be equivalent:

            self.compose(other).get(state)

            other.get(self.get(state))
        '''

        def new_func(fn, state):
            return self.func((lambda state2: other.func(fn, state2)), state)

        return Lens(new_func)
