from .userlens import UserLens
from .lens import (Lens,
                   both,
                   getattr_l,
                   getitem,
                   item,
                   item_by_value,
                   traverse_l,
                   trivial,
                   tuple_l, )


def lens(obj=None, lens=None):
    return UserLens(obj, lens)
