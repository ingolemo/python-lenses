from typing import Callable, Iterable, List, Optional, Type, TypeVar

from .. import optics

from .base import BaseUiLens

S = TypeVar("S")
T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")
X = TypeVar("X")
Y = TypeVar("Y")


class UnboundLens(BaseUiLens[S, T, A, B]):
    "An unbound lens is a lens that has not been bound to any state."

    __slots__ = ("_optic",)

    def __init__(self, optic):
        self._optic = optic

    def __repr__(self) -> str:
        return "UnboundLens({!r})".format(self._optic)

    def get(self) -> Callable[[S], B]:
        """Get the first value focused by the lens.

        >>> from lenses import lens
        >>> getter = lens.get()
        >>> getter([1, 2, 3])
        [1, 2, 3]
        >>> zero_item_getter = lens[0].get()
        >>> zero_item_getter([1, 2, 3])
        1
        """

        def getter(state):
            return self._optic.to_list_of(state)[0]

        return getter

    def collect(self) -> Callable[[S], List[B]]:
        """Get multiple values focused by the lens. Returns them as
        a list.

            >>> from lenses import lens
            >>> collect_each_first = lens.Each()[0].collect()
            >>> collect_each_first([(1, 2), (3, 4), (5, 6)])
            [1, 3, 5]
        """

        def getter(state):
            return self._optic.to_list_of(state)

        return getter

    def get_monoid(self) -> Callable[[S], B]:
        """Get the values focused by the lens, merging them together by
        treating them as a monoid. See `lenses.typeclass.mappend`.

            >>> from lenses import lens
            >>> get_each_monoidally = lens.Each().get_monoid()
            >>> get_each_monoidally([[], [1], [2, 3]])
            [1, 2, 3]
        """

        def getter(state):
            return self._optic.view(state)

        return getter

    def set(self, newvalue: B) -> Callable[[S], T]:
        """Set the focus to `newvalue`.

        >>> from lenses import lens
        >>> set_item_one_to_four = lens[1].set(4)
        >>> set_item_one_to_four([1, 2, 3])
        [1, 4, 3]
        """

        def setter(state):
            return self._optic.set(state, newvalue)

        return setter

    def set_many(self, new_values: Iterable[B]) -> Callable[[S], T]:
        """Set many foci to values taken by iterating over `new_values`.

        >>> from lenses import lens
        >>> lens.Each().set_many(range(4, 7))([0, 1, 2])
        [4, 5, 6]
        """

        def setter_many(state):
            return self._optic.iterate(state, new_values)

        return setter_many

    def modify(self, func: Callable[[A], B]) -> Callable[[S], T]:
        """Apply a function to the focus.

        >>> from lenses import lens
        >>> convert_item_one_to_string = lens[1].modify(str)
        >>> convert_item_one_to_string([1, 2, 3])
        [1, '2', 3]
        >>> add_ten_to_item_one = lens[1].modify(lambda n: n + 10)
        >>> add_ten_to_item_one([1, 2, 3])
        [1, 12, 3]
        """

        def modifier(state):
            return self._optic.over(state, func)

        return modifier

    def construct(self, focus: A) -> S:
        """Construct a state given a focus."""
        return self._optic.re().view(focus)

    def flip(self) -> "UnboundLens[A, B, S, T]":
        """Flips the direction of the lens. The lens must be unbound
        and all the underlying operations must be isomorphisms.

            >>> from lenses import lens
            >>> json_encoder = lens.Decode().Json().flip()
            >>> json_encode = json_encoder.get()
            >>> json_encode(['hello', 'world'])  # doctest: +SKIP
            b'["hello", "world"]'
        """
        return UnboundLens(self._optic.re())

    def __and__(self, other: "UnboundLens[A, B, X, Y]") -> "UnboundLens[S, T, X, Y]":
        """Refine the current focus of this lens by composing it with
        another lens object. The other lens must be unbound.

            >>> from lenses import lens
            >>> first = lens[0]
            >>> second = lens[1]
            >>> second_first = second & first
            >>> get_second_then_first = second_first.get()
            >>> get_second_then_first([[0, 1], [2, 3]])
            2
        """
        if not isinstance(other, UnboundLens):
            message = "Cannot compose lens of type {!r}."
            raise TypeError(message.format(type(other)))
        return self._compose_optic(other._optic)

    def __get__(self, instance: Optional[S], owner: Type) -> BaseUiLens[S, T, A, B]:
        if instance is None:
            return self
        return BoundLens(instance, self._optic)

    def _compose_optic(self, optic: optics.LensLike) -> "UnboundLens[S, T, X, Y]":
        return UnboundLens(self._optic.compose(optic))

    def _wrap_optic(
        self, optic: Callable[[optics.LensLike], optics.LensLike]
    ) -> "UnboundLens[S, T, X, Y]":
        return UnboundLens(optic(self._optic))

    def kind(self) -> str:
        'Returns the "kind" of the lens.'
        return self._optic.kind().__name__

    add_lens = __and__


