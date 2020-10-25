from typing import Callable, Generic, TypeVar

from .typeclass import mempty, mappend

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")
D = TypeVar("D")


class Const(Generic[C, A]):
    """An applicative functor that doesn't care about the data it's
    supposed to be a functor over, caring only about the data it was passed
    during creation. This type is essential to the lens' `get` operation.
    """

    __slots__ = ("item",)

    def __init__(self, item: C) -> None:
        self.item = item

    def __repr__(self) -> str:
        return "{}({!r})".format(self.__class__.__name__, self.item)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Const):
            return False
        return bool(self.item == other.item)

    def map(self, func: Callable[[A], B]) -> "Const[C, B]":
        return Const(self.item)

    def pure(self, item: D) -> "Const[D, B]":
        return Const(mempty(self.item))

    def apply(self, fn: "Const[C, Callable[[A], B]]") -> "Const[C, B]":
        return Const(mappend(fn.item, self.item))

    def unwrap(self) -> C:
        return self.item
