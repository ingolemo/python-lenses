import abc

from . import setter
from .identity import Identity
from .const import Const
from .functorisor import Functorisor
from .typeclass import fmap, pure, ap, traverse


def multiap(func, *args):
    '''Applies `func` to the data inside the `args` functors
    incrementally. `func` must be a curried function that takes
    `len(args)` arguments.

        >>> func = lambda a: lambda b: a + b
        >>> multiap(func, [1, 10], [100])
        [101, 110]
    '''
    functor = fmap(args[0], func)
    for arg in args[1:]:
        functor = ap(arg, functor)
    return functor


def collect_args(n):
    '''Returns a function that can be called `n` times with a single
    argument before returning all the args that have been passed to it
    in a tuple. Useful as a substitute for functions that can't easily be
    curried.

        >>> from lenses.baselens import collect_args
        >>> collect_args(3)(1)(2)(3)
        (1, 2, 3)
    '''
    args = []

    def arg_collector(arg):
        nonlocal args
        args.append(arg)
        if len(args) == n:
            return tuple(args)
        else:
            return arg_collector
    return arg_collector


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
        consttup = Functorisor(
            lambda a: Const(()), lambda a: Const((a,)))
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
    '''A lenses representing the composition of several sublenses.'''

    def __init__(self, lenses=()):
        self.lenses = list(self._filter_lenses(lenses))

    @staticmethod
    def _filter_lenses(lenses):
        for lens in lenses:
            if isinstance(lens, TrivialLens):
                continue
            elif type(lens) is ComposedLens:
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
    '''A traversal that focuses both items [0] and [1].

        >>> from lenses import lens
        >>> lens().both_()
        Lens(None, BothLens())
        >>> lens([1, 2, 3]).both_().get_all()
        (1, 2)
        >>> lens([1, 2, 3]).both_().set(4)
        [4, 4, 3]
    '''

    def func(self, f, state):
        def multisetter(items):
            s = setter.setitem_immutable(state, 0, items[0])
            s = setter.setitem_immutable(s, 1, items[1])
            return s
        return fmap(multiap(collect_args(2), f(state[0]), f(state[1])),
                    multisetter)

    def __repr__(self):
        return 'BothLens()'


class DecodeLens(GetterSetterLens):
    '''A lens that decodes and encodes its focus on the fly. Lets you
    focus a byte string as a unicode string.

        >>> from lenses import lens
        >>> lens().decode_(encoding='utf8')
        Lens(None, DecodeLens(encoding='utf8'))
        >>> lens(b'hello').decode_().get()
        'hello'
        >>> lens(b'hello').decode_().set('world')
        b'world'
    '''

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


class EachLens(BaseLens):
    '''A traversal that iterates over its state, focusing everything it
    iterates over. It uses `setter.fromiter` to reform the state
    afterwards so it should work with an iterable that function
    supports. Analogous to `iter`.

        >>> from lenses import lens
        >>> data = [1, 2, 3]
        >>> lens().each_()
        Lens(None, EachLens())
        >>> lens(data).each_().get_all()
        (1, 2, 3)
        >>> lens(data).each_().modify(lambda n: n + 1)
        [2, 3, 4]
    '''

    def func(self, f, state):
        items = list(state)
        if items == []:
            return f.get_pure(state)

        return fmap(multiap(collect_args(len(items)), *map(f, items)),
                    lambda a: setter.fromiter(state, a))

    def __repr__(self):
        return 'EachLens()'


class ErrorLens(BaseLens):
    '''A lens that raises an exception whenever it tries to focus
    something. Useful for debugging.

        >>> from lenses import lens
        >>> lens().error_(Exception())
        Lens(None, ErrorLens(Exception()))
        >>> lens(True).error_(Exception()).get()
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        Exception
        >>> lens(True).error_(Exception()).set(False)
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        Exception
    '''

    def __init__(self, exception):
        self.exception = exception

    def func(self, f, state):
        raise self.exception

    def __repr__(self):
        return 'ErrorLens({!r})'.format(self.exception)


