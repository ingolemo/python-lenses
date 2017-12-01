'''This module contains functions that you can hook into to allow
various lenses to operate on your own custom data structures.
'''

from typing import Any, Dict, Iterable, Iterator, List, Set, Tuple
from singledispatch import singledispatch
import copy
import sys

from ..typevars import A, B


@singledispatch
def setitem_immutable(self, key, value):
    # type: (Any, Any, Any) -> Any
    '''Takes an object, a key, and a value and produces a new object
    that is a copy of the original but with `value` as the new value of
    `key`.

        setitem_immutable(obj, key, obj[key]) == obj

    This function is used by many lenses (particularly GetitemLens) to
    set items on states even when those states do not ordinarily support
    `setitem`. This function is designed to have a similar signature as
    python's built-in `setitem` except that it returns a new object that
    has the item set rather than mutating the object in place.

    The default behaviour of this function is to call
    `obj._lens_setitem(key, value)` in the hope that the object knows
    how to set items immutably on itself. If that fails then it will
    make a copy of the object using `copy.copy` and will then mutate the
    new object by setting the item on it in the conventional way. This
    copying approach works for the vast majority of python objects, but
    if it doesn't work for your type then you should define the
    `_lens_setitem` method. This function is also wrapped with
    `functools.singledispatch`, allowing you to customise the behaviour
    of types that you did not write. Be warned that single dispatch
    functions are registered globally across your program and that your
    function also needs to be able to deal with subclasses of any types
    you register (or else register separate functions for each
    subclass).
    '''
    try:
        self._lens_setitem
    except AttributeError:
        selfcopy = copy.copy(self)
        selfcopy[key] = value
        return selfcopy
    else:
        return self._lens_setitem(key, value)


if sys.version_info[0] > 2:

    @setitem_immutable.register(bytes)
    def _bytes_setitem_immutable(self, key, value):
        # type: (bytes, int, int) -> bytes
        data = bytearray(self)
        data[key] = value
        return bytes(data)

    @setitem_immutable.register(str)
    def _str_setitem_immutable(self, key, value):
        # type: (str, int, str) -> str
        data = list(self)
        data[key] = value
        return ''.join(data)
else:

    @setitem_immutable.register(str)
    def _bytes_setitem_immutable(self, key, value):
        # type: (str, int, int) -> str
        data = bytearray(self)
        data[key] = value
        return bytes(data)

    @setitem_immutable.register(unicode)
    def _str_setitem_immutable(self, key, value):
        # type: (unicode, int, int) -> unicode
        data = list(self)
        data[key] = value
        return ''.join(data)


@setitem_immutable.register(tuple)
def _tuple_setitem_immutable(self, key, value):
    # type: (Tuple[A, ...], int, A) -> Tuple[A, ...]
    return tuple(value if i == key else item for i, item in enumerate(self))


@singledispatch
def setattr_immutable(self, name, value):
    # type: (Any, Any, Any) -> Any
    '''Takes an object, a string, and a value and produces a new object
    that is a copy of the original but with the attribute called `name`
    set to `value`.

        setattr_immutable(obj, 'attr', obj.attr) == obj

    This function is used by many lenses (particularly GetattrLens) to
    set attributes on states even when those states do not ordinarily
    support `setattr`. This function is designed to have a similar
    signature as python's built-in `setattr` except that it returns a
    new object that has the attribute set rather than mutating the
    object in place.

    The default behaviour of this function is to call
    `obj._lens_setattr(name, value)` in the hope that the object knows
    how to set attributes immutably on itself. If that fails then it
    will make a copy of the object using `copy.copy` and will then
    mutate the new object by calling the conventional `setattr` on it.
    This copying approach works for the vast majority of python objects,
    but if it doesn't work for your type then you should define the
    `_lens_setattr` method. This function is also wrapped with
    `functools.singledispatch`, allowing you to customise the behaviour
    of types that you did not write. Be warned that single dispatch
    functions are registered globally across your program and that your
    function also needs to be able to deal with subclasses of any types
    you register (or else register separate functions for each
    subclass).
    '''
    try:
        self._lens_setattr
    except AttributeError:
        selfcopy = copy.copy(self)
        setattr(selfcopy, name, value)
        return selfcopy
    else:
        return self._lens_setattr(name, value)


