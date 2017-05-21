from typing import (Callable, List, Optional, Type)

from .. import optics
from ..typevars import S, T, A, B, X, Y

from .base import Lens

class UnboundLens(Lens[S, T, A, B]):
    'An unbound lens is a lens that has not been bound to any state.'

    __slots__ = ['_optic']

    def __init__(self, optic):
        self._optic = optic

    def __repr__(self):
        # type: () -> str
        return 'UnboundLens({!r})'.format(self._optic)

    def get(self):
        # type: () -> Callable[[S], B]
        '''Get the first value focused by the lens.

            >>> from lenses import lens
            >>> getter = lens().get()
            >>> getter([1, 2, 3])
            [1, 2, 3]
            >>> zero_item_getter = lens()[0].get()
            >>> zero_item_getter([1, 2, 3])
            1
        '''
        def getter(state):
            return self.bind(state).get()
        return getter

    def get_all(self):
        # type: () -> Callable[[S], List[B]]
        '''Get multiple values focused by the lens. Returns them as
        a list.

            >>> from lenses import lens
            >>> get_all_item_zero = lens()[0].get_all()
            >>> get_all_item_zero([1, 2, 3])
            [1]
            >>> get_both = lens().both_().get_all()
            >>> get_both([1, 2, 3])
            [1, 2]
        '''
        def getter(state):
            return self.bind(state).get_all()
        return getter

    def get_monoid(self):
        # type: () -> Callable[[S], B]
        '''Get the values focused by the lens, merging them together by
        treating them as a monoid. See `lenses.typeclass.mappend`.

            >>> from lenses import lens
            >>> get_each_monoidally = lens().each_().get_monoid()
            >>> get_each_monoidally([[], [1], [2, 3]])
            [1, 2, 3]
        '''
        def getter(state):
            return self.bind(state).get_monoid()
        return getter

    def set(self, newvalue):
        # type: (B) -> Callable[[S], T]
        '''Set the focus to `newvalue`.

            >>> from lenses import lens
            >>> set_item_one_to_four = lens()[1].set(4)
            >>> set_item_one_to_four([1, 2, 3])
            [1, 4, 3]
        '''
        def setter(state):
            return self.bind(state).set(newvalue)
        return setter

    def modify(self, func):
        # type: (Callable[[A], B]) -> Callable[[S], T]
        '''Apply a function to the focus.

            >>> from lenses import lens
            >>> convert_item_one_to_string = lens()[1].modify(str)
            >>> convert_item_one_to_string([1, 2, 3])
            [1, '2', 3]
            >>> add_ten_to_item_one = lens()[1].modify(lambda n: n + 10)
            >>> add_ten_to_item_one([1, 2, 3])
            [1, 12, 3]
        '''
        def modifier(state):
            return self.bind(state).modify(func)
        return modifier

    def construct(self, focus):
        # type: (A) -> S
        '''Construct a state given a focus.'''
        return self._optic.re().view(focus)


    def flip(self):
        # type: () -> UnboundLens[A, B, S, T]
        '''Flips the direction of the lens. The lens must be unbound
        and all the underlying operations must be isomorphisms.

            >>> from lenses import lens
            >>> json_encoder = lens().decode_().json_().flip()
            >>> json_encoder.bind(['hello', 'world']).get()  # doctest: +SKIP
            b'["hello", "world"]'
        '''
        return UnboundLens(self._optic.from_())

    def bind(self, state):
        # type: (S) -> BoundLens[S, T, A, B]
        '''Bind this lens to a specific `state`.

            >>> from lenses import lens
            >>> lens()[1].bind([1, 2, 3]).get()
            2
        '''
        return BoundLens(state, self._optic)

    def add_lens(self, other):
        # type: (UnboundLens[A, B, X, Y]) -> UnboundLens[S, T, X, Y]
        '''Refine the current focus of this lens by composing it with
        another lens object. The other lens must be unbound.

            >>> from lenses import lens
            >>> first = lens()[0]
            >>> second = lens()[1]
            >>> second_first = second.add_lens(first)
            >>> get_second_then_first = second_first.get()
            >>> get_second_then_first([[0, 1], [2, 3]])
            2
        '''
        if not isinstance(other, UnboundLens):
            message = 'Cannot add lens of type {!r}.'
            raise TypeError(message.format(type(other)))
        return self._compose_optic(other._optic)

    def __get__(self, instance, owner):
        # type: (Optional[S], Type) -> Lens[S, T, A, B]
        if instance is None:
            return self
        return self.bind(instance)

    def _underlying_lens(self):
        # type: () -> optics.LensLike
        return self._optic

    def _compose_optic(self, optic):
        # type: (optics.LensLike) -> UnboundLens[S, T, X, Y]
        return UnboundLens(self._optic.compose(optic))


