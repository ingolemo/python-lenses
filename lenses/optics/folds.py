from ..const import Const
from .base import Fold, collect_args, multiap


class IterableFold(Fold):
    """A fold that can get values from any iterable object in python by
    iterating over it. Like any fold, you cannot set values.

        >>> IterableFold()
        IterableFold()
        >>> data = {2, 1, 3}
        >>> IterableFold().to_list_of(data) == list(data)
        True
        >>> def numbers():
        ...     yield 1
        ...     yield 2
        ...     yield 3
        ...
        >>> IterableFold().to_list_of(numbers())
        [1, 2, 3]
        >>> IterableFold().to_list_of([])
        []

    If you want to be able to set values as you iterate then look into
    the EachTraversal.
    """

    def __init__(self):
        pass

    def folder(self, state):
        return iter(state)

    def __repr__(self):
        return "IterableFold()"