@setattr_immutable.register(tuple)
def _tuple_setattr_immutable(self, name, value):
    # type: (Any, str, A) -> Any
    # setting attributes on a tuple probably means we really have a
    # namedtuple so we can use self._fields to understand the names
    data = (
        value if field == name else item
        for field, item in zip(self._fields, self)
    )
    return type(self)(*data)


@singledispatch
def contains_add(self, item):
    # type (Any, Any) -> Any
    '''Takes a collection and an item and returns a new collection of
    the same type that contains the item. The notion of "contains"
    is defined by the object itself; ``item in contains_add(obj, item)``
    must be true.

    This function is used by some lenses (particularly ContainsLens) to
    add new items to containers when necessary.

    The default behaviour of this function is to call
    ``obj._lens_contains_add(item)`` in the hope that the object knows
    how to add items to itself. This function is also wrapped with
    ``functools.singledispatch``, allowing you to customise the behaviour
    of types that you did not write. Be warned that single dispatch
    functions are registered globally across your program and that your
    function also needs to be able to deal with subclasses of any types
    you register (or else register separate functions for each subclass).
    '''
    try:
        self._lens_contains_add
    except AttributeError:
        message = 'Don\'t know how to add an item to {}'
        raise NotImplementedError(message.format(type(self)))
    else:
        return self._lens_contains_add(item)


@contains_add.register(list)
def _list_contains_add(self, item):
    # type (List[A], A) -> List[A]
    return self + [item]


@contains_add.register(tuple)
def _tuple_contains_add(self, item):
    # type (Tuple[A, ...], A) -> Tuple[A, ...]
    return self + (item,)


@contains_add.register(dict)
def _dict_contains_add(self, item):
    # type (Dict[A, B], A) -> Dict[A, B]
    result = self.copy()
    result[item] = None
    return result


@contains_add.register(set)
def _set_contains_add(self, item):
    # type (Set[A], A) -> Set[A]
    return self | {item}


@singledispatch
def contains_remove(self, item):
    # type (Any, Any) -> Any
    '''Takes a collection and an item and returns a new collection
    of the same type with that item removed. The notion of "contains"
    is defined by the object itself; ``item not in contains_add(obj,
    item)`` must be true.

    This function is used by some lenses (particularly ContainsLens) to
    remove items from containers when necessary.

    The default behaviour of this function is to call
    ``obj._lens_contains_remove(item)`` in the hope that the object knows
    how to add items to itself. This function is also wrapped with
    ``functools.singledispatch``, allowing you to customise the behaviour
    of types that you did not write. Be warned that single dispatch
    functions are registered globally across your program and that your
    function also needs to be able to deal with subclasses of any types
    you register (or else register separate functions for each subclass).
    '''
    try:
        self._lens_contains_remove
    except AttributeError:
        message = 'Don\'t know how to remove an item from {}'
        raise NotImplementedError(message.format(type(self)))
    else:
        return self._lens_contains_remove(item)


@contains_remove.register(list)
def _list_contains_remove(self, item):
    # type (List[A], A) -> List[A]
    return [x for x in self if x != item]


@contains_remove.register(tuple)
def _tuple_contains_remove(self, item):
    # type (Tuple[A, ...], A) -> Tuple[A, ...]
    return tuple(x for x in self if x != item)


@contains_remove.register(dict)
def _dict_contains_remove(self, item):
    # type (Dict[A, B], A) -> Dict[A, B]
    result = self.copy()
    del result[item]
    return result


@contains_remove.register(set)
def _set_contains_remove(self, item):
    # type (Set[A], A) -> Set[A]
    return self - {item}


