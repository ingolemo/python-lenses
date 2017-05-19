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

        >>> KeysTraversal()
        KeysTraversal()
        >>> from collections import OrderedDict
        >>> state = OrderedDict([(1, 10), (2, 20)])
        >>> KeysTraversal().to_list_of(state)
        [1, 2]
        >>> KeysTraversal().over(state, lambda n: n + 1)
        OrderedDict([(2, 10), (3, 20)])
    '''

    def __init__(self):
        self.lenses = [ItemsTraversal(), GetitemLens(0)]

    def __repr__(self):
        return 'KeysTraversal()'


class ValuesTraversal(ComposedLens):
    '''A traversal focusing the values of a dictionary. Analogous to
    `dict.values`.

        >>> ValuesTraversal()
        ValuesTraversal()
        >>> from collections import OrderedDict
        >>> state = OrderedDict([(1, 10), (2, 20)])
        >>> ValuesTraversal().to_list_of(state)
        [10, 20]
        >>> ValuesTraversal().over(state, lambda n: n + 1)
        OrderedDict([(1, 11), (2, 21)])
    '''

    def __init__(self):
        self.lenses = [ItemsTraversal(), GetitemLens(1)]

    def __repr__(self):
        return 'ValuesTraversal()'
