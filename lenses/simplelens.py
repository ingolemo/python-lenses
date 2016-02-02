import operator
import functools

from .identity import Identity
from .const import Const
from .typeclass import fmap, ap, traverse
from .setter import setitem_immutable, setattr_immutable, multi_magic_set


def starargs_curry(n):
    def decorator(fn):

        @functools.wraps(fn)
        def wrapper(arg):
            args = []

            def arg_collector(arg):
                nonlocal args
                args.append(arg)
                if len(args) == n:
                    return fn(*args)
                else:
                    return arg_collector

            return arg_collector(arg)
        return wrapper
    return decorator


class SimpleLens(object):
    '''A SimpleLens. Serves as the backbone of the lenses library. Acts as an
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
        '''Turns a pair of getter and setter functions into a van
        Laarhoven lens. A getter function is one that takes a state and
        returns a value derived from that state. A setter function takes
        an old state and a new value and injects the new value into the
        old state, returning a new state.

        def getter(state) -> value
        def setter(old_state, new_value) -> new_state
        '''

        def _(func, state):
            old_value = getter(state)
            fa = func(old_value)
            return fmap(fa, lambda a: setter(state, a))

        return cls(_)

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
        def getter(state):
            return getattr(state, name)

        def setter(state, value):
            return setattr_immutable(state, name, value)

        return SimpleLens.from_getter_setter(getter, setter)

    @classmethod
    def getitem(cls, key):
        '''A lens that focuses an item inside a container. Analogous to
        `operator.itemgetter`.'''
        def setter(state, value):
            return setitem_immutable(state, key, value)

        return SimpleLens.from_getter_setter(operator.itemgetter(key), setter)

    @classmethod
    def both(cls):
        '''A traversal that focuses both items [0] and [1].'''
        def _(func, state):
            mms = multi_magic_set(state, [(setitem_immutable, 1),
                                          (setitem_immutable, 0)])
            return ap(func(state[1]), fmap(func(state[0]), mms))
        return cls(_)

    @classmethod
    def item(cls, old_key):
        '''A lens that focuses a single item (key-value pair) in a
        dictionary by its key.'''
        def getter(state):
            try:
                return old_key, state[old_key]
            except KeyError:
                return None

        def setter(state, value):
            data = {k: v for k, v in state.items() if k is not old_key}
            if value is not None:
                data[value[0]] = value[1]
            return data

        return SimpleLens.from_getter_setter(getter, setter)

    @classmethod
    def item_by_value(cls, old_value):
        '''A lens that focuses a single item (key-value pair) in a
        dictionary by its value.'''
        def getter(state):
            for dkey, dvalue in state.items():
                if dvalue is old_value:
                    return dkey, dvalue
            raise LookupError('{} not in dict'.format(old_value))

        def setter(state, new_value):
            return dict([new_value] + [
                (k, v) for k, v in state.items() if v is not old_value])

        return cls.from_getter_setter(getter, setter)

    @classmethod
    def items(cls):
        '''A lens focusing a dictionary as a list of key-value tuples.
        Analogous to `dict.items`.'''
        def _(fn, state):
            items = list(state.items())

            @starargs_curry(len(items))
            def dict_builder(*args):
                return dict(args)

            dict_partial = fmap(fn(items[0]), dict_builder)
            for item in items[1:]:
                dict_partial = ap(fn(item), dict_partial)

            return dict_partial
        return cls(_)

    @classmethod
    def tuple(cls, *some_lenses):
        '''A lens that combines the focuses of other lenses into a
        single tuple.'''
        def getter(state):
            return tuple(a_lens.get(state) for a_lens in some_lenses)

        def setter(state, new_values):
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

        def setter(old_state, new_value):
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

        return SimpleLens(new_func)

    __and__ = compose
