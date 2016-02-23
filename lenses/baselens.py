import functools
import abc

from .identity import Identity
from .const import Const
from .functorisor import Functorisor
from .typeclass import fmap, pure, ap, traverse
from .setter import setitem_immutable, setattr_immutable, multi_magic_set


def multiap(func, *args):
    functor = fmap(args[0], func)
    for arg in args[1:]:
        functor = ap(arg, functor)
    return functor


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


class BaseLens(object, metaclass=abc.ABCMeta):
    '''A BaseLens. Serves as the backbone of the lenses library. Acts as an
    object-oriented wrapper around a function that does all the hard
    work. This function is a van Laarhoven lens and has the following
    type (in ML-style notation):

    func :: (value -> functor value), state -> functor state
    '''

    @abc.abstractmethod
    def func(self, f, state):
        pass

    def get(self, state):
        '''Returns the focus within `state`. If multiple items are
        focused then it will attempt to join them together with
        `lenses.typeclass.mappend`. The lens must have at least one
        focus.'''
        def func_pure(a):
            # it's a shame that we can't get values from types that have
            # no focus, but nothing can be done short of carrying type
            # information around all the way through the library.
            raise ValueError('No focus to get')
        const = Functorisor(func_pure, lambda a: Const(a))
        return self.func(const, state).item

    def get_all(self, state):
        'Returns a tuple of all the focuses within `state`.'
        consttup = Functorisor(lambda a: Const(()), lambda a: Const((a,)))
        return self.func(consttup, state).item

    def modify(self, state, fn):
        'Applies a function `fn` to the focus within `state`.'
        identfn = Functorisor(lambda a: Identity(a),
                              lambda a: Identity(fn(a)))
        return self.func(identfn, state).item

    def set(self, state, value):
        'Sets the focus within `state` to `value`.'
        ident = Functorisor(lambda a: Identity(a),
                            lambda a: Identity(value))
        return self.func(ident, state).item

    def compose(self, other):
        '''Composes another lens with this one.

        The `other` lens is used to refine the focus of this lens. The
        following two pieces of code should be equivalent:

        ```
        self.compose(other).get(state)

        other.get(self.get(state))
        ```
        '''
        return ComposedLens([self]).compose(other)

    __and__ = compose


class ComposedLens(BaseLens):

    def __init__(self, lenses=()):
        self.lenses = list(self._filter_lenses(lenses))

    @staticmethod
    def _filter_lenses(lenses):
        for lens in lenses:
            if isinstance(lens, TrivialLens):
                continue
            elif isinstance(lens, ComposedLens):
                yield from lens.lenses
            else:
                yield lens

    def func(self, f, state):
        if not self.lenses:
            return TrivialLens().func(f, state)

        res = f
        for lens in reversed(self.lenses):
            @res.replace_func
            def res(st, res=res, lens=lens):
                return lens.func(res, st)
        return res(state)

    def compose(self, other):
        result = ComposedLens(self.lenses + [other])
        if len(result.lenses) == 0:
            return TrivialLens()
        elif len(result.lenses) == 1:
            return result.lenses[0]
        return result

    def __repr__(self):
        return 'ComposedLens({!r})'.format(self.lenses)


class GetterSetterLens(BaseLens):
    '''Turns a pair of getter and setter functions into a van
    Laarhoven lens. A getter function is one that takes a state and
    returns a value derived from that state. A setter function takes
    an old state and a new value and injects the new value into the
    old state, returning a new state.

    def getter(state) -> value
    def setter(old_state, new_value) -> new_state
    '''

    def __init__(self, getter, setter):
        self.getter = getter
        self.setter = setter

    def func(self, f, state):
        old_value = self.getter(state)
        fa = f(old_value)
        return fmap(fa, lambda a: self.setter(state, a))

    def __repr__(self):
        return 'GetterSetterLens({!r}, {!r})'.format(self.getter, self.setter)


class BothLens(BaseLens):
    '''A traversal that focuses both items [0] and [1].'''

    def func(self, f, state):
        mms = multi_magic_set(state, [(setitem_immutable, 1),
                                      (setitem_immutable, 0)])
        return multiap(mms, f(state[0]), f(state[1]))

    def __repr__(self):
        return 'BothLens()'


class DecodeLens(GetterSetterLens):
    '''A lens that decodes and encodes its focus on the fly. Lets you
    focus a byte string as a unicode string.'''

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def getter(self, state):
        return state.decode(*self.args, **self.kwargs)

    def setter(self, state, focus):
        return focus.encode(*self.args, **self.kwargs)

    def __repr__(self):
        args = [repr(item) for item in self.args]
        kwargs = ['{}={!r}'.format(k, v)
                  for k, v in self.kwargs.items()]
        return 'DecodeLens({})'.format(', '.join(args + kwargs))


class ErrorLens(BaseLens):
    '''A lens that raises an exception whenever it tries to focus
    something. Useful for debugging.'''

    def __init__(self, exception):
        self.exception = exception

    def func(self, f, state):
        raise self.exception

    def __repr__(self):
        return 'ErrorLens({!r})'.format(self.excpetion)