@singledispatch
def to_iter(self):
    # type: (Any) -> Any
    '''Takes an object and produces an iterable. It is
    intended as the inverse of the `from_iter` function.

    For most types this hook is a thin wrapper around python's built-in
    `iter` function. Its default behaviour is to call `iter` and this
    is usually sufficient.

    The reason this hook exists is to customise how dictionaries are
    iterated. In order to properly reconstruct a dictionary from an
    iterable you need access to both the keys and the values. So this
    function iterates over dictionaries by thier items instead.

    This function will try to call a `_lens_to_iter()` method on its
    argument before it calls `iter`, allowing you to have different
    behaviours for lens iteration and regular iteration if you wish. This
    function is also wrapped with `functools.singledispatch`, allowing
    it to have different implementations for each type.
    '''
    try:
        self._lens_to_iter
    except AttributeError:
        return iter(self)
    else:
        return self._lens_to_iter()


@to_iter.register(dict)
def _dict_to_iter(self):
    # type: (Dict[A, B]) -> Iterator[Tuple[A, B]]
    return iter(self.items())


@singledispatch
def from_iter(self, iterable):
    # type: (Any, Any) -> Any
    '''Takes an object and an iterable and produces a new object that is
    a copy of the original with data from `iterable` reincorporated. It
    is intended as the inverse of the `to_iter` function. Any state in
    `self` that is not modelled by the iterable should remain unchanged.

        from_iter(self, to_iter(self)) == self

    This function is used by EachLens to synthesise states from
    iterables, allowing it to focus every element of an iterable state.

    The default behaviour of this function is to call
    `obj._lens_from_iter(iterable)` in the hope that the object knows how
    to create new versions of itself from an iterable. Many types can be
    created from iterables but do not use a `_lens_fromiter` method to
    do this. For that reason, this function is also wrapped with
    `functools.singledispatch`, allowing it to have different
    implementations for each type. Unlike some other functions in this
    module, there is no widely applicable fallback behaviour. If all
    else fails, it will raise a `NotImplementedError`.
    '''
    try:
        self._lens_from_iter
    except AttributeError:
        message = 'Don\'t know how to create instance of {} from iterable'
        raise NotImplementedError(message.format(type(self)))
    else:
        return self._lens_from_iter(iterable)


if sys.version_info[0] > 2:

    @from_iter.register(bytes)
    def _bytes_from_iter(self, iterable):
        # type: (bytes, Iterable[int]) -> bytes
        return bytes(iterable)

    @from_iter.register(str)
    def _str_from_iter(self, iterable):
        # type: (str, Iterable[str]) -> str
        return ''.join(iterable)
else:

    @from_iter.register(str)
    def _bytes_from_iter(self, iterable):
        # type: (str, Iterable[str]) -> str
        return ''.join(iterable)

    @from_iter.register(unicode)
    def _str_from_iter(self, iterable):
        # type: (unicode, Iterable[unicode]) -> unicode
        return u''.join(iterable)


@from_iter.register(dict)
def _dict_from_iter(self, iterable):
    # type: (Dict, Iterable[Tuple[A, B]]) -> Dict[A, B]
    new = self.copy()
    new.clear()
    new.update(iterable)
    return new


@from_iter.register(list)
def _list_from_iter(self, iterable):
    # type: (List, Iterable[A]) -> List[A]
    return list(iterable)


@from_iter.register(set)
def _set_from_iter(self, iterable):
    # type: (Set, Iterable[A]) -> Set[A]
    return set(iterable)


@from_iter.register(tuple)
def _tuple_from_iter(self, iterable):
    if type(self) is tuple:
        return tuple(iterable)
    elif hasattr(self, '_make'):
        # this is probably a namedtuple
        return self._make(iterable)
    else:
        message = 'Don\'t know how to create instance of {} from iterable'
        raise NotImplementedError(message.format(type(self)))
