from typing import Any

from .. import hooks
from .. import typeclass

from .base import Fold, Getter, Lens, Traversal


class ContainsLens(Lens):
    """A lens that takes an item and focuses a bool based on whether
    the state contains that item. It's most useful when used with
    sets, but it can be used with other collections like lists and
    dictionaries. Analogous to the ``in`` operator.

        >>> ContainsLens(1)
        ContainsLens(1)
        >>> ContainsLens(1).view([2, 3])
        False
        >>> ContainsLens(1).view([1, 2, 3])
        True
        >>> ContainsLens(1).set([1, 2, 3], False)
        [2, 3]
        >>> ContainsLens(1).set([2, 3], True)
        [2, 3, 1]
        >>> ContainsLens(1).set([1, 2, 3], True)
        [1, 2, 3]

    In order to use this lens on custom data-types you must implement
    ``lenses.hooks.contains_add`` and ``lens.hooks.contains_remove``.
    """

    def __init__(self, item):
        self.item = item

    def getter(self, state):
        return self.item in state

    def setter(self, state, focus):
        contains = self.item in state
        if focus and not contains:
            return hooks.contains_add(state, self.item)
        elif contains and not focus:
            return hooks.contains_remove(state, self.item)
        else:
            return state

    def __repr__(self):
        return "ContainsLens({!r})".format(self.item)


class GetattrLens(Lens):
    """A lens that focuses an attribute of an object. Analogous to
    `getattr`.

        >>> GetattrLens('left')
        GetattrLens('left')
        >>> from collections import namedtuple
        >>> Pair = namedtuple('Pair', 'left right')
        >>> GetattrLens('left').view(Pair(1, 2))
        1
        >>> GetattrLens('right').set(Pair(1, 2), 3)
        Pair(left=1, right=3)
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def getter(self, state):
        return getattr(state, self.name)

    def setter(self, state, focus):
        return hooks.setattr(state, self.name, focus)

    def __repr__(self):
        return "GetattrLens({!r})".format(self.name)


class GetitemLens(Lens):
    """A lens that focuses an item inside a container. Analogous to
    `operator.itemgetter`.

        >>> GetitemLens('foo')
        GetitemLens('foo')
        >>> GetitemLens('foo').view({'foo': 1})
        1
        >>> GetitemLens('foo').set({'foo': 1}, 2)
        {'foo': 2}
    """

    def __init__(self, key: Any) -> None:
        self.key = key

    def getter(self, state):
        return state[self.key]

    def setter(self, state, focus):
        return hooks.setitem(state, self.key, focus)

    def __repr__(self):
        return "GetitemLens({!r})".format(self.key)


class GetitemOrElseLens(GetitemLens):
    """A lens that focuses an item inside a container by calling its `get`
    method, allowing you to specify a default value for missing keys.
    Analogous to `dict.get`.

        >>> GetitemOrElseLens('foo', 0)
        GetitemOrElseLens('foo', default=0)
        >>> state = {'foo': 1}
        >>> GetitemOrElseLens('foo', 0).view(state)
        1
        >>> GetitemOrElseLens('baz', 0).view(state)
        0
        >>> GetitemOrElseLens('foo', 0).set(state, 2)
        {'foo': 2}
        >>> GetitemOrElseLens('baz', 0).over({}, lambda a: a + 10)
        {'baz': 10}
    """

    def __init__(self, key: Any, default: Any = None) -> None:
        self.key = key
        self.default = default

    def getter(self, state):
        return state.get(self.key, self.default)

    def __repr__(self):
        message = "GetitemOrElseLens({!r}, default={!r})"
        return message.format(self.key, self.default)


class ItemLens(Lens):
    """A lens that focuses a single item (key-value pair) in a
    dictionary by its key. Set an item to `None` to remove it from the
    dictionary.

        >>> ItemLens(1)
        ItemLens(1)
        >>> from collections import OrderedDict
        >>> state = OrderedDict([(1, 10), (2, 20)])
        >>> ItemLens(1).view(state)
        (1, 10)
        >>> ItemLens(3).view(state) is None
        True
        >>> ItemLens(1).set(state, (1, 11))
        OrderedDict([(1, 11), (2, 20)])
        >>> ItemLens(1).set(state, None)
        OrderedDict([(2, 20)])
    """

    def __init__(self, key: Any) -> None:
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
        return "ItemLens({!r})".format(self.key)


class ItemByValueLens(Lens):
    """A lens that focuses a single item (key-value pair) in a
    dictionary by its value. Set an item to `None` to remove it from the
    dictionary. This lens assumes that there will only be a single key
    with that particular value. If you violate that assumption then
    you're on your own.

        >>> ItemByValueLens(10)
        ItemByValueLens(10)
        >>> from collections import OrderedDict
        >>> state = OrderedDict([(1, 10), (2, 20)])
        >>> ItemByValueLens(10).view(state)
        (1, 10)
        >>> ItemByValueLens(30).view(state) is None
        True
        >>> ItemByValueLens(10).set(state, (3, 10))
        OrderedDict([(2, 20), (3, 10)])
        >>> ItemByValueLens(10).set(state, None)
        OrderedDict([(2, 20)])
    """

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
        return "ItemByValueLens({!r})".format(self.value)


class PartsLens(Lens):
    """An optic that takes the foci of a fold and packs them up together
    as a single list. The kind of this foci depends on what optic you
    give it.
    """

    def __init__(self, optic):
        self.optic = optic

    def getter(self, state):
        return self.optic.to_list_of(state)

    def setter(self, old_state, value):
        return self.optic.iterate(old_state, value)

    def __repr__(self) -> str:
        return "PartsLens({!r})".format(self.optic)

    def kind(self):
        if self.optic.kind() == base.Traversal:
            return base.Lens
        elif self.optic.kind() == base.Fold:
            return base.Getter


class TupleLens(Lens):
    """A lens that combines the focuses of other lenses into a single
    tuple. The sublenses must be optics of kind Lens; this means no
    Traversals.

        >>> tl = TupleLens(GetitemLens(0), GetitemLens(2))
        >>> tl
        TupleLens(GetitemLens(0), GetitemLens(2))
        >>> tl.view([1, 2, 3, 4])
        (1, 3)
        >>> tl.set([1, 2, 3, 4], (5, 6))
        [5, 2, 6, 4]

    This lens is particularly useful when immediately followed by
    an EachLens, allowing you to traverse data even when it comes
    from disparate locations within the state.

        >>> import lenses
        >>> each = lenses.optics.EachTraversal()
        >>> tee = tl & each & each
        >>> state = ([1, 2, 3], 4, [5, 6])
        >>> tee.to_list_of(state)
        [1, 2, 3, 5, 6]
    """

    def __init__(self, *lenses):
        self.lenses = lenses
        for lens in self.lenses:
            if not lens._is_kind(Lens):
                raise TypeError("TupleLens only works with lenses")

    def getter(self, state):
        return tuple(lens.view(state) for lens in self.lenses)

    def setter(self, state, focus):
        for lens, new_value in zip(self.lenses, focus):
            state = lens.set(state, new_value)
        return state

    def __repr__(self):
        args = ", ".join(repr(lens) for lens in self.lenses)
        return "TupleLens({})".format(args)