class FilteringLens(BaseLens):
    '''A traversal that only traverses a focus if the predicate returns
    when called with that focus as an argument. Best used when composed
    after a traversal.'''

    def __init__(self, predicate):
        self.predicate = predicate

    def func(self, f, state):
        return f(state) if self.predicate(state) else pure(f(state), state)

    def __repr__(self):
        return 'FilteringLens({!r})'.format(self.predicate)


class GetattrLens(GetterSetterLens):
    '''A lens that focuses an attribute of an object. Analogous to
    `getattr`.'''

    def __init__(self, name):
        self.name = name

    def getter(self, state):
        return getattr(state, self.name)

    def setter(self, state, focus):
        return setattr_immutable(state, self.name, focus)

    def __repr__(self):
        return 'GetattrLens({!r})'.format(self.name)


class GetitemLens(GetterSetterLens):
    '''A lens that focuses an item inside a container. Analogous to
    `operator.itemgetter`.'''

    def __init__(self, key):
        self.key = key

    def getter(self, state):
        return state[self.key]

    def setter(self, state, focus):
        return setitem_immutable(state, self.key, focus)

    def __repr__(self):
        return 'GetitemLens({!r})'.format(self.key)


class ItemLens(GetterSetterLens):
    '''A lens that focuses a single item (key-value pair) in a
    dictionary by its key.'''

    def __init__(self, key):
        self.key = key

    def getter(self, state):
        try:
            return self.key, state[self.key]
        except KeyError:
            return None

    def setter(self, state, focus):
        data = {k: v for k, v in state.items() if k != self.key}
        if focus is not None:
            data[focus[0]] = focus[1]
        return data

    def __repr__(self):
        return 'ItemLens({!r})'.format(self.key)


class ItemByValueLens(GetterSetterLens):
    '''A lens that focuses a single item (key-value pair) in a
    dictionary by its value.'''

    def __init__(self, value):
        self.value = value

    def getter(self, state):
        for dkey, dvalue in state.items():
            if dvalue is self.value:
                return dkey, dvalue

    def setter(self, state, focus):
        data = {k: v for k, v in state.items() if v != self.value}
        if focus is not None:
            data[focus[0]] = focus[1]
        return data

    def __repr__(self):
        return 'ItemByValueLens({!r})'.format(self.key)


class ItemsLens(BaseLens):
    '''A traversal focusing key-value tuples that are the items of a
    dictionary. Analogous to `dict.items`.'''

    def func(self, f, state):
        items = list(state.items())
        if items == []:
            return f.get_pure(state)

        @starargs_curry(len(items))
        def dict_builder(*args):
            return dict(args)

        return multiap(dict_builder, *map(f, items))

    def __repr__(self):
        return 'ItemsLens()'


class JsonLens(GetterSetterLens):
    '''A lens that focuses a string containing json data as its parsed
    equivalent. Analogous to `json.loads`.'''

    def __init__(self):
        self.json_mod = __import__('json')

    def getter(self, state):
        return self.json_mod.loads(state)

    def setter(self, state, focus):
        return self.json_mod.dumps(focus)

    def __repr__(self):
        return 'JsonLens()'


class KeysLens(ComposedLens):
    '''A traversal focusing the keys of a dictionary. Analogous to
    `dict.keys`.'''

    def __init__(self):
        self.lenses = [ItemsLens(), GetitemLens(0)]

    def __repr__(self):
        return 'KeysLens()'


class TraverseLens(BaseLens):
    '''A traversal that focuses everything in a data structure depending
    on how that data structure defines `lenses.typeclass.traverse`. Usually
    somewhat similar to iterating over it.'''

    def func(self, f, state):
        return traverse(state, f)

    def __repr__(self):
        return 'TraverseLens()'


class TrivialLens(BaseLens):
    '''A trivial lens that focuses the whole state. Analogous to
    `lambda a: a`.'''

    def func(self, f, state):
        return fmap(f(state), lambda newvalue: newvalue)

    def __repr__(self):
        return 'TrivialLens()'


class TupleLens(GetterSetterLens):
    '''A lens that combines the focuses of other lenses into a
    single tuple.'''

    def __init__(self, *lenses):
        self.lenses = lenses

    def getter(self, state):
        return tuple(lens.get(state) for lens in self.lenses)

    def setter(self, state, focus):
        for lens, new_value in zip(self.lenses, focus):
            state = lens.set(state, new_value)
        return state

    def __repr__(self):
        args = ', '.join(repr(lens) for lens in self.lenses)
        return 'TupleLens({})'.format(args)


class ValuesLens(ComposedLens):
    '''A traversal focusing the values of a dictionary. Analogous to
    `dict.values`.'''

    def __init__(self):
        self.lenses = [ItemsLens(), GetitemLens(1)]

    def __repr__(self):
        return 'ValuesLens()'


class ZoomAttrLens(BaseLens):
    '''A lens that looks up an attribute on its target and follows it as
    if were a bound `Lens` object.'''

    def __init__(self, name):
        self.name = name

    def func(self, f, state):
        l = getattr(state, self.name)
        return l.lens.func(f, state)

    def __repr__(self):
        return 'ZoomAttrLens({!r})'.format(self.name)


class ZoomLens(BaseLens):
    '''Follows its state as it were a bound `Lens` object.'''

    def func(self, f, state):
        return state.lens.func(f, state.state)

    def __repr__(self):
        return 'ZoomLens()'
