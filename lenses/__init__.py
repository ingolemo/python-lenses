from .boundlens import BoundLens
from .lens import Lens, setter, make_lens
from .functor import fmap


def lens(obj):
    'Returns a lens bound to an object. A BoundLens.'
    return BoundLens(obj, Lens.trivial())
