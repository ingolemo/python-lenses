from typing import Callable, Generic, Iterator, Optional, Union, TypeVar

from . import hooks
from . import typeclass

import sys

A = TypeVar("A")
B = TypeVar("B")


class Just(Generic[A]):
    """A class that can contain a value or not. If it contains a value
    then it will be an instance of Just. If it doesn't then it will be
    an instance of Nothing. You can wrap an existing value By calling
    the Just constructor:

        >>> from lenses.maybe import Just, Nothing
        >>> Just(1)
        Just(1)

    To extract it again you can use the `maybe` method:

        >>> Just(1).maybe()
        1
    """

    # The typing module in 3.5.2 is broken when using Generic with __slots__,
    # see https://github.com/python/typing/issues/332
    # We can just skip defining __slots__ and this will work fine for that
    # version, at a slight overhead expense.
    if sys.version_info[:3] != (3, 5, 2):
        __slots__ = ("item",)

    def __init__(self, item: A) -> None:
        self.item = item

    def __add__(self, other: "Just[A]") -> "Just[A]":
        if other.is_nothing():
            return self
        return Just(typeclass.mappend(self.item, other.item))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Just):
            return False

        return bool(self.item == other.item)

    def __iter__(self) -> Iterator[A]:
        yield self.item

    def __repr__(self) -> str:
        return "Just({!r})".format(self.item)

    def map(self, fn: Callable[[A], B]) -> "Just[B]":
        """Apply a function to the value inside the Maybe."""
        return Just(fn(self.item))

    def maybe(self, guard: B = None) -> Union[None, A, B]:
        """Unwraps the value, returning it is there is one, else
        returning the guard."""
        return self.item

    def unwrap(self) -> A:
        return self.item

    def is_nothing(self) -> bool:
        return False


class Nothing(Just[A]):
    __slots__ = ()

    def __init__(self) -> None:
        pass

    def __add__(self, other: Just[A]) -> Just[A]:
        return other

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Nothing)

    def __iter__(self) -> Iterator[A]:
        return iter([])

    def __repr__(self) -> str:
        return "Nothing()"

    def map(self, fn: Callable[[A], B]) -> Just[B]:
        """Apply a function to the value inside the Maybe."""
        return Nothing()

    def maybe(self, guard: B = None) -> Union[None, A, B]:
        """Unwraps the value, returning it is there is one, else
        returning the guard."""
        return guard

    def unwrap(self) -> A:
        raise ValueError("Cannot unwrap Nothing")

    def is_nothing(self) -> bool:
        return True


@typeclass.mempty.register(Just)
def _maybe_mempty(self: Just[A]) -> Nothing:
    return Nothing()


@typeclass.fmap.register(Just)
def _maybe_fmap(self: Just[A], fn: Callable[[A], B]) -> Just[B]:
    return self.map(fn)


@typeclass.pure.register(Just)
def _maybe_pure(self: Just, item: B) -> Just[B]:
    return Just(item)


@typeclass.apply.register(Just)
def _maybe_apply(self: Just[A], fn: Just[Callable[[A], B]]) -> Just[B]:
    if self.is_nothing() or fn.is_nothing():
        return Nothing()
    return Just(fn.item(self.item))


@hooks.from_iter.register(Just)
def _maybe_from_iter(self: Just, iter: Iterator[A]) -> Just[A]:
    i = list(iter)
    if i == []:
        return Nothing()
    return Just(i[0])
