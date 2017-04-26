from ..const import Const
from ..typeclass import fmap

from .base import Getter


class FunctionGetter(Getter):
    '''Converts a function into a getter. The function is called on the
    focus before it is returned.

        >>> from lenses import lens
        >>> lens().f_(abs)
        Lens(None, FunctionGetter(<built-in function abs>))
        >>> lens(-1).f_(abs).get()
        1
        >>> lens([-1, 2, -3]).each_().f_(abs).get_all()
        [1, 2, 3]
    '''

    def __init__(self, function):
        self.function = function

    def func(self, f, state):
        return Const(fmap(f(state).unwrap(), self.function))

    def __repr__(self):
        return 'FunctionGetter({!r})'.format(self.function)
