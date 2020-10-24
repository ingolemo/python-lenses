from ..identity import Identity

from .base import LensLike, Setter

__all__ = ["ForkedSetter"]


class ForkedSetter(Setter):
    """A setter representing the parallel composition of several sub-lenses.

    >>> import lenses
    >>> gi = lenses.optics.GetitemLens
    >>> fs = ForkedSetter(gi(0) & gi(1), gi(2))
    >>> fs
    ForkedSetter(GetitemLens(0) & GetitemLens(1), GetitemLens(2))
    >>> state = [[0, 0], 0, 0]
    >>> fs.set(state, 1)
    [[0, 1], 0, 1]
    """

    def __init__(self, *lenses):
        self.lenses = lenses

    def func(self, f, state):
        for lens in self.lenses:
            state = lens.func(f, state).unwrap()

        return Identity(state)

    def __repr__(self):
        args = ", ".join(repr(l) for l in self.lenses)
        return "ForkedSetter({})".format(args)
