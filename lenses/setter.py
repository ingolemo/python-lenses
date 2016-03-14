from functools import singledispatch
import copy


@singledispatch
def setitem_immutable(self, key, value):
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


@setitem_immutable.register(bytes)
def _bytes_setitem_immutable(self, key, value):
    data = bytearray(self)
    data[key] = value
    return bytes(data)


@setitem_immutable.register(str)
def _str_setitem_immutable(self, key, value):
    data = list(self)
    data[key] = value
    return ''.join(data)


@setitem_immutable.register(tuple)
def _tuple_setitem_immutable(self, key, value):
    return tuple(value if i == key else item
                 for i, item in enumerate(self))


@singledispatch
def setattr_immutable(self, name, value):
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
    # setting attributes on a tuple probably means we really have a
    # namedtuple so we can use self._fields to understand the names
    data = (value if field == name else item
            for field, item in zip(self._fields, self))
    return type(self)(*data)


@singledispatch
def fromiter(self, iterable):
    '''Takes an object and an iterable and produces a new object that is
    a copy of the original with data from `iterable` reincorporated. It
    is intended as the inverse of the `iter` function. Any state in
    `self` that is not modelled by the iterable should remain unchanged.

        fromiter(self, iter(self)) == self

    This function is used by EachLens to synthesise states from
    iterables, allowing the lenses library to focus every element of an
    iterable state.

    The default behaviour of this function is to call
    `obj._lens_fromiter(iterable)` in the hope that the object knows how
    to create new versions of itself from an iterable. Many types can be
    created from iterables but do not use a `_lens_fromiter` method to
    do this. For that reason, this function is also wrapped with
    `functools.singledispatch`, allowing it to have different
    implementations for each type. Unlike some other functions in this
    module, there is no widely applicable fallback behaviour.
    '''
    try:
        self._lens_fromiter
    except AttributeError:
        message = 'Don\'t know how to create instance of {} from iterable'
        raise NotImplementedError(message.format(type(self)))
    else:
        return self._lens_fromiter(iterable)


@fromiter.register(bytes)
def _bytes_fromiter(self, iterable):
    return bytes(iterable)


@fromiter.register(dict)
def _dict_fromiter(self, iterable):
    new = self.copy()
    new.clear()
    new.update(zip(iterable, self.values()))
    return new


@fromiter.register(list)
def _list_fromiter(self, iterable):
    return list(iterable)


@fromiter.register(set)
def _set_fromiter(self, iterable):
    return set(iterable)


@fromiter.register(str)
def _str_fromiter(self, iterable):
    return ''.join(iterable)


@fromiter.register(tuple)
def _tuple_fromiter(self, iterable):
    # we need to use `type(self)` to handle namedtuples and perhaps
    # other subclasses
    return type(self)(iterable)
