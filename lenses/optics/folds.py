from ..const import Const
from .traversals import collect_args, multiap
from .base import Fold

class IterableFold(Fold):
    '''A fold that can get values from any iterable object in python by
    iterating over it. Like any fold, you cannot set values.

        >>> from lenses import lens
        >>> lens().iter_()
        Lens(None, IterableFold())
        >>> lens({2, 1, 3}).iter_().get_all()
        [1, 2, 3]
        >>> def numbers():
        ...     yield 1
        ...     yield 2
        ...     yield 3
        >>> lens(numbers()).iter_().get_all()
        [1, 2, 3]
        >>> lens([]).iter_().get_all()
        []

    If you want to be able to set values as you iterate then look into
    the EachTraversal.
    '''

    def func(self, f, state):
        items = list(state)
        if items == []:
            return f.pure(state)

        collector = collect_args(len(items))
        applied = multiap(collector, *map(f, items))
        return applied

    def __repr__(self):
        return 'IterableFold()'