class FilteringLens(BaseLens):
    '''A traversal that only traverses a focus if the predicate returns
    when called with that focus as an argument. Best used when composed
    after a traversal.

        >>> from lenses import lens
        >>> lens().filter_(bool)
        Lens(None, FilteringLens(<class 'bool'>))
        >>> lens([0, 1, '', 'hi']).traverse_().filter_(bool).get_all()
        (1, 'hi')
        >>> lens([0, 1, '', 'hi']).traverse_().filter_(bool).set(2)
        [0, 2, '', 2]
    '''

    def __init__(self, predicate):
        self.predicate = predicate

    def func(self, f, state):
        return f(state) if self.predicate(state) else pure(f(state), state)

    def __repr__(self):
        return 'FilteringLens({!r})'.format(self.predicate)


class GetattrLens(GetterSetterLens):
    '''A lens that focuses an attribute of an object. Analogous to
    `getattr`.

        >>> from lenses import lens
        >>> from collections import namedtuple
        >>> Either = namedtuple('Either', 'left right')
        >>> lens().left
        Lens(None, GetattrLens('left'))
        >>> lens().getattr_('right')
        Lens(None, GetattrLens('right'))
        >>> lens(Either(1, 2)).left.get()
        1
        >>> lens(Either(1, 2)).right.set(3)
        Either(left=1, right=3)
    '''

    def __init__(self, name):
        self.name = name

    def getter(self, state):
        return getattr(state, self.name)

    def setter(self, state, focus):
        return setter.setattr_immutable(state, self.name, focus)

    def __repr__(self):
        return 'GetattrLens({!r})'.format(self.name)


class GetitemLens(GetterSetterLens):
    '''A lens that focuses an item inside a container. Analogous to
    `operator.itemgetter`.

        >>> from lenses import lens
        >>> lens()[0]
        Lens(None, GetitemLens(0))
        >>> lens().getitem_(0)
        Lens(None, GetitemLens(0))
        >>> lens([1, 2, 3])[0].get()
        1
        >>> lens({'hello': 'world'})['hello'].get()
        'world'
        >>> lens([1, 2, 3])[0].set(4)
        [4, 2, 3]
        >>> lens({'hello': 'world'})['hello'].set('universe')
        {'hello': 'universe'}
    '''

    def __init__(self, key):
        self.key = key

    def getter(self, state):
        return state[self.key]

    def setter(self, state, focus):
        return setter.setitem_immutable(state, self.key, focus)

    def __repr__(self):
        return 'GetitemLens({!r})'.format(self.key)


class GetterLens(GetterSetterLens):
    '''A lens that applies a function to its focus when the focus is
    retrieved, but will just sets whatever it is asked. This lens
    allows you to post-process values as you retrieve them, but still
    lets you set values directly. Equivalent to
    `GetterSetterLens(getter, (lambda s, f: f))'.

    Note that modify does both a get and a set.

        >>> from lenses import lens
        >>> lens().getter_(str)
        Lens(None, GetterLens(<class 'str'>))
        >>> lens([1, 2, 3])[0].getter_(str).get()
        '1'
        >>> lens([1, 2, 3])[0].getter_(str).set(4)
        [4, 2, 3]
        >>> lens([1, 2, 3])[0].getter_(str).modify(lambda a: a+'.')
        ['1.', 2, 3]
    '''

    def __init__(self, getter):
        self.getter = getter

    def setter(self, state, focus):
        return focus

    def __repr__(self):
        return 'GetterLens({!r})'.format(self.getter)


class ItemLens(GetterSetterLens):
    '''A lens that focuses a single item (key-value pair) in a
    dictionary by its key. Set an item to `None` to remove it from the
    dictionary.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().item_(1)
        Lens(None, ItemLens(1))
        >>> lens(data).item_(1).get()
        (1, 10)
        >>> lens(data).item_(1).set((1, 11))
        OrderedDict([(1, 11), (2, 20)])
        >>> lens(data).item_(1).set(None)
        OrderedDict([(2, 20)])
    '''

    def __init__(self, key):
        self.key = key

    def getter(self, state):
        try:
            return self.key, state[self.key]
        except KeyError:
            return None

    def setter(self, state, focus):
        data = state.copy()
        if focus is None:
            del data[self.key]
            return data
        if focus[0] != self.key:
            del data[self.key]
        data[focus[0]] = focus[1]
        return data

    def __repr__(self):
        return 'ItemLens({!r})'.format(self.key)


