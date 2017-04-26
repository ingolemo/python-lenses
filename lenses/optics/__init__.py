from .base import *
from .isomorphisms import *
from .true_lenses import *
from .traversals import *


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
