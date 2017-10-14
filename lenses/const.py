from typing import Callable, Generic

from .typeclass import mempty, mappend
from .typevars import A, B, C, D


class Const(Generic[C, A]):
    '''An applicative functor that doesn't care about the data it's
    supposed to be a functor over, caring only about the data it was passed
    during creation. This type is essential to the lens' `get` operation.
    '''
    __slots__ = ('item',)

    def __init__(self, item):
        # type: (C) -> None
        self.item = item

    def __repr__(self):
        # type: () -> str
        return '{}({!r})'.format(self.__class__.__name__, self.item)

    def __eq__(self, other):
        # type: (object) -> bool
        if not isinstance(other, Const):
            return False
        return bool(self.item == other.item)

    def map(self, func):
        # type: (Callable[[A], B]) -> Const[C, B]
        return Const(self.item)

    def pure(self, item):
        # type: (D) -> Const[D, B]
        return Const(mempty(self.item))

    def apply(self, fn):
        # type: (Const[C, Callable[[A], B]]) -> Const[C, B]
        return Const(mappend(fn.item, self.item))

    def unwrap(self):
        # type: () -> C
        return self.item
