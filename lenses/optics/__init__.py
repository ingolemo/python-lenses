from .. import hooks
from .. import typeclass

from .base import *
from .isomorphisms import *
from .traversals import *


class GetterSetterLens(Lens):
    '''Turns a pair of getter and setter functions into a van
    Laarhoven lens. A getter function is one that takes a state and
    returns a value derived from that state. A setter function takes
    an old state and a new value and uses them to construct a new state.

        >>> from lenses import lens
        >>> def getter(state):
        ...     'Get the average of a list'
        ...     return sum(state) // len(state)
        ...
        >>> def setter(old_state, value):
        ...     'Set the average of a list by changing the final value'
        ...     target_sum = value * len(old_state)
        ...     prefix = old_state[:-1]
        ...     return prefix + [target_sum - sum(prefix)]
        ...
        >>> average_lens = lens().getter_setter_(getter, setter)
        >>> average_lens
        Lens(None, GetterSetterLens(<function getter...>, <function setter...>))
        >>> average_lens.bind([1, 2, 4, 5]).get()
        3
        >>> average_lens.bind([1, 2, 3]).set(4)
        [1, 2, 9]
        >>> average_lens.bind([1, 2, 3]) - 1
        [1, 2, 0]

    Though GetterSetterLens is more powerful because it can inspect the
    old state to produce a new one, Isomorphism is more suited to
    building custom lenses due to the greater availability of functions
    that already fit its API. Only use a GetterSetterLens if you need the
    extra power it affords.
    '''

    def __init__(self, getter, setter):
        self.getter = getter
        self.setter = setter

    def func(self, f, state):
        old_value = self.getter(state)
        fa = f(old_value)
        return typeclass.fmap(fa, lambda a: self.setter(state, a))

    def __repr__(self):
        return 'GetterSetterLens({!r}, {!r})'.format(self.getter, self.setter)


class GetattrLens(GetterSetterLens):
    '''A lens that focuses an attribute of an object. Analogous to
    `getattr`.

        >>> from lenses import lens
        >>> from collections import namedtuple
        >>> Pair = namedtuple('Pair', 'left right')
        >>> lens().getattr_('left')
        Lens(None, GetattrLens('left'))
        >>> lens(Pair(1, 2)).getattr_('left').get()
        1
        >>> lens(Pair(1, 2)).getattr_('right').set(3)
        Pair(left=1, right=3)
    '''

    def __init__(self, name):
        self.name = name

    def getter(self, state):
        return getattr(state, self.name)

    def setter(self, state, focus):
        return hooks.setattr_immutable(state, self.name, focus)

    def __repr__(self):
        return 'GetattrLens({!r})'.format(self.name)


class GetZoomAttrLens(Lens):
    '''A lens that focuses an attribute of an object, though if that attribute
    happens to be a lens it will zoom the lens.

        >>> from lenses import lens
        >>> from collections import namedtuple
        >>> Triple = namedtuple('Triple', 'left middle right')
        >>> state = Triple(1, 10, lens().middle)
        >>> lens().left
        Lens(None, GetZoomAttrLens('left'))
        >>> lens(state).left.get()
        1
        >>> lens(state).left.set(3)
        Triple(left=3, middle=10, right=Lens(None, GetZoomAttrLens('middle')))
        >>> lens(state).right.get()
        10
        >>> lens(state).right.set(13)
        Triple(left=1, middle=13, right=Lens(None, GetZoomAttrLens('middle')))
    '''

    def __init__(self, name):
        self.name = name
        self._getattr_cache = GetattrLens(name)

    def func(self, f, state):
        attr = getattr(state, self.name)
        try:
            sublens = attr._underlying_lens()
        except AttributeError:
            sublens = self._getattr_cache
        return sublens.func(f, state)

    def __repr__(self):
        return 'GetZoomAttrLens({!r})'.format(self.name)


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
        return hooks.setitem_immutable(state, self.key, focus)

    def __repr__(self):
        return 'GetitemLens({!r})'.format(self.key)


class GetitemOrElseLens(GetitemLens):
    '''A lens that focuses an item inside a container by calling its `get`
    method, allowing you to specify a default value for missing keys.
    Analogous to `dict.get`.

        >>> from lenses import lens
        >>> lens().get_('foo')
        Lens(None, GetitemOrElseLens('foo'))
        >>> lens({'foo': 'bar'}).get_('baz').get()
        >>> lens({'foo': 'bar'}).get_('baz', []).get()
        []
        >>> from collections import OrderedDict
        >>> lens(OrderedDict({'foo': 'bar'})).get_('baz').set('qux')
        OrderedDict([('foo', 'bar'), ('baz', 'qux')])
    '''

    def __init__(self, key, default=None):
        self.key = key
        self.default = default

    def getter(self, state):
        return state.get(self.key, self.default)

    def __repr__(self):
        return 'GetitemOrElseLens({!r})'.format(self.key)


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
        >>> lens(data).item_(3).get() is None
        True
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
    with that particular value. If you violate that assumption then
    you're on your own.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().item_by_value_(10)
        Lens(None, ItemByValueLens(10))
        >>> lens(data).item_by_value_(10).get()
        (1, 10)
        >>> lens(data).item_by_value_(30).get() is None
        True
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


class KeysLens(ComposedLens):
    '''A traversal focusing the keys of a dictionary. Analogous to
    `dict.keys`.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().keys_()
        Lens(None, KeysLens())
        >>> lens(data).keys_().get_all()
        [1, 2]
        >>> lens(data).keys_().modify(lambda n: n + 1)
        OrderedDict([(2, 10), (3, 20)])
    '''

    def __init__(self):
        self.lenses = [ItemsLens(), GetitemLens(0)]

    def __repr__(self):
        return 'KeysLens()'


class TupleLens(GetterSetterLens):
    '''A lens that combines the focuses of other lenses into a single
    tuple. The sublenses must be optics of kind Lens; this means no
    Traversals.

        >>> from lenses import lens
        >>> lens().tuple_()
        Lens(None, TupleLens())
        >>> tl = lens().tuple_(lens()[0], lens()[2])
        >>> tl
        Lens(None, TupleLens(GetitemLens(0), GetitemLens(2)))
        >>> tl.bind([1, 2, 3, 4]).get()
        (1, 3)
        >>> tl.bind([1, 2, 3, 4]).set((5, 6))
        [5, 2, 6, 4]

    This lens is particularly useful when immediately followed by
    an EachLens, allowing you to traverse data even when it comes
    from disparate locations within the state.

        >>> state = ([1, 2, 3], 4, [5, 6])
        >>> tl.bind(state).each_().each_().get_all()
        [1, 2, 3, 5, 6]
        >>> tl.bind(state).each_().each_() + 10
        ([11, 12, 13], 4, [15, 16])
    '''

    def __init__(self, *lenses):
        self.lenses = [l._underlying_lens() for l in lenses]
        for lens in self.lenses:
            if not lens._is_kind(Lens):
                raise TypeError('TupleLens only works with lenses')

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
        [10, 20]
        >>> lens(data).values_().modify(lambda n: n + 1)
        OrderedDict([(1, 11), (2, 21)])
    '''

    def __init__(self):
        self.lenses = [ItemsLens(), GetitemLens(1)]

    def __repr__(self):
        return 'ValuesLens()'
