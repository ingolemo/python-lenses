from .. import typeclass
from ..maybe import Just, Nothing

from .base import Prism


class FilteringPrism(Prism):
    '''A prism that only focuses a value if the predicate returns `True`
    when called with that value as an argument. Best used when composed
    after a traversal. It only prevents the traversal from visiting foci,
    it does not filter out values the way that python's regular `filter`
    function does.

        >>> from lenses import lens
        >>> lens().filter_(all)
        Lens(None, FilteringPrism(<built-in function all>))
        >>> data = [[1, 2], [0], ['a'], ['', 'b']]
        >>> lens(data).each_().filter_(all).get_all()
        [[1, 2], ['a']]
        >>> lens(data).each_().filter_(all).set(2)
        [2, [0], 2, ['', 'b']]

    The filtering is done to foci before the lens' manipulation is
    applied. This means that the resulting foci can still violate the
    predicate if the manipulating function doesn't respect it:

        >>> lens(['', 2, '']).each_().filter_(bool).set(None)
        ['', None, '']
    '''

    def __init__(self, predicate):
        self.predicate = predicate

    def unpack(self, state):
        if self.predicate(state):
            return Just(state)
        return Nothing()

    def pack(self, focus):
        return focus

    def __repr__(self):
        return 'FilteringPrism({!r})'.format(self.predicate)


class InstancePrism(FilteringPrism):
    '''A prism that focuses a value only when that value is an instance
    of `type_`.

        >>> from lenses import lens
        >>> lens().instance_(int)
        Lens(None, InstancePrism(...))
        >>> lens(1).instance_(int).get_all()
        [1]
        >>> lens(1).instance_(float).get_all()
        []
        >>> lens(1).instance_(int).set(2)
        2
        >>> lens(1).instance_(float).set(2)
        1
    '''

    def __init__(self, type_):
        self.type = type_

    def predicate(self, value):
         return isinstance(value, self.type)

    def __repr__(self):
        return 'InstancePrism({!r})'.format(self.type)


class JustPrism(Prism):
    '''A prism that focuses the value inside a `lenses.maybe.Just`
    object.

        >>> from lenses import lens
        >>> from lenses.maybe import Just, Nothing
        >>> lens().just_()
        Lens(None, JustPrism())
        >>> lens(Just(1)).just_().get_all()
        [1]
        >>> lens(Nothing()).just_().get_all()
        []
        >>> lens(Just(1)).just_().set(2)
        Just(2)
        >>> lens(Nothing()).just_().set(2)
        Nothing()
    '''

    def __init__(self):
        pass

    def unpack(self, a):
        return a

    def pack(self, a):
        return Just(a)

    def __repr__(self):
        return 'JustPrism()'
