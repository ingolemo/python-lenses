from .lens import Lens
from .simplelens import SimpleLens
from .methodlens import MethodLens


def lens(obj=None, lens=None):
    return Lens(obj, lens)
