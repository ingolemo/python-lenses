import functools
import copy


def _rich_setter(self, kind, key, value):
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
    if kind == 'setitem':
        return tuple(value if i == key else item
                     for i, item in enumerate(self))
    elif kind == 'setattr':
        # probably a namedtuple
        return type(self)(*(value if field == key else item
                            for field, item in zip(self._fields, self)))


class Lens:
    'A no-frills lens class. serves as the backbone of the lenses library'

    def __init__(self, getter_func, setter_func):
        self._get = getter_func
        self._set = setter_func

    def __getattr__(self, name):
        return Lens(
            lambda item: getattr(self._get(item), name),
            lambda item, a: self._set(
                item,
                _rich_setter(self._get(item), 'setattr', name, a))
        )

    def __getitem__(self, name):
        return Lens(
            lambda item: self._get(item)[name],
            lambda item, a: self._set(
                item,
                _rich_setter(self._get(item), 'setitem', name, a))
        )
