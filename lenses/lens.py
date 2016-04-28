import functools

from . import baselens

lens_methods = [
    ('both_', baselens.BothLens),
    ('decode_', baselens.DecodeLens),
    ('error_', baselens.ErrorLens),
    ('each_', baselens.EachLens),
    ('filter_', baselens.FilteringLens),
    ('getattr_', baselens.GetattrLens),
    ('getitem_', baselens.GetitemLens),
    ('getter_', baselens.GetterLens),
    ('getter_setter_', baselens.GetterSetterLens),
    ('iso_', baselens.IsomorphismLens),
    ('item_', baselens.ItemLens),
    ('item_by_value_', baselens.ItemByValueLens),
    ('items_', baselens.ItemsLens),
    ('json_', baselens.JsonLens),
    ('keys_', baselens.KeysLens),
    ('norm_', baselens.NormalisingLens),
    ('setter_', baselens.SetterLens),
    ('traverse_', baselens.TraverseLens),
    ('trivial_', baselens.TrivialLens),
    ('tuple_', baselens.TupleLens),
    ('values_', baselens.ValuesLens),
    ('zoomattr_', baselens.ZoomAttrLens),
    ('zoom_', baselens.ZoomLens),
]


# we skip all the augmented artithmetic methods because the point of the
# lenses library is not to mutate anything
transparent_dunders = ('''
    __lt__ __le__ __eq__ __ne__ __gt__ __ge__

    __add__ __sub__ __mul__ __matmul__ __truediv__
    __floordiv__ __div__ __mod__ __divmod__ __pow__
    __lshift__ __rshift__ __and__ __xor__ __or__

    __radd__ __rsub__ __rmul__ __rmatmul__ __rtruediv__
    __rfloordiv__ __rdiv__ __rmod__ __rdivmod__ __rpow__
    __rlshift__ __rrshift__ __rand__ __rxor__ __ror__

    __neg__ __pos__ __invert__
''').split()


def _carry_op(name):
    def operation(self, *args, **kwargs):
        return self.modify(lambda a: getattr(a, name)(*args, **kwargs))

    doc = 'Equivalent to `self.modify(lambda a: a.{}(*args, **kwargs))`'
    operation.__name__ = name
    operation.__doc__ = doc.format(name)
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

    def __init__(self, state=None, lens=None):
        if lens is None:
            lens = baselens.TrivialLens()
        self.state = state
        self.lens = lens

    def __repr__(self):
        return '{}({!r}, {!r})'.format(self.__class__.__name__,
                                       self.state, self.lens)

    def _assert_bound(self, name):
        if self.state is None:
            raise ValueError('{} requires a bound lens'.format(name))

    def _assert_unbound(self, name):
        if self.state is not None:
            raise ValueError('{} requires an unbound lens'.format(name))

    def get(self, *, state=None):
        '''Get the first value focused by the lens.

            >>> from lenses import lens
            >>> lens([1, 2, 3]).get()
            [1, 2, 3]
            >>> lens([1, 2, 3])[0].get()
            1
        '''
        if state is not None:
            self = self.bind(state)
        self._assert_bound('Lens.get')
        return self.lens.get_all(self.state)[0]

    def get_all(self, *, state=None):
        '''Get multiple values focused by the lens. Returns them as a
        list.

            >>> from lenses import lens
            >>> lens([1, 2, 3])[0].get_all()
            [1]
            >>> lens([1, 2, 3]).both_().get_all()
            [1, 2]
        '''
        if state is not None:
            self = self.bind(state)
        self._assert_bound('Lens.get_all')
        return self.lens.get_all(self.state)

    def get_monoid(self, *, state=None):
        '''Get the values focused by the lens, merging them together by
        treating them as a monoid. See `lenses.typeclass.mappend`.

            >>> from lenses import lens
            >>> lens([[], [1], [2, 3]]).traverse_().get_monoid()
            [1, 2, 3]
        '''
        if state is not None:
            self = self.bind(state)
        self._assert_bound('Lens.get_monoid')
        return self.lens.get(self.state)

    def set(self, newvalue, *, state=None):
        '''Set the focus to `newvalue`.

            >>> from lenses import lens
            >>> lens([1, 2, 3])[1].set(4)
            [1, 4, 3]
        '''
        if state is not None:
            self = self.bind(state)
        self._assert_bound('Lens.set')
        return self.lens.set(self.state, newvalue)

    def modify(self, func, *, state=None):
        '''Apply a function to the focus.

            >>> from lenses import lens
            >>> lens([1, 2, 3])[1].modify(str)
            [1, '2', 3]
            >>> lens([1, 2, 3])[1].modify(lambda n: n + 10)
            [1, 12, 3]
        '''
        if state is not None:
            self = self.bind(state)
        self._assert_bound('Lens.modify')
        return self.lens.modify(self.state, func)

    def call(self, method_name, *args, state=None, **kwargs):
        '''Call a method on the focus. The method must return a new
        value for the focus.

            >>> from lenses import lens
            >>> lens(['alpha', 'beta', 'gamma'])[2].call('upper')
            ['alpha', 'beta', 'GAMMA']
        '''
        def func(a):
            return getattr(a, method_name)(*args, **kwargs)
        if state is not None:
            self = self.bind(state)
        return self.modify(func)

    def add_lens(self, other):
        '''Refine the current focus of this lens by composing it with
        another lens object. Can be a `lenses.LensLike` or an unbound
        `lenses.Lens`.

            >>> from lenses import lens
            >>> second_first = lens()[1][0]
            >>> lens([[0, 1], [2, 3]]).add_lens(second_first).get()
            2
        '''
        if isinstance(other, baselens.LensLike):
            return Lens(self.state, self.lens.compose(other))
        elif isinstance(other, Lens):
            other._assert_unbound('Lens.add_lens')
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
        self._assert_unbound('Lens.bind')
        return Lens(state, self.lens)

    def flip(self):
        '''Flips the direction of the lens. The lens must be unbound and
        all the underlying operations must be isomorphisms.

            >>> from lenses import lens
            >>> json_encoder = lens().decode_().json_().flip()
            >>> json_encoder.bind(['hello', 'world']).get()
            b'["hello", "world"]'
        '''
        self._assert_unbound('Lens.flip')
        return Lens(self.state, self.lens.flip())

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.bind(instance)

    def __getattr__(self, name):
        if name.endswith('_'):
            raise AttributeError('Not a valid lens constructor')

        if name.endswith('_l'):
            return self.add_lens(baselens.ZoomAttrLens(name[:-2]))

        if name.endswith('_m'):
            def caller(*args, **kwargs):
                return self.call(name[:-2], *args, **kwargs)
            return caller

        return self.add_lens(baselens.GetattrLens(name))

    def __getitem__(self, name):
        return self.add_lens(baselens.GetitemLens(name))

    def _underlying_lens(self):
        return self.lens
