from .boundlens import BoundLens
from .lens import (Lens,
                   both,
                   getattr_l,
                   getitem,
                   item,
                   item_by_value,
                   make_lens,
                   traverse_l,
                   trivial,
                   tuple_l, )


def lens(obj, lens=None):
    'Returns a lens bound to an object. A BoundLens.'
    if lens is None:
        lens = trivial()
    return BoundLens(obj, lens)
