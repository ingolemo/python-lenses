import functools

from .lens import Lens


class Unbound:
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __repr__(self):
        return '<_unbound>'

_unbound = Unbound()


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


def _valid_state(selfstate, argstate):
    states = selfstate is not _unbound, argstate is not _unbound
    if states == (False, False):
        raise ValueError('Lens is unbound and no state has been passed')
    elif states == (True, True):
        raise ValueError('Passed an state to an already bound Lens')
    elif states == (True, False):
        return selfstate
    elif states == (False, True):
        return argstate
    else:
        raise RuntimeError('Unreachable branch reached')


class UserLens(object):
    'A user-friendly object for interacting with the lenses library'
    __slots__ = ['state', 'lens']

    def __init__(self, state, sublens):
        self.state = _unbound if state is None else state
        self.lens = Lens.trivial() if sublens is None else sublens

    def __repr__(self):
        return '{}({!r}, {!r})'.format(self.__class__.__name__,
                                       self.state, self.lens)

    def get(self, state=_unbound):
        'Get the value in `state` or `self.state` focused by the lens.'
        state = _valid_state(self.state, state)
        return self.lens.get(state)

    def get_all(self, state=_unbound):
        '''Get multiple values in `state` or `self.state` focused by the
        lens. Returns them as a tuple.'''
        state = _valid_state(self.state, state)
        return self.lens.get_all(state)

    def set(self, newvalue, state=_unbound):
        '''Set the focus of `state` or `self.state` to `newvalue`.'''
        state = _valid_state(self.state, state)
        return self.lens.set(state, newvalue)

    def modify(self, func, state=_unbound):
        '''Apply a function to the focus of `state` or `self.state`.'''
        state = _valid_state(self.state, state)
        return self.lens.modify(state, func)

    def call_method(self, method_name, *args, state=_unbound, **kwargs):
        '''Call a method on the focus of `state` or `self.state`. The
        method must return a new value for the focus.'''
        def func(a):
            return getattr(a, method_name)(*args, **kwargs)
        return self.modify(func, state)

    def add_lens(self, new_lens):
        '''Refine the current focus of this lens by composing it with a
        `lenses.Lens` object.'''
        return UserLens(self.state, self.lens.compose(new_lens))

    def bind(self, state):
        '''Bind this lens to a specific `state`. Raises `ValueError`
        when the lens has already been bound.'''
        if self.state is not _unbound:
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
    from_getter_setter_ = _carry_lens(Lens.from_getter_setter)
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
