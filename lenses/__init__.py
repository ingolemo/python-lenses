from .boundlens import BoundLens
from .lens import Lens, setter, make_lens
from .functor import fmap


def lens(obj=None):
    'Returns a lens bound to an object. A BoundLens.'
    if obj is None:
        trivial_lens = Lens(lambda fn, state: fmap(
            fn(state),
            lambda newvalue: newvalue
        ))
        return trivial_lens
    return BoundLens(obj, lens())