class ItemByValueLens(GetterSetterLens):
    '''A lens that focuses a single item (key-value pair) in a
    dictionary by its value. Set an item to `None` to remove it from the
    dictionary. This lens assumes that there will only be a single key
    with that particular value. The results of this lens are not defined
    when that assumption is broken.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().item_by_value_(10)
        Lens(None, ItemByValueLens(10))
        >>> lens(data).item_by_value_(10).get()
        (1, 10)
        >>> lens(data).item_by_value_(10).set((3, 10))
        OrderedDict([(2, 20), (3, 10)])
        >>> lens(data).item_by_value_(10).set(None)
        OrderedDict([(2, 20)])
    '''

    def __init__(self, value):
        self.value = value

    def getter(self, state):
        for dkey, dvalue in state.items():
            if dvalue == self.value:
                return dkey, dvalue

    def setter(self, state, focus):
        data = state.copy()
        for key, val in state.items():
            if val == self.value:
                del data[key]
        if focus is not None:
            data[focus[0]] = focus[1]
        return data

    def __repr__(self):
        return 'ItemByValueLens({!r})'.format(self.value)


class ItemsLens(BaseLens):
    '''A traversal focusing key-value tuples that are the items of a
    dictionary. Analogous to `dict.items`.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().items_()
        Lens(None, ItemsLens())
        >>> lens(data).items_().get_all()
        ((1, 10), (2, 20))
        >>> lens(data).items_()[1].modify(lambda n: n + 1)
        OrderedDict([(1, 11), (2, 21)])
    '''

    def func(self, f, state):
        items = list(state.items())
        if items == []:
            return f.get_pure(state)

        def dict_builder(args):
            data = state.copy()
            data.clear()
            data.update(a for a in args if a is not None)
            return data

        return fmap(multiap(collect_args(len(items)), *map(f, items)),
                    dict_builder)

    def __repr__(self):
        return 'ItemsLens()'


