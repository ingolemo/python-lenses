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
from .setter import setter
from .typeclass import fmap


def lens(obj, lens=trivial):
    'Returns a lens bound to an object. A BoundLens.'
    return BoundLens(obj, lens)
