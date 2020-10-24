from .. import typeclass
from ..maybe import Just, Nothing

from .base import Prism


class FilteringPrism(Prism):
    """A prism that only focuses a value if the predicate returns `True`
    when called with that value as an argument. Best used when composed
    after a traversal. It only prevents the traversal from visiting foci,
    it does not filter out values the way that python's regular `filter`
    function does.

        >>> FilteringPrism(all)
        FilteringPrism(<built-in function all>)
        >>> import lenses
        >>> each = lenses.optics.EachTraversal()
        >>> state = [[1, 2], [0], ['a'], ['', 'b']]
        >>> (each & FilteringPrism(all)).to_list_of(state)
        [[1, 2], ['a']]
        >>> (each & FilteringPrism(all)).set(state, 2)
        [2, [0], 2, ['', 'b']]

    The filtering is done to foci before the lens' manipulation is
    applied. This means that the resulting foci can still violate the
    predicate if the manipulating function doesn't respect it:

        >>> (each & FilteringPrism(bool)).set(['', 2, ''], None)
        ['', None, '']
    """

    def __init__(self, predicate):
        self.predicate = predicate

    def unpack(self, state):
        if self.predicate(state):
            return Just(state)
        return Nothing()

    def pack(self, focus):
        return focus

    def __repr__(self):
        return "FilteringPrism({!r})".format(self.predicate)


class InstancePrism(FilteringPrism):
    """A prism that focuses a value only when that value is an instance
    of `type_`.

        >>> InstancePrism(int)
        InstancePrism(...)
        >>> InstancePrism(int).to_list_of(1)
        [1]
        >>> InstancePrism(float).to_list_of(1)
        []
        >>> InstancePrism(int).set(1, 2)
        2
        >>> InstancePrism(float).set(1, 2)
        1
    """

    def __init__(self, type_):
        self.type = type_

    def predicate(self, value):
        return isinstance(value, self.type)

    def __repr__(self):
        return "InstancePrism({!r})".format(self.type)


class JustPrism(Prism):
    """A prism that focuses the value inside a `lenses.maybe.Just`
    object.

        >>> from lenses.maybe import Just, Nothing
        >>> JustPrism()
        JustPrism()
        >>> JustPrism().to_list_of(Just(1))
        [1]
        >>> JustPrism().to_list_of(Nothing())
        []
        >>> JustPrism().set(Just(1), 2)
        Just(2)
        >>> JustPrism().set(Nothing(), 2)
        Nothing()
    """

    def __init__(self):
        pass

    def unpack(self, a):
        return a

    def pack(self, a):
        return Just(a)

    def __repr__(self):
        return "JustPrism()"
