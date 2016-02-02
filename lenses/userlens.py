import functools

from .lens import Lens


def _carry_op(name):
    def operation(self, *args, **kwargs):
        return self.modify(lambda a: getattr(a, name)(*args, **kwargs))

    operation.__name__ = name
    return operation


def _carry_lens(method):
    @functools.wraps(method)
    def _(self, *args, **kwargs):
        lens = method(*args, **kwargs)
        return self.add_lens(lens)
    return _


class UserLens(object):
    'A user-friendly object for interacting with the lenses library'
    __slots__ = ['state', 'lens']

    def __init__(self, state, sublens):
        self.state = state
        self.lens = Lens.trivial() if sublens is None else sublens

    def __repr__(self):
        return '{}({!r}, {!r})'.format(self.__class__.__name__,
                                       self.state, self.lens)

    def _assert_state(self):
        if self.state is None:
            raise ValueError('Operation requires a bound lens')

    def get(self):
        'Get the value focused by the lens.'
        self._assert_state()
        return self.lens.get(self.state)

    def get_all(self):
        '''Get multiple values focused by the lens. Returns them as a
        tuple.'''
        self._assert_state()
        return self.lens.get_all(self.state)

    def set(self, newvalue):
        '''Set the focus to `newvalue`.'''
        self._assert_state()
        return self.lens.set(self.state, newvalue)

    def modify(self, func):
        '''Apply a function to the focus.'''
        self._assert_state()
        return self.lens.modify(self.state, func)

    def call_method(self, method_name, *args, **kwargs):
        '''Call a method on the focus. The method must return a new
        value for the focus.'''
        def func(a):
            return getattr(a, method_name)(*args, **kwargs)
        return self.modify(func)

    def add_lens(self, other):
        '''Refine the current focus of this lens by composing it with
        another lens object. Can be a `lenses.Lens` or an unbound
        `lenses.UserLens`.'''
        if isinstance(other, Lens):
            return UserLens(self.state, self.lens.compose(other))
        elif isinstance(other, UserLens):
            if other.state is not None:
                raise ValueError('Other lens has a state bound to it.')
            return UserLens(self.state, self.lens.compose(other.lens))
        else:
            raise TypeError('''Cannot add lens of type {!r}.'''
                            .format(type(other)))

    def bind(self, state):
        '''Bind this lens to a specific `state`. Raises `ValueError`
        when the lens has already been bound.'''
        if self.state is not None:
            raise ValueError('Trying to bind an already bound lens')
        return UserLens(state, self.lens)

    def __getattr__(self, name):
        if name.endswith('_'):
            raise AttributeError('Not a valid lens constructor')
        return self.add_lens(Lens.getattr(name))

    def __getitem__(self, name):
        return self.add_lens(Lens.getitem(name))

    both_ = _carry_lens(Lens.both)
    decode_ = _carry_lens(Lens.decode)
    getter_setter_ = _carry_lens(Lens.from_getter_setter)
    getattr_ = _carry_lens(Lens.getattr)
    getitem_ = _carry_lens(Lens.getitem)
    item_ = _carry_lens(Lens.item)
    item_by_value_ = _carry_lens(Lens.item_by_value)
    items_ = _carry_lens(Lens.item)
    traverse_ = _carry_lens(Lens.traverse)
    trivial_ = _carry_lens(Lens.trivial)
    tuple_ = _carry_lens(Lens.tuple)

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
