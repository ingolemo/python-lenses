from typing import Callable, Generic

from .typeclass import apply, pure
from .typevars import A, B


class Identity(Generic[A]):
    '''The identiy functor applies functions to its contents
    with no additional funtionality. It is the trivial or null
    functor.

    It is needed for lenses to be able to set values.
    '''

    __slots__ = ('item',)

    def __init__(self, item):
        # type: (A) -> None
        self.item = item

    def __repr__(self):
        # type: () -> str
        return '{}({!r})'.format(self.__class__.__name__, self.item)

    def __eq__(self, other):
        # type: (object) -> bool
        if not isinstance(other, Identity):
            return False
        return bool(self.item == other.item)

    def map(self, fn):
        # type: (Callable[[A], B]) -> Identity[B]
        return Identity(fn(self.item))

    @classmethod
    def pure(cls, item):
        # type: (A) -> Identity[A]
        return cls(item)

    def apply(self, fn):
        # type: (Identity[Callable[[A], B]]) -> Identity[B]
        return Identity(fn.item(self.item))

    def unwrap(self):
        # type: () -> A
        return self.item
