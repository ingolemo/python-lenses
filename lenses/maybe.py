from typing import Callable, Generic, Iterator, Optional, Union

from . import hooks
from . import typeclass
from .typevars import A, B


class Just(Generic[A]):
    '''A class that can contain a value or not. If it contains a value
    then it will be an instance of Just. If it doesn't then it will be
    an instance of Nothing. You can wrap an existing value By calling
    the Just constructor:

        >>> from lenses.maybe import Just, Nothing
        >>> Just(1)
        Just(1)

    To extract it again you can use the `maybe` method:

        >>> Just(1).maybe()
        1
    '''

    __slots__ = ('item',)

    def __init__(self, item):
        # type: (A) -> None
        self.item = item

    def __add__(self, other):
        # type: (Just[A]) -> Just[A]
        if other.is_nothing():
            return self
        return Just(typeclass.mappend(self.item, other.item))

    def __eq__(self, other):
        # type: (object) -> bool
        if not isinstance(other, Just):
            return False

        return bool(self.item == other.item)

    def __iter__(self):
        # type: () -> Iterator[A]
        yield self.item

    def __repr__(self):
        # type: () -> str
        return 'Just({!r})'.format(self.item)

    def map(self, fn):
        # type: (Callable[[A], B]) -> Just[B]
        '''Apply a function to the value inside the Maybe.'''
        return Just(fn(self.item))

    def maybe(self, guard=None):
        # type: (B) -> Union[None, A, B]
        '''Unwraps the value, returning it is there is one, else
        returning the guard.'''
        return self.item

    def unwrap(self):
        # type: () -> A
        return self.item

    def is_nothing(self):
        # type: () -> bool
        return False


class Nothing(Just[A]):
    __slots__ = ()

    def __init__(self):
        # type: () -> None
        pass

    def __add__(self, other):
        # type: (Just[A]) -> Just[A]
        return other

    def __eq__(self, other):
        # type: (object) -> bool
        return isinstance(other, Nothing)

    def __iter__(self):
        # type: () -> Iterator[A]
        return iter([])

    def __repr__(self):
        # type: () -> str
        return 'Nothing()'

    def map(self, fn):
        # type: (Callable[[A], B]) -> Just[B]
        '''Apply a function to the value inside the Maybe.'''
        return Nothing()

    def maybe(self, guard=None):
        # type: (B) -> Union[None, A, B]
        '''Unwraps the value, returning it is there is one, else
        returning the guard.'''
        return guard

    def unwrap(self):
        # type: () -> A
        raise ValueError('Cannot unwrap Nothing')

    def is_nothing(self):
        # type: () -> bool
        return True


@typeclass.mempty.register(Just)
def _maybe_mempty(self):
    # type: (Just[A]) -> Nothing
    return Nothing()


@typeclass.fmap.register(Just)
def _maybe_fmap(self, fn):
    # type: (Just[A], Callable[[A], B]) -> Just[B]
    return self.map(fn)


@typeclass.pure.register(Just)
def _maybe_pure(self, item):
    # type: (Just, B) -> Just[B]
    return Just(item)


@typeclass.apply.register(Just)
def _maybe_apply(self, fn):
    # type: (Just[A], Just[Callable[[A], B]]) -> Just[B]
    if self.is_nothing() or fn.is_nothing():
        return Nothing()
    return Just(fn.item(self.item))


@hooks.from_iter.register(Just)
def _maybe_from_iter(self, iter):
    # type: (Just, Iterator[A]) -> Just[A]
    i = list(iter)
    if i == []:
        return Nothing()
    return Just(i[0])
