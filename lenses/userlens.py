from .lens import Lens, _is_lens_constructor

_guard = object()


def _carry_op(name):
    def operation(self, *args, **kwargs):
        return self.modify(lambda a: getattr(a, name)(*args, **kwargs))

    operation.__name__ = name
    return operation


def _valid_item(selfitem, argitem):
    items = selfitem is not _guard, argitem is not _guard
    if items == (False, False):
        raise ValueError('Lens is unbound and no item has been passed')
    elif items == (True, True):
        raise ValueError('Passed an item to an already bound Lens')
    elif items == (True, False):
        return selfitem
    elif items == (False, True):
        return argitem
    else:
        raise RuntimeError('Unreachable branch reached')


class UserLens(object):
    'A user-friendly object for interacting with the lenses library'
    __slots__ = ['item', 'lens']

    def __init__(self, item, sublens):
        self.item = _guard if item is None else item
        self.lens = Lens.trivial() if sublens is None else sublens

    def __repr__(self):
        return '{}({!r}, {!r})'.format(self.__class__.__name__, self.item,
                                       self.lens)

    def get(self, item=_guard):
        'get the item via the lens'
        item = _valid_item(self.item, item)
        return self.lens.get(item)

    def get_all(self, item=_guard):
        'get all items via the lens'
        item = _valid_item(self.item, item)
        return self.lens.get_all(item)

    def set(self, newvalue, item=_guard):
        'set the item via the lens'
        item = _valid_item(self.item, item)
        return self.lens.set(item, newvalue)

    def modify(self, func, item=_guard):
        'apply a function to the item via the lens'
        item = _valid_item(self.item, item)
        return self.lens.modify(item, func)

    def call_method(self, method_name, *args, item=_guard, **kwargs):
        '''call a method on the item via the lens.

        the method should return a new item.'''
        method = getattr(self.get(item), method_name)
        return self.set(method(*args, **kwargs), item)

    def add_lens(self, new_lens):
        'compose the internal lens with an extra lens'
        return UserLens(self.item, self.lens.compose(new_lens))

    def bind(self, item):
        if self.item is not _guard:
            raise ValueError('Trying to bind an already bound lens')
        return UserLens(item, self.lens)

    def __getattr__(self, name):
        if not name.endswith('_'):
            return self.add_lens(Lens.getattr(name))

        constructor = getattr(Lens, name[:-1])
        if not _is_lens_constructor(constructor):
            raise AttributeError('Not a valid lens constructor')

        def _(*args, **kwargs):
            return self.add_lens(constructor(*args, **kwargs))
        return _

    def __getitem__(self, name):
        return self.add_lens(Lens.getitem(name))

    # __new__
    # __init__
    # __del__
    # __repr__
    __str__ = _carry_op('__str__')
    __bytes__ = _carry_op('__bytes__')
    __format__ = _carry_op('__format__')
    __lt__ = _carry_op('__lt__')
    __le__ = _carry_op('__le__')
    __eq__ = _carry_op('__eq__')
    __ne__ = _carry_op('__ne__')
    __gt__ = _carry_op('__gt__')
    __ge__ = _carry_op('__ge__')
    # __hash__
    __bool__ = _carry_op('__bool__')
    # __getattr__
    # __getattribute__
    # __setattr__
    # __delattr__
    # __dir__
    # __get__
    # __set__
    # __delete__
    # __slots__
    # __instancecheck__
    # __subclasscheck__
    # __call__
    # __len__
    # __length_hint__
    # __getitem__
    # __missing__
    # __setitem__
    # __delitem__
    # __iter__
    # __next__
    # __reversed__
    # __contains__
    __add__ = _carry_op('__add__')
    __sub__ = _carry_op('__sub__')
    __mul__ = _carry_op('__mul__')
    __matmul__ = _carry_op('__matmul__')
    __truediv__ = _carry_op('__truediv__')
    __floordiv__ = _carry_op('__floordiv__')
    __div__ = _carry_op('__div__')  # python 2
    __mod__ = _carry_op('__mod__')
    __divmod__ = _carry_op('__divmod__')
    __pow__ = _carry_op('__pow__')
    __lshift__ = _carry_op('__lshift__')
    __rshift__ = _carry_op('__rshift__')
    __and__ = _carry_op('__and__')
    __xor__ = _carry_op('__xor__')
    __or__ = _carry_op('__or__')
    __radd__ = _carry_op('__radd__')
    __rsub__ = _carry_op('__rsub__')
    __rmul__ = _carry_op('__rmul__')
    __rmatmul__ = _carry_op('__rmatmul__')
    __rtruediv__ = _carry_op('__rtruediv__')
    __rfloordiv__ = _carry_op('__rfloordiv__')
    __rdiv__ = _carry_op('__rdiv__')  # python2
    __rmod__ = _carry_op('__rmod__')
    __rdivmod__ = _carry_op('__rdivmod__')
    __rpow__ = _carry_op('__rpow__')
    __rlshift__ = _carry_op('__rlshift__')
    __rrshift__ = _carry_op('__rrshift__')
    __rand__ = _carry_op('__rand__')
    __rxor__ = _carry_op('__rxor__')
    __ror__ = _carry_op('__ror__')
    # we skip all the augmented artithmetic methods because the point of the
    # lenses library is not to mutate anything
    __neg__ = _carry_op('__neg__')
    __pos__ = _carry_op('__pos__')
    __abs__ = _carry_op('__abs__')
    __invert__ = _carry_op('__invert__')
    __complex__ = _carry_op('__complex__')
    __int__ = _carry_op('__int__')
    __long__ = _carry_op('__long__')  # python2
    __float__ = _carry_op('__float__')
    __round__ = _carry_op('__round__')
    __index__ = _carry_op('__index__')
    # __enter__
    # __exit__
    # __await__
    # __aiter__
    # __anext__
    # __aenter__
    # __aexit__
