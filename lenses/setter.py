import functools
import copy


def magic_set(self, kind, key, value):
    'A setter function that tries many different ways to set things'
    try:
        self.lens_setter
    except AttributeError:
        return setter(self, kind, key, value)
    else:
        return self.lens_setter(kind, key, value)


@functools.singledispatch
def setter(self, kind, key, value):
    '''returns a copy of self with key replaced by value.

    kind is either 'setitem' or 'setattr' depending on how the lens
    was accessed. The default approach is to make a copy of self and
    attempt to mutate the copy.
    '''
    selfcopy = copy.copy(self)
    if kind == 'setitem':
        selfcopy[key] = value
    elif kind == 'setattr':
        setattr(selfcopy, key, value)
    return selfcopy


@setter.register(tuple)
def _(self, kind, key, value):
    '''Handles setting items in tuples.

    Assumes that if we try to set an attribute on a tuple then it is
    actually a namedtuple.'''
    if kind == 'setitem':
        return tuple(value if i == key else item
                     for i, item in enumerate(self))
    elif kind == 'setattr':
        return type(self)(*(value if field == key else item
                            for field, item in zip(self._fields, self)))
