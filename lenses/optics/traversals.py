from .. import hooks
from .. import typeclass

from .base import Traversal, collect_args, multiap


class BothTraversal(Traversal):
    '''A traversal that focuses both items [0] and [1].

        >>> BothTraversal()
        BothTraversal()
        >>> BothTraversal().to_list_of([1, 2, 3])
        [1, 2]
        >>> BothTraversal().set([1, 2, 3], 4)
        [4, 4, 3]
    '''
    def __init__(self):
        pass

    def folder(self, state):
        yield state[0]
        yield state[1]

    def builder(self, state, values):
        state = hooks.setitem_immutable(state, 0, values[0])
        state = hooks.setitem_immutable(state, 1, values[1])
        return state

    def __repr__(self):
        return 'BothTraversal()'


class EachTraversal(Traversal):
    '''A traversal that iterates over its state, focusing everything it
    iterates over. It uses `lenses.hooks.fromiter` to reform the state
    afterwards so it should work with any iterable that function
    supports. Analogous to `iter`.

        >>> from lenses import lens
        >>> state = [1, 2, 3]
        >>> EachTraversal()
        EachTraversal()
        >>> EachTraversal().to_list_of(state)
        [1, 2, 3]
        >>> EachTraversal().over(state, lambda n: n + 1)
        [2, 3, 4]

    For technical reasons, this lens iterates over dictionaries by their
    items and not just their keys.

        >>> state = {'one': 1}
        >>> EachTraversal().to_list_of(state)
        [('one', 1)]
    '''

    def __init__(self):
        pass

    def folder(self, state):
        return hooks.to_iter(state)

    def builder(self, state, values):
        return hooks.from_iter(state, values)

    def __repr__(self):
        return 'EachTraversal()'


class GetZoomAttrTraversal(Traversal):
    '''A traversal that focuses an attribute of an object, though if
    that attribute happens to be a lens it will zoom the lens. This
    is used internally to make lenses that are attributes of objects
    transparent. If you already know whether you are focusing a lens or
    a non-lens you should be explicit and use a ZoomAttrTraversal or a
    GetAttrLens respectively.
    '''

    def __init__(self, name):
        from lenses.optics import GetattrLens
        self.name = name
        self._getattr_cache = GetattrLens(name)

    def func(self, f, state):
        attr = getattr(state, self.name)
        try:
            sublens = attr._optic
        except AttributeError:
            sublens = self._getattr_cache
        return sublens.func(f, state)

    def __repr__(self):
        return 'GetZoomAttrTraversal({!r})'.format(self.name)



class ItemsTraversal(Traversal):
    '''A traversal focusing key-value tuples that are the items of a
    dictionary. Analogous to `dict.items`.

        >>> from collections import OrderedDict
        >>> state = OrderedDict([(1, 10), (2, 20)])
        >>> ItemsTraversal()
        ItemsTraversal()
        >>> ItemsTraversal().to_list_of(state)
        [(1, 10), (2, 20)]
        >>> ItemsTraversal().over(state, lambda n: (n[0], n[1] + 1))
        OrderedDict([(1, 11), (2, 21)])
    '''

    def __init__(self):
        pass

    def folder(self, state):
        return state.items()

    def builder(self, state, values):
        data = state.copy()
        data.clear()
        data.update(v for v in values if v is not None)
        return data

    def __repr__(self):
        return 'ItemsTraversal()'


class ZoomAttrTraversal(Traversal):
    '''A lens that looks up an attribute on its target and follows it as
    if were a bound `Lens` object. Ignores the state, if any, of the
    lens that is being looked up.
    '''

    def __init__(self, name):
        # type: (str) -> None
        self.name = name

    def func(self, f, state):
        optic = getattr(state, self.name)._optic
        return optic.func(f, state)

    def __repr__(self):
        return 'ZoomAttrTraversal({!r})'.format(self.name)


class ZoomTraversal(Traversal):
    '''Follows its state as if it were a bound `Lens` object.

        >>> from lenses import bind
        >>> ZoomTraversal()
        ZoomTraversal()
        >>> state = bind([1, 2])[1]
        >>> ZoomTraversal().view(state)
        2
        >>> ZoomTraversal().set(state, 3)
        [1, 3]
    '''
    def __init__(self):
        pass

    def func(self, f, state):
        return state._optic.func(f, state._state)

    def __repr__(self):
        return 'ZoomTraversal()'
