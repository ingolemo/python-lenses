from typing import Any, Callable, Generic, List, Tuple, Dict, TypeVar


import sys
from functools import singledispatch

A = TypeVar("A")
B = TypeVar("B")

# monoid
@singledispatch
def mempty(monoid: Any) -> Any:
    return monoid.mempty()


@singledispatch
def mappend(monoid: Any, other: Any) -> Any:
    return monoid + other


@mempty.register(int)
def _mempty_int(self: int) -> int:
    return 0


@mempty.register(str)
def _mempty_str(string: str) -> str:
    return ""


@mempty.register(list)
def _mempty_list(lst: List[A]) -> List[A]:
    return []


@mempty.register(tuple)
def _mempty_tuple(tup: Tuple[Any, ...]) -> Tuple[Any, ...]:
    return tuple(mempty(item) for item in tup)


@mappend.register(tuple)
def _mappend_tuple(tup: Tuple[Any, ...], other: Tuple[Any, ...]) -> Tuple[Any, ...]:
    if len(tup) != len(other):
        raise ValueError("Cannot mappend tuples of differing lengths")
    result = ()  # type: Tuple[Any, ...]
    for x, y in zip(tup, other):
        result += (mappend(x, y),)
    return result


@mempty.register(dict)
def _mempty_dict(dct: dict) -> dict:
    return {}


@mappend.register(dict)
def _mappend_dict(dct: dict, other: dict) -> dict:
    out = {}
    out.update(dct)
    out.update(other)
    return out


# functor
@singledispatch
def fmap(functor: Any, func: Callable[[Any], Any]) -> Any:
    """Applies a function to the data 'inside' a functor.

    Uses functools.singledispatch so you can write your own functors
    for use with the library."""
    return functor.map(func)


@fmap.register(list)
def _fmap_list(lst: List[A], func: Callable[[A], B]) -> List[B]:
    return [func(a) for a in lst]


@fmap.register(tuple)
def _fmap_tuple(tup: Tuple[A, ...], func: Callable[[A], B]) -> Tuple[B, ...]:
    return tuple(func(a) for a in tup)


# applicative functor
@singledispatch
def pure(applicative: Any, item: B) -> Any:
    return applicative.pure(item)


@singledispatch
def apply(applicative: Any, func: Any) -> Any:
    return applicative.apply(func)


@pure.register(list)
def _pure_list(lst: List[A], item: B) -> List[B]:
    return [item]


@apply.register(list)
def _apply_list(lst: List[A], funcs: List[Callable[[A], B]]) -> List[B]:
    return [f(i) for i in lst for f in funcs]


@pure.register(tuple)
def _pure_tuple(tup: Tuple[A, ...], item: B) -> Tuple[B]:
    return (item,)


@apply.register(tuple)
def _apply_tuple(
    tup: Tuple[A, ...], funcs: Tuple[Callable[[A], B], ...]
) -> Tuple[B, ...]:
    return tuple(f(i) for i in tup for f in funcs)
