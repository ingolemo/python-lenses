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
        '''Turns a pair of getter and setter functions into a van Laarhoven
        lens. A getter function is one that takes a state and returns a
        value derived from that state. A setter function takes a new value and
        an old state and injects the new value into the old state, returning
        a new state.

        def getter(state) -> value
        def setter(new_value, old_state) -> new_state
        '''

        def new_func(func, state):
            old_value = getter(state)
            fa = func(old_value)
            return fmap(fa, lambda a: setter(a, state))

        return cls(new_func)

    @classmethod
    def trivial(cls):
        '''A trivial lens that focuses the whole state. Analogous to
        `lambda a: a`.'''
        def _(func, state):
            return fmap(func(state), lambda newvalue: newvalue)
        return cls(_)

    @classmethod
    def getattr(cls, name):
        '''A lens that focuses an attribute of an object. Analogous to
        `getattr`.'''
        return _magic_set_lens(name, 'setattr', getattr)

    @classmethod
    def getitem(cls, key):
        '''A lens that focuses an item inside a container. Analogous to
        `operator.itemgetter`.'''
        return _magic_set_lens(key, 'setitem', operator.getitem)

    @classmethod
    def both(cls):
        '''A traversal that focuses both items [0] and [1].'''
        def _(func, state):
            mms = multi_magic_set(state, [('setitem', 1), ('setitem', 0)])
            return ap(func(state[1]), fmap(func(state[0]), mms))
        return cls(_)

    @classmethod
    def item(cls, old_key):
        '''A lens that focuses a single item (key-value pair) in a
        dictionary by its key.'''
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
        '''A lens that focuses a single item (key-value pair) in a
        dictionary by its value.'''
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
        Analogous to `dict.items`.'''
        def _(fn, state):
            return fmap(fn(state.items()), dict)
        return cls(_)

    @classmethod
    def tuple(cls, *some_lenses):
        '''A lens that combines the focuses of other lenses into a
        single tuple.'''
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
        '''A lens that decodes and encodes its focus the fly. Lets you
        focus a byte string as a unicode string.'''
        def getter(state):
            return state.decode(*args, **kwargs)

        def setter(new_value, old_state):
            return new_value.encode(*args, **kwargs)

        return cls.from_getter_setter(getter, setter)

    def get(self, state):
        '''Returns the focus within `state`. If multiple items are
        focused then it will attempt to join them together with
        `lenses.typeclass.mappend`.'''
        return self.func(lambda a: Const(a), state).item

    def get_all(self, state):
        'Returns a tuple of all the focuses within `state`.'
        return self.func(lambda a: Const((a, )), state).item

    def modify(self, state, fn):
        'Applies a function `fn` to the focus within `state`.'
        return self.func(lambda a: Identity(fn(a)), state).item

    def set(self, state, value):
        'Sets the focus within `state` to `value`.'
        return self.func(lambda a: Identity(value), state).item

    def compose(self, other):
        '''Composes another lens with this one.

        The `other` lens is used to refine the focus of this lens. The
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
