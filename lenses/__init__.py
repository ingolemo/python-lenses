from .boundlens import BoundLens
from .lens import Lens, make_lens
from .setter import setter
from .typeclass import fmap


def lens(obj):
    'Returns a lens bound to an object. A BoundLens.'
    return BoundLens(obj, Lens.trivial())
