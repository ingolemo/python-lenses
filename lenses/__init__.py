from .boundlens import BoundLens
from .lens import (Lens, make_lens, getattr_l, getitem, both, trivial)
from .setter import setter
from .typeclass import fmap


def lens(obj, lens=trivial):
    'Returns a lens bound to an object. A BoundLens.'
    return BoundLens(obj, lens)
