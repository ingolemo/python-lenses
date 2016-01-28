from .userlens import UserLens
from .lens import Lens


def lens(obj=None, lens=None):
    return UserLens(obj, lens)
