from functools import singledispatch
import copy


@singledispatch
def setitem_immutable(self, key, value):
    '''Takes an object, a key, and a value and produces a new object
    that is a copy of the original but with `value` as the new value of
    `key`.

        setitem_immutable(obj, key, obj[key]) == obj
    '''
    try:
        self._lens_setitem
    except AttributeError:
        selfcopy = copy.copy(self)
        selfcopy[key] = value
        return selfcopy
    else:
        return self._lens_setitem(key, value)


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

        fromiter(obj, iter(obj)) == obj
    '''
    try:
        self._lens_fromiter
    except AttributeError:
        message = 'Don\'t know how to create instance of {} from iterable'
        raise NotImplementedError(message.format(type(self)))
    else:
        return self._lens_fromiter(iterable)


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
