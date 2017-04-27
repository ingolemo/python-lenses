from ..identity import Identity

from .base import Setter

class ForkedSetter(Setter):
    '''A lenses representing the parallel composition of several sub-lenses.

        >>> from lenses import lens
        >>> lens().fork_(lens()[0], lens()[2])
        Lens(None, (GetitemLens(0)) | (GetitemLens(2)))
        >>> lens([[0, 0], 0, 0]).fork_(lens()[0][1], lens()[2]).set(1)
        [[0, 1], 0, 1]
    '''

    def __init__(self, *lenses):
        self.lenses = [lens._underlying_lens() for lens in lenses]

    def func(self, f, state):
        for lens in self.lenses:
            state = lens.func(f, state).unwrap()

        return Identity(state)

    def __repr__(self):
        return ' | '.join('({})'.format(l) for l in self.lenses)
