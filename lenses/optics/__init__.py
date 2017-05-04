from .base import *
from .folds import *
from .isomorphisms import *
from .prisms import *
from .setters import *
from .true_lenses import *
from .traversals import *


class KeysTraversal(ComposedLens):
    '''A traversal focusing the keys of a dictionary. Analogous to
    `dict.keys`.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().keys_()
        Lens(None, KeysTraversal())
        >>> lens(data).keys_().get_all()
        [1, 2]
        >>> lens(data).keys_().modify(lambda n: n + 1)
        OrderedDict([(2, 10), (3, 20)])
    '''

    def __init__(self):
        self.lenses = [ItemsTraversal(), GetitemLens(0)]

    def __repr__(self):
        return 'KeysTraversal()'


class ValuesTraversal(ComposedLens):
    '''A traversal focusing the values of a dictionary. Analogous to
    `dict.values`.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().values_()
        Lens(None, ValuesTraversal())
        >>> lens(data).values_().get_all()
        [10, 20]
        >>> lens(data).values_().modify(lambda n: n + 1)
        OrderedDict([(1, 11), (2, 21)])
    '''

    def __init__(self):
        self.lenses = [ItemsTraversal(), GetitemLens(1)]

    def __repr__(self):
        return 'ValuesTraversal()'
