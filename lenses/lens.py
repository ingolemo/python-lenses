import functools

from . import baselens

lens_methods = [
    ('both_', baselens.BothLens),
    ('decode_', baselens.DecodeLens),
    ('error_', baselens.ErrorLens),
    ('filter_', baselens.FilteringLens),
    ('getattr_', baselens.GetattrLens),
    ('getitem_', baselens.GetitemLens),
    ('getter_setter_', baselens.GetterSetterLens),
    ('item_', baselens.ItemLens),
    ('item_by_value_', baselens.ItemByValueLens),
    ('items_', baselens.ItemsLens),
    ('json_', baselens.JsonLens),
    ('keys_', baselens.KeysLens),
    ('traverse_', baselens.TraverseLens),
    ('trivial_', baselens.TrivialLens),
    ('tuple_', baselens.TupleLens),
    ('values_', baselens.ValuesLens),
    ('zoomattr_', baselens.ZoomAttrLens),
    ('zoom_', baselens.ZoomLens),
]

transparent_dunders = [
    # '__new__', '__init__', '__del__', '__repr__', '__str__',
    # '__bytes__', '__format__',

    '__lt__', '__le__', '__eq__', '__ne__', '__gt__', '__ge__',

    # '__hash__',

    '__bool__',

    # '__getattr__', '__getattribute__', '__setattr__', '__delattr__',
    # '__dir__',
    # '__get__', '__set__', '__delete__',
    # '__slots__',
    # '__instancecheck__', '__subclasscheck__',
    # '__call__',
    # '__len__', '__length_hint__',
    # '__getitem__', '__missing__', '__setitem__', '__delitem__',
    # '__iter__', '__next__', '__reversed__',
    # '__contains__',

    '__add__', '__sub__', '__mul__', '__matmul__', '__truediv__',
    '__floordiv__', '__div__', '__mod__', '__divmod__', '__pow__',
    '__lshift__', '__rshift__', '__and__', '__xor__', '__or__',

    '__radd__', '__rsub__', '__rmul__', '__rmatmul__', '__rtruediv__',
    '__rfloordiv__', '__rdiv__', '__rmod__', '__rdivmod__', '__rpow__',
    '__rlshift__', '__rrshift__', '__rand__', '__rxor__', '__ror__',

    # we skip all the augmented artithmetic methods because the point of the
    # lenses library is not to mutate anything
    '__neg__', '__pos__', '__abs__', '__invert__', '__complex__', '__int__',
    '__long__', '__float__', '__round__', '__index__',

    # '__enter__', '__exit__', '__await__', '__aiter__', '__anext__',
    # '__aenter__', '__aexit__',
]


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


def _add_extra_methods(cls):
    for dunder in transparent_dunders:
        setattr(cls, dunder, _carry_op(dunder))

    for name, lens in lens_methods:
        setattr(cls, name, _carry_lens(lens))

    return cls


@_add_extra_methods
class Lens(object):
    'A user-friendly object for interacting with the lenses library'
    __slots__ = ['state', 'lens']

    def __init__(self, state, sublens=None):
        self.state = state
        self.lens = baselens.TrivialLens() if sublens is None else sublens

    def __repr__(self):
        return '{}({!r}, {!r})'.format(self.__class__.__name__,
                                       self.state, self.lens)

    def _assert_state(self):
        if self.state is None:
            raise ValueError('Operation requires a bound lens')

    def get(self):
        '''Get the first value focused by the lens.

            >>> from lenses import lens
            >>> lens([1, 2, 3]).get()
            [1, 2, 3]
            >>> lens([1, 2, 3])[0].get()
            1
        '''
        self._assert_state()
        return self.lens.get_all(self.state)[0]

    def get_all(self):
        '''Get multiple values focused by the lens. Returns them as a
        tuple.

            >>> from lenses import lens
            >>> lens([1, 2, 3])[0].get_all()
            (1,)
            >>> lens([1, 2, 3]).both_().get_all()
            (1, 2)
        '''
        self._assert_state()
        return self.lens.get_all(self.state)

    def get_monoid(self):
        '''Get the values focused by the lens, merging them together by
        treating them as a monoid. See `lenses.typeclass.mappend`.

            >>> from lenses import lens
            >>> lens([[], [1], [2, 3]]).traverse_().get_monoid()
            [1, 2, 3]
        '''
        self._assert_state()
        return self.lens.get(self.state)

    def set(self, newvalue):
        '''Set the focus to `newvalue`.

            >>> from lenses import lens
            >>> lens([1, 2, 3])[1].set(4)
            [1, 4, 3]
        '''
        self._assert_state()
        return self.lens.set(self.state, newvalue)

    def modify(self, func):
        '''Apply a function to the focus.

            >>> from lenses import lens
            >>> lens([1, 2, 3])[1].modify(str)
            [1, '2', 3]
            >>> lens([1, 2, 3])[1].modify(lambda n: n + 10)
            [1, 12, 3]
        '''
        self._assert_state()
        return self.lens.modify(self.state, func)

    def call(self, method_name, *args, **kwargs):
        '''Call a method on the focus. The method must return a new
        value for the focus.

            >>> from lenses import lens
            >>> lens(['alpha', 'beta', 'gamma'])[2].call('upper')
            ['alpha', 'beta', 'GAMMA']
        '''
        def func(a):
            return getattr(a, method_name)(*args, **kwargs)
        return self.modify(func)

    def add_lens(self, other):
        '''Refine the current focus of this lens by composing it with
        another lens object. Can be a `lenses.BaseLens` or an unbound
        `lenses.Lens`.

            >>> from lenses import lens
            >>> second_first = lens()[1][0]
            >>> lens([[0, 1], [2, 3]]).add_lens(second_first).get()
            2
        '''
        if isinstance(other, baselens.BaseLens):
            return Lens(self.state, self.lens.compose(other))
        elif isinstance(other, Lens):
            if other.state is not None:
                raise ValueError('Other lens has a state bound to it.')
            return Lens(self.state, self.lens.compose(other.lens))
        else:
            raise TypeError('''Cannot add lens of type {!r}.'''
                            .format(type(other)))

    def bind(self, state):
        '''Bind this lens to a specific `state`. Raises `ValueError`
        when the lens has already been bound.

            >>> from lenses import lens
            >>> lens()[1].bind([1, 2, 3]).get()
            2
        '''
        if self.state is not None:
            raise ValueError('Trying to bind an already bound lens')
        return Lens(state, self.lens)

    def __get__(self, obj, type=None):
        return self.bind(obj)

    def __getattr__(self, name):
        if name.endswith('_'):
            raise AttributeError('Not a valid lens constructor')

        if name.endswith('_l'):
            return self.add_lens(baselens.ZoomAttrLens(name[:-2]))

        return self.add_lens(baselens.GetattrLens(name))

    def __getitem__(self, name):
        return self.add_lens(baselens.GetitemLens(name))
