"""This module contains functions that you can hook into to allow various
lenses to operate on your own custom data structures.

You can hook into them by defining a method that starts with
``_lens_`` followed by the name of the hook function. So, for
example: the hook for ``lenses.hooks.contains_add`` is a method called
``_lens_contains_add``. This is the preferred way of hooking into this
library because it does not require you to have the lenses library as
a hard dependency.

These functions are all decorated with ``singledispatch``, allowing
you to customise the behaviour of types that you did not write. Be
warned that single dispatch functions are registered globally across
your program and that your function also needs to be able to deal with
subclasses of any types you register (or else register separate functions
for each subclass).

All of these hooks operate in the following order:

* Use an implementation registered with ``singledispatch.register``
  for the relevant type, if one exists.
* Use the relevant ``_lens_*`` method on the first object that was passed
  in, if it exists.
* Use a default implementation that is likely to work for most python
  objects, if one exists.
* Raise ``NotImplementedError``.
"""

from typing import (
    Any,
    Dict,
    FrozenSet,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    Set,
    Tuple,
    TypeVar,
)
import copy
import sys


import dataclasses
from functools import singledispatch
from builtins import setattr as builtin_setattr

A = TypeVar("A")
B = TypeVar("B")


@singledispatch
def setitem(self: Any, key: Any, value: Any) -> Any:
    """Takes an object, a key, and a value and produces a new object
    that is a copy of the original but with ``value`` as the new value of
    ``key``.

    The following equality should hold for your definition:

    .. code-block:: python

        setitem(obj, key, obj[key]) == obj

    This function is used by many lenses (particularly GetitemLens) to
    set items on states even when those states do not ordinarily support
    ``setitem``. This function is designed to have a similar signature
    as python's built-in ``setitem`` except that it returns a new object
    that has the item set rather than mutating the object in place.

    It's what enables the ``lens[some_key]`` functionality.

    The corresponding method call for this hook is
    ``obj._lens_setitem(key, value)``.

    The default implementation makes a copy of the object using
    ``copy.copy`` and then mutates the new object by setting the item
    on it in the conventional way.
    """
    try:
        self._lens_setitem
    except AttributeError:
        selfcopy = copy.copy(self)
        selfcopy[key] = value
        return selfcopy
    else:
        return self._lens_setitem(key, value)


@setitem.register(bytes)
def _bytes_setitem(self: bytes, key: int, value: int) -> bytes:
    data = bytearray(self)
    data[key] = value
    return bytes(data)


@setitem.register(str)
def _str_setitem(self: str, key: int, value: str) -> str:
    data = list(self)
    data[key] = value
    return "".join(data)


@setitem.register(tuple)
def _tuple_setitem(self: Tuple[A, ...], key: int, value: A) -> Tuple[A, ...]:
    return tuple(value if i == key else item for i, item in enumerate(self))


@singledispatch
def setattr(self: Any, name: Any, value: Any) -> Any:
    """Takes an object, a string, and a value and produces a new object
    that is a copy of the original but with the attribute called ``name``
    set to ``value``.

    The following equality should hold for your definition:

    .. code-block:: python

        setattr(obj, 'attr', obj.attr) == obj

    This function is used by many lenses (particularly GetattrLens) to set
    attributes on states even when those states do not ordinarily support
    ``setattr``. This function is designed to have a similar signature
    as python's built-in ``setattr`` except that it returns a new object
    that has the attribute set rather than mutating the object in place.

    It's what enables the ``lens.some_attribute`` functionality.

    The corresponding method call for this hook is
    ``obj._lens_setattr(name, value)``.

    The default implementation makes a copy of the object using
    ``copy.copy`` and then mutates the new object by calling python's
    built in ``setattr`` on it.
    """
    if dataclasses.is_dataclass(self) and not isinstance(self, type):
        return dataclasses.replace(self, **{name: value})

    try:
        self._lens_setattr
    except AttributeError:
        selfcopy = copy.copy(self)
        builtin_setattr(selfcopy, name, value)
        return selfcopy
    else:
        return self._lens_setattr(name, value)


@setattr.register(tuple)
def _tuple_setattr_immutable(self: NamedTuple, name: str, value: A) -> NamedTuple:
    # setting attributes on a tuple probably means we really have a
    # namedtuple so we can use self._fields to understand the names
    data = (value if field == name else item for field, item in zip(self._fields, self))
    return type(self)(*data)


@singledispatch
def contains_add(self: Any, item: Any) -> Any:
    """Takes a collection and an item and returns a new collection
    of the same type that contains the item. The notion of "contains"
    is defined by the object itself; The following must be ``True``:

    .. code-block:: python

        item in contains_add(obj, item)

    This function is used by some lenses (particularly ContainsLens)
    to add new items to containers when necessary.

    The corresponding method call for this hook is
    ``obj._lens_contains_add(item)``.

    There is no default implementation.
    """
    try:
        self._lens_contains_add
    except AttributeError:
        message = "Don't know how to add an item to {}"
        raise NotImplementedError(message.format(type(self)))
    else:
        return self._lens_contains_add(item)