class BoundLens(Lens[S, T, A, B]):
    'A bound lens is a lens that has been bound to a specific state.'

    __slots__ = ['_state', '_optic']

    def __init__(self, state, optic):
        # type: (S, optics.LensLike) -> None
        self._state = state
        self._optic = optic

    def __repr__(self):
        # type: () -> str
        return 'BoundLens({!r}, {!r})'.format(self._state, self._optic)

    def get(self):
        # type: () -> B
        '''Get the first value focused by the lens.

            >>> from lenses import lens
            >>> lens([1, 2, 3]).get()
            [1, 2, 3]
            >>> lens([1, 2, 3])[0].get()
            1
        '''
        return self._optic.to_list_of(self._state)[0]

    def get_all(self):
        # type: () -> List[B]
        '''Get multiple values focused by the lens. Returns them as
        a list.

            >>> from lenses import lens
            >>> lens([1, 2, 3])[0].get_all()
            [1]
            >>> lens([1, 2, 3]).both_().get_all()
            [1, 2]
        '''
        return self._optic.to_list_of(self._state)

    def get_monoid(self):
        # type: () -> B
        '''Get the values focused by the lens, merging them together by
        treating them as a monoid. See `lenses.typeclass.mappend`.

            >>> from lenses import lens
            >>> lens([[], [1], [2, 3]]).each_().get_monoid()
            [1, 2, 3]
        '''
        return self._optic.view(self._state)

    def set(self, newvalue):
        # type: (B) -> T
        '''Set the focus to `newvalue`.

            >>> from lenses import lens
            >>> lens([1, 2, 3])[1].set(4)
            [1, 4, 3]
        '''
        return self._optic.set(self._state, newvalue)

    def modify(self, func):
        # type: (Callable[[A], B]) -> T
        '''Apply a function to the focus.

            >>> from lenses import lens
            >>> lens([1, 2, 3])[1].modify(str)
            [1, '2', 3]
            >>> lens([1, 2, 3])[1].modify(lambda n: n + 10)
            [1, 12, 3]
        '''
        return self._optic.over(self._state, func)

    def bind(self, state):
        raise ValueError('Lens already bound')

    def add_lens(self, other):
        # type: (UnboundLens[A, B, X, Y]) -> BoundLens[S, T, X, Y]
        '''Refine the current focus of this lens by composing it with
        another lens object. The other lens must be unbound.

            >>> from lenses import lens
            >>> first = lens()[0]
            >>> second = lens([[0, 1], [2, 3]])[1]
            >>> second.add_lens(first).get()
            2
        '''
        if not isinstance(other, UnboundLens):
            message = 'Cannot add lens of type {!r}.'
            raise TypeError(message.format(type(other)))
        return self._compose_optic(other._optic)

    def _underlying_lens(self):
        # type: () -> optics.LensLike
        return self._optic

    def _compose_optic(self, optic):
        # type: (optics.LensLike) -> BoundLens[S, T, X, Y]
        return BoundLens(self._state, self._optic.compose(optic))
