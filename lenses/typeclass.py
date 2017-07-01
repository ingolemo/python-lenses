from typing import Any, Callable, Generic, List, Tuple, Dict

from singledispatch import singledispatch
import sys

from .typevars import A, B


# monoid
@singledispatch
def mempty(monoid):
    # type: (Any) -> Any
    return monoid.mempty()


@singledispatch
def mappend(monoid, other):
    # type: (Any, Any) -> Any
    return monoid + other


@mempty.register(int)
def _mempty_int(self):
    # type: (int) -> int
    return 0


if sys.version_info[0] < 3:

    @mempty.register(long)
    def _mempty_long(self):
        # type: (long) -> long
        return long(0)

    @mempty.register(unicode)
    def _memty_unicode(self):
        # type: (unicode) -> unicode
        return u''


@mempty.register(str)
def _mempty_str(string):
    # type: (str) -> str
    return ''


@mempty.register(list)
def _mempty_list(lst):
    # type: (list) -> list
    return []


@mempty.register(tuple)
def _mempty_tuple(tup):
    # type: (tuple) -> tuple
    return tuple(mempty(item) for item in tup)


@mappend.register(tuple)
def _mappend_tuple(tup, other):
    # type (tuple, tuple) -> tuple
    if len(tup) != len(other):
        raise ValueError('Cannot mappend tuples of differing lengths')
    result = ()
    for x, y in zip(tup, other):
        result += (mappend(x, y),)
    return result


@mempty.register(dict)
def _mempty_dict(dct):
    # type: (dict) -> dict
    return {}


@mappend.register(dict)
def _mappend_dict(dct, other):
    # type: (dict, dict) -> dict
    out = {}
    out.update(dct)
    out.update(other)
    return out


# functor
@singledispatch
def fmap(functor, func):
    # type: (Any, Callable[[Any], Any]) -> Any
    '''Applies a function to the data 'inside' a functor.

    Uses functools.singledispatch so you can write your own functors
    for use with the library.'''
    return functor.map(func)


@fmap.register(list)
def _fmap_list(lst, func):
    # type: (List[A], Callable[[A], B]) -> List[B]
    return [func(a) for a in lst]


@fmap.register(tuple)
def _fmap_tuple(tup, func):
    # type: (Tuple[A, ...], Callable[[A], B]) -> Tuple[B, ...]
    return tuple(func(a) for a in tup)


# applicative functor
@singledispatch
def pure(applicative, item):
    # type: (Any, B) -> Any
    return applicative.pure(item)


@singledispatch
def apply(applicative, func):
    # type: (Any, Any) -> Any
    return applicative.apply(func)


@pure.register(list)
def _pure_list(lst, item):
    # type: (List[A], B) -> List[B]
    return [item]


@apply.register(list)
def _apply_list(lst, funcs):
    # type: (List[A], List[Callable[[A], B]]) -> List[B]
    return [f(i) for i in lst for f in funcs]


@pure.register(tuple)
def _pure_tuple(tup, item):
    # type: (Tuple[A, ...], B) -> Tuple[B]
    return (item,)


@apply.register(tuple)
def _apply_tuple(tup, funcs):
    # type: (Tuple[A, ...], Tuple[Callable[[A], B], ...]) -> Tuple[B, ...]
    return tuple(f(i) for i in tup for f in funcs)
