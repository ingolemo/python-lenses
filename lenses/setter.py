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