class BoundLens(BaseUiLens[S, T, A, B]):
    "A bound lens is a lens that has been bound to a specific state."

    __slots__ = ("_state", "_optic")

    def __init__(self, state: S, optic: optics.LensLike) -> None:
        self._state = state
        self._optic = optic

    def __repr__(self) -> str:
        return "BoundLens({!r}, {!r})".format(self._state, self._optic)

    def get(self) -> B:
        """Get the first value focused by the lens.

        >>> from lenses import bind
        >>> bind([1, 2, 3]).get()
        [1, 2, 3]
        >>> bind([1, 2, 3])[0].get()
        1
        """
        return self._optic.to_list_of(self._state)[0]

    def collect(self) -> List[B]:
        """Get multiple values focused by the lens. Returns them as
        a list.

            >>> from lenses import bind
            >>> bind([(1, 2), (3, 4), (5, 6)]).Each()[0].collect()
            [1, 3, 5]
        """
        return self._optic.to_list_of(self._state)

    def get_monoid(self) -> B:
        """Get the values focused by the lens, merging them together by
        treating them as a monoid. See `lenses.typeclass.mappend`.

            >>> from lenses import bind
            >>> bind([[], [1], [2, 3]]).Each().get_monoid()
            [1, 2, 3]
        """
        return self._optic.view(self._state)

    def set(self, newvalue: B) -> T:
        """Set the focus to `newvalue`.

        >>> from lenses import bind
        >>> bind([1, 2, 3])[1].set(4)
        [1, 4, 3]
        """
        return self._optic.set(self._state, newvalue)

    def set_many(self, new_values: Iterable[B]) -> T:
        """Set many foci to values taken by iterating over `new_values`.

        >>> from lenses import bind
        >>> bind([0, 1, 2]).Each().set_many(range(4, 7))
        [4, 5, 6]
        """

        return self._optic.iterate(self._state, new_values)

    def modify(self, func: Callable[[A], B]) -> T:
        """Apply a function to the focus.

        >>> from lenses import bind
        >>> bind([1, 2, 3])[1].modify(str)
        [1, '2', 3]
        >>> bind([1, 2, 3])[1].modify(lambda n: n + 10)
        [1, 12, 3]
        """
        return self._optic.over(self._state, func)

    def __and__(self, other: UnboundLens[A, B, X, Y]) -> "BoundLens[S, T, X, Y]":
        """Refine the current focus of this lens by composing it with
        another lens object. The other lens must be unbound.

            >>> from lenses import lens, bind
            >>> first = lens[0]
            >>> second = bind([[0, 1], [2, 3]])[1]
            >>> (second & first).get()
            2
        """
        if not isinstance(other, UnboundLens):
            message = "Cannot compose lens of type {!r}."
            raise TypeError(message.format(type(other)))
        return self._compose_optic(other._optic)

    def _compose_optic(self, optic: optics.LensLike) -> "BoundLens[S, T, X, Y]":
        return BoundLens(self._state, self._optic.compose(optic))

    def _wrap_optic(
        self, optic: Callable[[optics.LensLike], optics.LensLike]
    ) -> "BoundLens[S, T, X, Y]":
        return BoundLens(self._state, optic(self._optic))

    def kind(self) -> str:
        'Returns the "kind" of the lens.'
        return self._optic.kind().__name__

    add_lens = __and__


__all__ = ["UnboundLens", "BoundLens"]
