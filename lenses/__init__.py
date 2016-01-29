from .userlens import UserLens
from .lens import Lens
from .methodlens import MethodLens


def lens(obj=None, lens=None):
    return UserLens(obj, lens)