class JsonLens(GetterSetterLens):
    '''A lens that focuses a string containing json data as its parsed
    equivalent. Analogous to `json.loads`.

        >>> from lenses import lens
        >>> data = '[{"points": [4, 7]}]'
        >>> lens().json_()
        Lens(None, JsonLens())
        >>> lens(data).json_()[0]['points'][1].get()
        7
        >>> lens(data).json_()[0]['points'][0].set(8)
        '[{"points": [8, 7]}]'
    '''

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
    `dict.keys`.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().keys_()
        Lens(None, KeysLens())
        >>> lens(data).keys_().get_all()
        (1, 2)
        >>> lens(data).keys_().modify(lambda n: n + 1)
        OrderedDict([(2, 10), (3, 20)])
    '''

    def __init__(self):
        self.lenses = [ItemsLens(), GetitemLens(0)]

    def __repr__(self):
        return 'KeysLens()'


class NormalisingLens(GetterSetterLens):
    '''A lens that applies a function as it sets a new focus without
    regard to the old state. It will get foci without transformation.
    This lens allows you to post-process values before you set them
    them, but still get value as they exist in the state. Useful for
    type conversions or normalising data. This lens is similar to the
    SetterLens, but the setter function has a more convenient signature,
    applicable to most built-in functions/constructors.

        >>> from lenses import lens
        >>> lens().norm_(int)
        Lens(None, NormalisingLens(<class 'int'>))
        >>> lens([1, 2, 3])[0].norm_(int).get()
        1
        >>> lens([1, 2, 3])[0].norm_(int).set('4')
        [4, 2, 3]
        >>> lens([1, 2, 3])[0].norm_(int).modify(lambda a: a - 4.5)
        [-3, 2, 3]
    '''

    def __init__(self, setter):
        self.raw_setter = setter

    def getter(self, state):
        return state

    def setter(self, state, focus):
        return self.raw_setter(focus)

    def __repr__(self):
        return 'NormalisingLens({!r})'.format(self.raw_setter)


class SetterLens(GetterSetterLens):
    '''A lens that applies a function as it sets a new focus, but will
    get foci without transformation. Note that modify does both a get
    and a set.

        >>> from lenses import lens
        >>> def setter(state, focus):
        ...     return type(state)(focus)
        ...
        >>> lens().setter_(setter)
        Lens(None, SetterLens(<function setter at ...>))
        >>> lens([1, 2, 3])[0].setter_(setter).get()
        1
        >>> lens([1, 2, 3])[0].setter_(setter).set('4')
        [4, 2, 3]
        >>> lens([1, 2, 3])[0].setter_(setter).modify(lambda a: a - 4.5)
        [-3, 2, 3]
    '''

    def __init__(self, setter):
        self.setter = setter

    def getter(self, state):
        return state

    def __repr__(self):
        return 'SetterLens({!r})'.format(self.setter)


class TraverseLens(BaseLens):
    '''A traversal that focuses everything in a data structure depending
    on how that data structure defines `lenses.typeclass.traverse`. Usually
    somewhat similar to iterating over it.

        >>> from lenses import lens
        >>> lens().traverse_()
        Lens(None, TraverseLens())
        >>> lens([1, 2, 3]).traverse_().get_all()
        (1, 2, 3)
        >>> lens([1, 2, 3]).traverse_().modify(lambda n: n + 1)
        [2, 3, 4]
    '''

    def func(self, f, state):
        return traverse(state, f)

    def __repr__(self):
        return 'TraverseLens()'


class TrivialLens(BaseLens):
    '''A trivial lens that focuses the whole state. It doesn't do
    manipulate the state. Mostly used as a "null" lens. Analogous to
    `lambda a: a`.

        >>> from lenses import lens
        >>> lens()
        Lens(None, TrivialLens())
        >>> lens(True).get()
        True
        >>> lens(True).set(False)
        False
    '''

    def func(self, f, state):
        return fmap(f(state), lambda newvalue: newvalue)

    def __repr__(self):
        return 'TrivialLens()'


class TupleLens(GetterSetterLens):
    '''A lens that combines the focuses of other lenses into a
    single tuple.

        >>> from lenses import lens
        >>> lens().tuple_()
        Lens(None, TupleLens())
        >>> tl = lens().tuple_(lens()[0].lens, lens()[2].lens)
        >>> tl
        Lens(None, TupleLens(GetitemLens(0), GetitemLens(2)))
        >>> tl.bind([1, 2, 3, 4]).get()
        (1, 3)
        >>> tl.bind([1, 2, 3, 4]).set((5, 6))
        [5, 2, 6, 4]
    '''

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
    `dict.values`.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().values_()
        Lens(None, ValuesLens())
        >>> lens(data).values_().get_all()
        (10, 20)
        >>> lens(data).values_().modify(lambda n: n + 1)
        OrderedDict([(1, 11), (2, 21)])
    '''

    def __init__(self):
        self.lenses = [ItemsLens(), GetitemLens(1)]

    def __repr__(self):
        return 'ValuesLens()'


class ZoomAttrLens(BaseLens):
    '''A lens that looks up an attribute on its target and follows it as
    if were a bound `Lens` object. Ignores the state, if any, of the
    lens that is being looked up.

        >>> from lenses import lens
        >>> class ClassWithLens:
        ...     def __init__(self, items):
        ...         self._private_items = items
        ...     def __repr__(self):
        ...         return 'ClassWithLens({!r})'.format(self._private_items)
        ...     first = lens()._private_items[0]
        ...
        >>> data = (ClassWithLens([1, 2, 3]), 4)
        >>> lens().first_l
        Lens(None, ZoomAttrLens('first'))
        >>> lens().zoomattr_('first')
        Lens(None, ZoomAttrLens('first'))
        >>> lens(data)[0].first_l.get()
        1
        >>> lens(data)[0].first_l.set(5)
        (ClassWithLens([5, 2, 3]), 4)
    '''

    def __init__(self, name):
        self.name = name

    def func(self, f, state):
        l = getattr(state, self.name)
        return l.lens.func(f, state)

    def __repr__(self):
        return 'ZoomAttrLens({!r})'.format(self.name)


class ZoomLens(BaseLens):
    '''Follows its state as it were a bound `Lens` object.

        >>> from lenses import lens
        >>> data = [lens([1, 2])[1], 4]
        >>> lens().zoom_()
        Lens(None, ZoomLens())
        >>> lens(data)[0].zoom_().get()
        2
        >>> lens(data)[0].zoom_().set(3)
        [[1, 3], 4]
    '''

    def func(self, f, state):
        return state.lens.func(f, state.state)

    def __repr__(self):
        return 'ZoomLens()'
