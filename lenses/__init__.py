from .lens import Lens
from .methodlens import MethodLens


def lens(obj=None, lens=None):
    return Lens(obj, lens)