@contains_add.register(list)
def _list_contains_add(self: List[A], item: A) -> List[A]:
    return self + [item]


@contains_add.register(tuple)
def _tuple_contains_add(self: Tuple[A, ...], item: A) -> Tuple[A, ...]:
    return self + (item,)


@contains_add.register(dict)
def _dict_contains_add(self: Dict[A, Any], item: A) -> Dict[A, Any]:
    result = self.copy()
    result[item] = None
    return result


@contains_add.register(set)
def _set_contains_add(self: Set[A], item: A) -> Set[A]:
    return self | {item}


@singledispatch
def contains_remove(self: Any, item: Any) -> Any:
    """Takes a collection and an item and returns a new collection
    of the same type with that item removed. The notion of "contains"
    is defined by the object itself; the following must be ``True``:

    .. code-block:: python

        item not in contains_remove(obj, item)

    This function is used by some lenses (particularly ContainsLens)
    to remove items from containers when necessary.

    The corresponding method call for this hook is
    ``obj._lens_contains_remove(item)``.

    There is no default implementation.
    """
    try:
        self._lens_contains_remove
    except AttributeError:
        message = "Don't know how to remove an item from {}"
        raise NotImplementedError(message.format(type(self)))
    else:
        return self._lens_contains_remove(item)


@contains_remove.register(list)
def _list_contains_remove(self: List[A], item: A) -> List[A]:
    return [x for x in self if x != item]


@contains_remove.register(tuple)
def _tuple_contains_remove(self: Tuple[A, ...], item: A) -> Tuple[A, ...]:
    return tuple(x for x in self if x != item)


@contains_remove.register(dict)
def _dict_contains_remove(self: Dict[A, B], item: A) -> Dict[A, B]:
    result = self.copy()
    del result[item]
    return result


@contains_remove.register(set)
def _set_contains_remove(self: Set[A], item: A) -> Set[A]:
    return self - {item}


@singledispatch
def to_iter(self: Any) -> Any:
    """Takes an object and produces an iterable. It is intended as the
    inverse of the ``from_iter`` function.

    The reason this hook exists is to customise how dictionaries are
    iterated. In order to properly reconstruct a dictionary from an
    iterable you need access to both the keys and the values. So this
    function iterates over dictionaries by thier items instead.

    The corresponding method call for this hook is
    ``obj._lens_to_iter()``.

    The default implementation is to call python's built in ``iter``
    function.
    """
    try:
        self._lens_to_iter
    except AttributeError:
        return iter(self)
    else:
        return self._lens_to_iter()


@to_iter.register(dict)
def _dict_to_iter(self: Dict[A, B]) -> Iterator[Tuple[A, B]]:
    return iter(self.items())


@singledispatch
def from_iter(self: Any, iterable: Any) -> Any:
    """Takes an object and an iterable and produces a new object that is
    a copy of the original with data from ``iterable`` reincorporated. It
    is intended as the inverse of the ``to_iter`` function. Any state in
    ``self`` that is not modelled by the iterable should remain unchanged.

    The following equality should hold for your definition:

    .. code-block:: python

        from_iter(self, to_iter(self)) == self

    This function is used by EachLens to synthesise states from iterables,
    allowing it to focus every element of an iterable state.

    The corresponding method call for this hook is
    ``obj._lens_from_iter(iterable)``.

    There is no default implementation.
    """
    try:
        self._lens_from_iter
    except AttributeError:
        message = "Don't know how to create instance of {} from iterable"
        raise NotImplementedError(message.format(type(self)))
    else:
        return self._lens_from_iter(iterable)


@from_iter.register(bytes)
def _bytes_from_iter(self: bytes, iterable: Iterable[int]) -> bytes:
    return bytes(iterable)


@from_iter.register(str)
def _str_from_iter(self: str, iterable: Iterable[str]) -> str:
    return "".join(iterable)


@from_iter.register(dict)
def _dict_from_iter(self: Dict, iterable: Iterable[Tuple[A, B]]) -> Dict[A, B]:
    new = self.copy()
    new.clear()
    new.update(iterable)
    return new


@from_iter.register(list)
def _list_from_iter(self: List, iterable: Iterable[A]) -> List[A]:
    return list(iterable)


@from_iter.register(set)
def _set_from_iter(self: Set, iterable: Iterable[A]) -> Set[A]:
    return set(iterable)


@from_iter.register(frozenset)
def _frozenset_from_iter(self: FrozenSet, iterable: Iterable[A]) -> FrozenSet[A]:
    return frozenset(iterable)


@from_iter.register(tuple)
def _tuple_from_iter(self, iterable):
    if type(self) is tuple:
        return tuple(iterable)
    elif hasattr(self, "_make"):
        # this is probably a namedtuple
        return self._make(iterable)
    else:
        message = "Don't know how to create instance of {} from iterable"
        raise NotImplementedError(message.format(type(self)))
