from .boundlens import BoundLens
from .lens import Lens, setter, make_lens
from .functor import fmap


def lens(obj):
    'Returns a lens bound to an object. A BoundLens.'
    trivial_lens = Lens(lambda fn, state: fmap(
        fn(state),
        lambda newvalue: newvalue
    ))
    return BoundLens(obj, trivial_lens)
