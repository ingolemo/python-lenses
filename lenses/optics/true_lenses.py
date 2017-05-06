from typing import Any

from .. import hooks
from .. import typeclass

from .base import Lens


class GetattrLens(Lens):
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
        # type: (str) -> None
        self.name = name

    def getter(self, state):
        return getattr(state, self.name)

    def setter(self, state, focus):
        return hooks.setattr_immutable(state, self.name, focus)

    def __repr__(self):
        return 'GetattrLens({!r})'.format(self.name)


class GetitemLens(Lens):
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
        # type: (Any) -> None
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
        # type: (Any, Any) -> None
        self.key = key
        self.default = default

    def getter(self, state):
        return state.get(self.key, self.default)

    def __repr__(self):
        return 'GetitemOrElseLens({!r})'.format(self.key)


class ItemLens(Lens):
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
        # type: (Any) -> None
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


class ItemByValueLens(Lens):
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


class TupleLens(Lens):
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
        return tuple(lens.view(state) for lens in self.lenses)

    def setter(self, state, focus):
        for lens, new_value in zip(self.lenses, focus):
            state = lens.set(state, new_value)
        return state

    def __repr__(self):
        args = ', '.join(repr(lens) for lens in self.lenses)
        return 'TupleLens({})'.format(args)
