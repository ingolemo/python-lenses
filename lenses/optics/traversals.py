import copy

from .. import hooks
from .. import typeclass

from .base import Traversal, collect_args, multiap


class EachTraversal(Traversal):
    """A traversal that iterates over its state, focusing everything it
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
    """

    def __init__(self):
        pass

    def folder(self, state):
        return hooks.to_iter(state)

    def builder(self, state, values):
        return hooks.from_iter(state, values)

    def __repr__(self):
        return "EachTraversal()"


class GetZoomAttrTraversal(Traversal):
    """A traversal that focuses an attribute of an object, though if
    that attribute happens to be a lens it will zoom the lens. This
    is used internally to make lenses that are attributes of objects
    transparent. If you already know whether you are focusing a lens or
    a non-lens you should be explicit and use a ZoomAttrTraversal or a
    GetAttrLens respectively.
    """

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
        return "GetZoomAttrTraversal({!r})".format(self.name)


class ItemsTraversal(Traversal):
    """A traversal focusing key-value tuples that are the items of a
    dictionary. Analogous to `dict.items`.

        >>> from collections import OrderedDict
        >>> state = OrderedDict([(1, 10), (2, 20)])
        >>> ItemsTraversal()
        ItemsTraversal()
        >>> ItemsTraversal().to_list_of(state)
        [(1, 10), (2, 20)]
        >>> ItemsTraversal().over(state, lambda n: (n[0], n[1] + 1))
        OrderedDict([(1, 11), (2, 21)])
    """

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
        return "ItemsTraversal()"


class RecurTraversal(Traversal):
    """A traversal that recurses through an object focusing everything it
    can find of a particular type. This traversal will probe arbitrarily
    deep into the contents of the state looking for sub-objects. It
    uses some naughty tricks to do this including looking at an object's
    `__dict__` attribute.

    It is somewhat analogous to haskell's uniplate optic.

        >>> RecurTraversal(int)
        RecurTraversal(<... 'int'>)
        >>> data = [[1, 2, 100.0], [3, 'hello', [{}, 4], 5]]
        >>> RecurTraversal(int).to_list_of(data)
        [1, 2, 3, 4, 5]
        >>> class Container(object):
        ...     def __init__(self, contents):
        ...         self.contents = contents
        ...     def __repr__(self):
        ...         return 'Container({!r})'.format(self.contents)
        >>> data = [Container(1), 2, Container(Container(3)), [4, 5]]
        >>> RecurTraversal(int).over(data, lambda n: n+1)
        [Container(2), 3, Container(Container(4)), [5, 6]]
        >>> RecurTraversal(Container).to_list_of(data)
        [Container(1), Container(Container(3))]

    Be careful with this; it can focus things you might not expect.
    """

    def __init__(self, cls):
        self.cls = cls
        self._builder_cache = {}

    def folder(self, state):
        if isinstance(state, self.cls):
            yield state
        elif self.can_iter(state):
            for substate in hooks.to_iter(state):
                for focus in self.folder(substate):
                    yield focus
        elif hasattr(state, "__dict__"):
            for attr in sorted(state.__dict__):
                substate = getattr(state, attr)
                for focus in self.folder(substate):
                    yield focus

    def builder(self, state, values):
        assert self._builder_cache == {}
        result = self.build_object(state, values)
        self._builder_cache = {}
        return result

    def build_object(self, state, values):
        if not self.can_hash(state):
            return self.build_object_no_cache(state, values)

        guard = object()
        cache = self._builder_cache.get(state, guard)
        if cache is not guard:
            return cache
        result = self.build_object_no_cache(state, values)
        self._builder_cache[state] = result
        return result

    def build_object_no_cache(self, state, values):
        if isinstance(state, self.cls):
            assert len(values) == 1
            return values[0]
        elif self.can_iter(state):
            return self.build_from_iter(state, values)
        elif hasattr(state, "__dict__"):
            return self.build_dunder_dict(state, values)
        else:
            return state

    def build_from_iter(self, state, values):
        new_substates = []
        for substate in hooks.to_iter(state):
            count = len(list(self.folder(substate)))
            new_substate = substate
            if count:
                subvalues, values = values[:count], values[count:]
                new_substate = self.build_object(substate, subvalues)
            new_substates.append(new_substate)

        assert len(values) == 0
        new_state = hooks.from_iter(state, new_substates)
        return new_state

    def build_dunder_dict(self, state, values):
        new_state = state
        for attr in sorted(state.__dict__):
            substate = getattr(state, attr)
            count = len(list(self.folder(substate)))
            if count:
                subvalues, values = values[:count], values[count:]
                new_substate = self.build_object(substate, subvalues)
                new_state = hooks.setattr(new_state, attr, new_substate)
        assert len(values) == 0
        return new_state

    @staticmethod
    def can_iter(state):
        # characters appear iterable because they are just strings,
        # but if we actually try to iterate over them then we enter
        # infinite recursion
        if isinstance(state, str) and len(state) == 1:
            return False

        from_types = set(hooks.from_iter.registry.keys()) - {object}
        can_from = any(isinstance(state, type_) for type_ in from_types)
        return can_from

    @staticmethod
    def can_hash(state):
        try:
            hash(state)
        except TypeError:
            return False
        else:
            return True

    def __repr__(self):
        return "RecurTraversal({!r})".format(self.cls)


class ZoomAttrTraversal(Traversal):
    """A lens that looks up an attribute on its target and follows it as
    if were a bound `Lens` object. Ignores the state, if any, of the
    lens that is being looked up.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def func(self, f, state):
        optic = getattr(state, self.name)._optic
        return optic.func(f, state)

    def __repr__(self):
        return "ZoomAttrTraversal({!r})".format(self.name)


class ZoomTraversal(Traversal):
    """Follows its state as if it were a bound `Lens` object.

    >>> from lenses import bind
    >>> ZoomTraversal()
    ZoomTraversal()
    >>> state = bind([1, 2])[1]
    >>> ZoomTraversal().view(state)
    2
    >>> ZoomTraversal().set(state, 3)
    [1, 3]
    """

    def __init__(self):
        pass

    def func(self, f, state):
        return state._optic.func(f, state._state)

    def __repr__(self):
        return "ZoomTraversal()"
