from .boundlens import BoundLens
from .lens import Lens, setter, make_lens
from .functor import fmap


def lens(obj=None):
    '''returns a lens-like object.

    called with no argument it returns an instance of Lens that does nothing.
    when called with an argument it returns an empty BoundLens.
    '''
    if obj is None:
        trivial_lens = Lens(lambda fn, state: fmap(
            fn(state),
            lambda newvalue: newvalue
        ))
        return trivial_lens
    return BoundLens(obj, lens())
