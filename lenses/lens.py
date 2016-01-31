import operator

from .identity import Identity
from .const import Const
from .typeclass import fmap, ap, traverse
from .setter import magic_set, multi_magic_set


class Lens(object):
    '''A Lens. Serves as the backbone of the lenses library. Acts as an
    object-oriented wrapper around a function that does all the hard
    work. This function is a van Laarhoven lens and has the following
    type (in ML-style notation):

    func :: (value -> functor value), state -> functor state
    '''
    __slots__ = ['func']

    def __init__(self, func):
        self.func = func

    @classmethod
    def from_getter_setter(cls, getter, setter):
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
            return fmap(fa, lambda a: setter(a, state))

        return cls(new_func)

    @classmethod
    def trivial(cls):
        '''A trivial lens that magnifies to the whole state.'''
        def _(func, state):
            return fmap(func(state), lambda newvalue: newvalue)
        return cls(_)

    @classmethod
    def getattr(cls, name):
        '''A lens that magnifies an attribute on an object'''
        return _magic_set_lens(name, 'setattr', getattr)

    @classmethod
    def getitem(cls, key):
        '''A lens that magnifies an item inside a container'''
        return _magic_set_lens(key, 'setitem', operator.getitem)

    @classmethod
    def both(cls):
        '''A traversal that magnifies both items [0] and [1].'''
        def _(func, state):
            mms = multi_magic_set(state, [('setitem', 1), ('setitem', 0)])
            return ap(func(state[1]), fmap(func(state[0]), mms))
        return cls(_)

    @classmethod
    def item(cls, old_key):
        '''A lens that magnifies an item (key-value pair) in a dictionary by
        its key'''
        def _(fn, state):
            return fmap(
                fn((old_key, state[old_key])),
                lambda new_value: dict([new_value] + [
                    (k, v) for k, v in state.items() if k is not old_key
                ])
            )

        return cls(_)

    @classmethod
    def item_by_value(cls, old_value):
        '''A lens that magnifies an item (key-value pair) in a dictionary by
        its value.'''
        def getter(state):
            for dkey, dvalue in state.items():
                if dvalue is old_value:
                    return dkey, dvalue
            raise LookupError('{} not in dict'.format(old_value))

        def setter(new_value, state):
            return dict([new_value] + [
                (k, v) for k, v in state.items() if v is not old_value])

        return cls.from_getter_setter(getter, setter)

    @classmethod
    def items(cls):
        '''A lens focusing a dictionary as a list of key-value tuples.
        Similar to dict.items'''
        def _(fn, state):
            return fmap(fn(state.items()), dict)
        return cls(_)

    @classmethod
    def tuple(cls, *some_lenses):
        '''takes some lenses and returns a lens that magnifies a tuple with
        values taken from all the lenses'''
        def getter(state):
            return tuple(a_lens.get(state) for a_lens in some_lenses)

        def setter(new_values, state):
            for a_lens, new_value in zip(some_lenses, new_values):
                state = a_lens.set(state, new_value)
            return state

        return cls.from_getter_setter(getter, setter)

    @classmethod
    def traverse(cls):
        '''A traversal that focuses everything in a data structure depending
        on how that data structure defines `lenses.typeclass.traverse`. Usually
        somewhat similar to iterating over it.'''
        return cls(lambda fn, state: traverse(state, fn))

    @classmethod
    def decode(cls, *args, **kwargs):
        '''A lens that decodes and encodes one the fly. Lets you focus a
        byte string as a unicode string.'''
        def getter(state):
            return state.decode(*args, **kwargs)

        def setter(new_value, old_state):
            return new_value.encode(*args, **kwargs)

        return cls.from_getter_setter(getter, setter)

    def get(self, state):
        'Returns the value this lens is magnified on.'
        return self.func(lambda a: Const(a), state).item

    def get_all(self, state):
        'Returns all values this lens traverses over.'
        return self.func(lambda a: Const((a, )), state).item

    def modify(self, state, fn):
        'Applies a function to the magnified value.'
        return self.func(lambda a: Identity(fn(a)), state).item

    def set(self, state, newitem):
        'Sets the magnified value in the passed state.'
        return self.func(lambda a: Identity(newitem), state).item

    def compose(self, other):
        '''Composes another lens with this one.

        The `other` lens is used to refine the `self` lens. The
        following two pieces of code should be equivalent:

        ```
        self.compose(other).get(state)

        other.get(self.get(state))
        ```
        '''

        def new_func(fn, state):
            return self.func((lambda state2: other.func(fn, state2)), state)

        return Lens(new_func)

    __and__ = compose


def _magic_set_lens(name, method, getter):
    @Lens
    def new_lens(fn, state):
        return fmap(
            fn(getter(state, name)),
            lambda newvalue: magic_set(state, method, name, newvalue))

    return new_lens
