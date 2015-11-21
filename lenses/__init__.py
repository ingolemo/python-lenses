from .boundlens import BoundLens
from .lens import Lens, setter


def lens(obj=None):
    '''returns a lens-like object.

    called with no argument it returns an instance of Lens that does nothing.
    when called with an argument it returns an empty BoundLens.
    '''
    if obj is None:
        return Lens(
            lambda item: item,
            lambda item, newvalue: newvalue
        )
    return BoundLens(obj, lens())
