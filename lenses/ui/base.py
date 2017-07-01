from typing import (Any, Callable, Generic, Iterable, Optional, Type, cast)

import copy
import operator

from .. import optics
from ..maybe import Just
from ..typevars import S, T, A, B, X, Y


def _carry_binary_op(name):
    def operation(self, other):
        def modifier(focus):
            return getattr(operator, name)(focus, other)

        return self.modify(modifier)

    return operation, 'self.modify(operator.{}, other)'.format(name)


def _carry_reverse_op(name):
    opname = name.replace('__r', '__')

    def operation(self, other):
        def modifier(focus):
            return getattr(operator, opname)(other, focus)

        return self.modify(modifier)

    doc = 'self.modify(lambda s, o: operator.{}(o, s), other)'.format(opname)
    return operation, doc


def _carry_unary_op(name):
    def operation(self):
        def modifier(focus):
            return getattr(operator, name)(focus)

        return self.modify(modifier)

    return operation, 'self.modify(operator.{})'.format(name)


def _add_extra_methods(cls):
    # type: (Type[BaseUiLens]) -> Type[BaseUiLens]
    binary = '''__lt__ __le__ __eq__ __ne__ __gt__ __ge__
                __add__ __sub__ __mul__ __matmul__ __truediv__
                __floordiv__ __div__ __mod__ __divmod__ __pow__
                __lshift__ __rshift__ __xor__ __or__'''.split()
    reverse = '''__radd__ __rsub__ __rmul__ __rmatmul__ __rtruediv__
                 __rfloordiv__ __rdiv__ __rmod__ __rdivmod__ __rpow__
                 __rlshift__ __rrshift__ __rxor__ __ror__'''.split()
    unary = '__neg__ __pos__ __invert__'.split()

    funcs = [_carry_binary_op, _carry_reverse_op, _carry_unary_op]
    for func, dunders in zip(funcs, [binary, reverse, unary]):
        for dunder in dunders:
            operation, doc = func(dunder)
            operation.__name__ = dunder
            operation.__doc__ = doc
            setattr(cls, dunder, operation)

    return cls


@_add_extra_methods
class BaseUiLens(Generic[S, T, A, B]):
    '''This class contains all the methods that are common to both
    the BoundLens and UnboundLens classes. It is not intended to be
    instantiated directly.'''

    def call(self, method_name, *args, **kwargs):
        # type: (str, *Any, **Any) -> T
        '''Call a method on the focus. The method must return a new
        value for the focus.

            >>> from lenses import lens
            >>> lens[2].call('upper')(['alpha', 'beta', 'gamma'])
            ['alpha', 'beta', 'GAMMA']

        As a shortcut, you can include the name of the method you want
        to call immediately after `call_`:

            >>> lens[2].call_upper()(['alpha', 'beta', 'gamma'])
            ['alpha', 'beta', 'GAMMA']
        '''
        caller = operator.methodcaller(method_name, *args, **kwargs)
        return self.modify(caller)

    def call_mut(self, method_name, *args, **kwargs):
        # type: (str, *Any, **Any) -> T
        '''Call a method on the focus that will mutate it in place.
        Works by making a deep copy of the focus before calling the
        mutating method on it. The return value of that method is ignored.
        You can pass a keyword argument shallow=True to only make a
        shallow copy.

            >>> from lenses import lens
            >>> lens[0].call_mut('sort')([[3, 1, 2], [5, 4]])
            [[1, 2, 3], [5, 4]]

        As a shortcut, you can include the name of the method you want
        to call immediately after `call_mut_`:

            >>> lens[0].call_mut_sort()([[3, 1, 2], [5, 4]])
            [[1, 2, 3], [5, 4]]
        '''
        shallow = False
        if 'shallow' in kwargs:
            shallow = kwargs['shallow']
            del kwargs['shallow']

        def func(a):
            # type: (A) -> B
            a = copy.copy(a) if shallow else copy.deepcopy(a)
            getattr(a, method_name)(*args, **kwargs)
            return cast(B, a)

        return self.modify(func)

    def bitwise_and(self, other):
        # type: (Any) -> T
        '''Uses the bitwise and operator on the focus. A convenience
        method since lenses use __and__ for doing composition.

            >>> from lenses import lens
            >>> lens.each_().bitwise_and(5)([1, 2, 3, 4])
            [1, 0, 1, 4]
        '''

        def func(a):
            # type: (A) -> B
            return a & other

        return self.modify(func)

    def both_(self):
        # type: () -> BaseUiLens[S, T, X, Y]
        '''A traversal that focuses both items [0] and [1].

            >>> from lenses import lens
            >>> lens.both_()
            UnboundLens(BothTraversal())
            >>> lens.both_().collect()([1, 2, 3])
            [1, 2]
            >>> lens.both_().set(4)([1, 2, 3])
            [4, 4, 3]
        '''
        return self._compose_optic(optics.BothTraversal())

    def decode_(self, encoding='utf-8', errors='strict'):
        # type: (str, str) -> BaseUiLens[S, T, X, Y]
        '''An isomorphism that decodes and encodes its focus on the
        fly. Lets you focus a byte string as a unicode string. The
        arguments have the same meanings as `bytes.decode`. Analogous to
        `bytes.decode`.

            >>> from lenses import lens
            >>> lens.decode_(encoding='utf8')
            UnboundLens(DecodeIso('utf8', 'strict'))
            >>> lens.decode_().get()(b'hello')  # doctest: +SKIP
            'hello'
            >>> lens.decode_().set('world')(b'hello')  # doctest: +SKIP
            b'world'
        '''
        return self._compose_optic(optics.DecodeIso(encoding, errors))

    def each_(self):
        # type: () -> BaseUiLens[S, T, X, Y]
        '''A traversal that iterates over its state, focusing everything
        it iterates over. It uses `lenses.hooks.fromiter` to reform
        the state afterwards so it should work with any iterable that
        function supports. Analogous to `iter`.

            >>> from lenses import lens
            >>> data = [1, 2, 3]
            >>> lens.each_()
            UnboundLens(EachTraversal())
            >>> lens.each_().collect()(data)
            [1, 2, 3]
            >>> (lens.each_() + 1)(data)
            [2, 3, 4]

        For technical reasons, this lens iterates over dictionaries by
        their items and not just their keys.

            >>> data = {'one': 1}
            >>> lens.each_().collect()(data)
            [('one', 1)]
            >>> (lens.each_()[1] + 1)(data)
            {'one': 2}
        '''
        return self._compose_optic(optics.EachTraversal())

    def error_(self, exception, message=None):
        # type: (Exception, Optional[str]) -> BaseUiLens[S, T, X, Y]
        '''An optic that raises an exception whenever it tries to focus
        something. If `message is None` then the exception will be
        raised unmodified. If `message is not None` then when the lens
        is asked to focus something it will run `message.format(state)`
        and the exception will be called with the resulting formatted
        message as it's only argument. Useful for debugging.

            >>> from lenses import lens
            >>> lens.error_(Exception())
            UnboundLens(ErrorIso(Exception()))
            >>> lens.error_(Exception, '{}')
            UnboundLens(ErrorIso(<...Exception...>, '{}'))
            >>> lens.error_(Exception).get()(True)
            Traceback (most recent call last):
              File "<stdin>", line 1, in ?
            Exception
            >>> lens.error_(Exception('An error occurred')).set(False)(True)
            Traceback (most recent call last):
              File "<stdin>", line 1, in ?
            Exception: An error occurred
            >>> lens.error_(ValueError, 'applied to {}').get()(True)
            Traceback (most recent call last):
              File "<stdin>", line 1, in ?
            ValueError: applied to True
        '''
        return self._compose_optic(optics.ErrorIso(exception, message))

    def f_(self, getter):
        # type: (Callable[[A], X]) -> BaseUiLens[S, T, X, Y]
        '''An optic that wraps a getter function. A getter function is
        one that takes a state and returns a value derived from that
        state. The function is called on the focus before it is returned.

            >>> from lenses import lens
            >>> lens.f_(abs)
            UnboundLens(Getter(<built-in function abs>))
            >>> lens.f_(abs).get()(-1)
            1
            >>> lens.each_().f_(abs).collect()([-1, 2, -3])
            [1, 2, 3]

        This optic cannot be used to set or modify values.
        '''
        return self._compose_optic(optics.Getter(getter))

    def filter_(self, predicate):
        # type: (Callable[[A], bool]) -> BaseUiLens[S, T, X, Y]
        '''A prism that only focuses a value if the predicate returns
        `True` when called with that value as an argument. Best used
        when composed after a traversal. It only prevents the traversal
        from visiting foci, it does not filter out values the way that
        python's regular `filter` function does.

            >>> from lenses import lens
            >>> lens.filter_(all)
            UnboundLens(FilteringPrism(<built-in function all>))
            >>> data = [[1, 2], [0], ['a'], ['', 'b']]
            >>> lens.each_().filter_(all).collect()(data)
            [[1, 2], ['a']]
            >>> lens.each_().filter_(all).set(2)(data)
            [2, [0], 2, ['', 'b']]

        The filtering is done to foci before the lens' manipulation is
        applied. This means that the resulting foci can still violate
        the predicate if the manipulating function doesn't respect it:

            >>> lens.each_().filter_(bool).set(None)(['', 2, ''])
            ['', None, '']
        '''
        return self._compose_optic(optics.FilteringPrism(predicate))

    def fold_(self, func):
        # type: (Callable[[A], Iterable[X]]) -> BaseUiLens[S, T, X, Y]
        '''A fold that takes a function that returns an iterable and
        focuses all the values in that iterable.

            >>> from lenses import lens
            >>> def ends(state):
            ...     yield state[0]
            ...     yield state[-1]
            >>> lens.fold_(ends).collect()([1, 2, 3])
            [1, 3]
        '''
        return self._compose_optic(optics.Fold(func))

    def fork_(self, *lenses):
        # type: (*BaseUiLens[A, B, X, Y])-> BaseUiLens[S, T, X, Y]
        '''A setter representing the parallel composition of several
        sub-lenses.

            >>> from lenses import lens
            >>> lens.fork_(lens[0], lens[2])
            UnboundLens(ForkedSetter(GetitemLens(0), GetitemLens(2)))
            >>> lens.fork_(lens[0][1], lens[2]).set(1)([[0, 0], 0, 0])
            [[0, 1], 0, 1]
        '''
        true_lenses = [l._optic for l in lenses]
        return self._compose_optic(optics.ForkedSetter(*true_lenses))

    def get_(self, key, default=None):
        # type: (Any, Optional[Y]) -> BaseUiLens[S, T, X, Y]
        '''A lens that focuses an item inside a container by calling
        its `get` method, allowing you to specify a default value for
        missing keys.  Analogous to `dict.get`.

            >>> from lenses import lens
            >>> lens.get_('foo')
            UnboundLens(GetitemOrElseLens('foo', default=None))
            >>> lens.get_('baz').get()({'foo': 'bar'})
            >>> lens.get_('baz', []).get()({'foo': 'bar'})
            []
            >>> from collections import OrderedDict
            >>> lens.get_('baz').set('qux')(OrderedDict({'foo': 'bar'}))
            OrderedDict([('foo', 'bar'), ('baz', 'qux')])
        '''
        return self._compose_optic(optics.GetitemOrElseLens(key, default))

    def getattr_(self, name):
        # type: (str) -> BaseUiLens[S, T, X, Y]
        '''A lens that focuses an attribute of an object. Analogous to
        `getattr`.

            >>> from lenses import lens
            >>> from collections import namedtuple
            >>> Pair = namedtuple('Pair', 'left right')
            >>> lens.getattr_('left')
            UnboundLens(GetattrLens('left'))
            >>> lens.getattr_('left').get()(Pair(1, 2))
            1
            >>> lens.getattr_('right').set(3)(Pair(1, 2))
            Pair(left=1, right=3)
        '''
        return self._compose_optic(optics.GetattrLens(name))

    def getitem_(self, key):
        # type: (Any) -> BaseUiLens[S, T, X, Y]
        '''A lens that focuses an item inside a container. Analogous to
        `operator.itemgetter`.

            >>> from lenses import lens
            >>> lens[0]
            UnboundLens(GetitemLens(0))
            >>> lens.getitem_(0)
            UnboundLens(GetitemLens(0))
            >>> lens[0].get()([1, 2, 3])
            1
            >>> lens['hello'].get()({'hello': 'world'})
            'world'
            >>> lens[0].set(4)([1, 2, 3])
            [4, 2, 3]
            >>> lens['hello'].set('universe')({'hello': 'world'})
            {'hello': 'universe'}
        '''
        return self._compose_optic(optics.GetitemLens(key))

    def lens_(self, getter, setter):
        # type: (Callable[[A], X], Callable[[A, Y], B]) -> BaseUiLens[S, T, X, Y]
        '''An optic that wraps a pair of getter and setter functions. A
        getter function is one that takes a state and returns a value
        derived from that state. A setter function takes an old state
        and a new value and uses them to construct a new state.

            >>> from lenses import lens
            >>> def getter(state):
            ...     'Get the average of a list'
            ...     return sum(state) // len(state)
            ...
            >>> def setter(old_state, value):
            ...     'Set the average of a list by changing the final value'
            ...     target_sum = value * len(old_state)
            ...     prefix = old_state[:-1]
            ...     return prefix + [target_sum - sum(prefix)]
            ...
            >>> average_lens = lens.lens_(getter, setter)
            >>> average_lens
            UnboundLens(Lens(<function getter...>, <function setter...>))
            >>> average_lens.get()([1, 2, 4, 5])
            3
            >>> average_lens.set(4)([1, 2, 3])
            [1, 2, 9]
            >>> (average_lens - 1)([1, 2, 3])
            [1, 2, 0]
        '''
        return self._compose_optic(optics.Lens(getter, setter))

    def getzoomattr_(self, name):
        # type: (str) -> BaseUiLens[S, T, X, Y]
        '''A traversal that focuses an attribute of an object, though if
        that attribute happens to be a lens it will zoom the lens. This
        is used internally to make lenses that are attributes of objects
        transparent. If you already know whether you are focusing a lens
        or a non-lens you should be explicit and use a ZoomAttrTraversal
        or a GetAttrLens respectively.

            >>> from lenses import lens
            >>> from collections import namedtuple
            >>> Triple = namedtuple('Triple', 'left mid right')
            >>> state = Triple(1, 2, lens.mid)
            >>> lens.left
            UnboundLens(GetZoomAttrTraversal('left'))
            >>> lens.left.get()(state)
            1
            >>> lens.left.set(3)(state)
            Triple(left=3, mid=2, right=UnboundLens(GetZoomAttrTraversal('mid')))
            >>> lens.right.get()(state)
            2
            >>> lens.right.set(4)(state)
            Triple(left=1, mid=4, right=UnboundLens(GetZoomAttrTraversal('mid')))
        '''
        return self._compose_optic(optics.GetZoomAttrTraversal(name))

    def instance_(self, type_):
        # type: (Type) -> BaseUiLens[S, T, X, Y]
        '''A prism that focuses a value only when that value is an
        instance of `type_`.

            >>> from lenses import lens
            >>> lens.instance_(int)
            UnboundLens(InstancePrism(...))
            >>> lens.instance_(int).collect()(1)
            [1]
            >>> lens.instance_(float).collect()(1)
            []
            >>> lens.instance_(int).set(2)(1)
            2
            >>> lens.instance_(float).set(2)(1)
            1
        '''
        return self._compose_optic(optics.InstancePrism(type_))

    def iso_(self, forwards, backwards):
        # type: (Callable[[A], X], Callable[[Y], B]) -> BaseUiLens[S, T, X, Y]
        '''A lens based on an isomorphism. An isomorphism can be
        formed by two functions that mirror each other; they can convert
        forwards and backwards between a state and a focus without losing
        information. The difference between this and a regular Lens is
        that here the backwards functions don't need to know anything
        about the original state in order to produce a new state.

        These equalities should hold for the functions you supply (given
        a reasonable definition for __eq__):

            backwards(forwards(state)) == state
            forwards(backwards(focus)) == focus

        These kinds of conversion functions are very common across
        the python ecosystem. For example, NumPy has `np.array` and
        `np.ndarray.tolist` for converting between python lists and its
        own arrays. Isomorphism makes it easy to store data in one form,
        but interact with it in a more convenient form.

            >>> from lenses import lens
            >>> lens.iso_(chr, ord)
            UnboundLens(Isomorphism(<... chr>, <... ord>))
            >>> lens.iso_(chr, ord).get()(65)
            'A'
            >>> lens.iso_(chr, ord).set('B')(65)
            66

        Due to their symmetry, isomorphisms can be flipped, thereby
        swapping thier forwards and backwards functions:

            >>> flipped = lens.iso_(chr, ord).flip()
            >>> flipped
            UnboundLens(Isomorphism(<... ord>, <... chr>))
            >>> flipped.get()('A')
            65
        '''
        return self._compose_optic(optics.Isomorphism(forwards, backwards))

    def item_(self, key):
        # type: (Any) -> BaseUiLens[S, T, X, Y]
        '''A lens that focuses a single item (key-value pair) in a
        dictionary by its key. Set an item to `None` to remove it from
        the dictionary.

            >>> from lenses import lens
            >>> from collections import OrderedDict
            >>> data = OrderedDict([(1, 10), (2, 20)])
            >>> lens.item_(1)
            UnboundLens(ItemLens(1))
            >>> lens.item_(1).get()(data)
            (1, 10)
            >>> lens.item_(3).get()(data) is None
            True
            >>> lens.item_(1).set((1, 11))(data)
            OrderedDict([(1, 11), (2, 20)])
            >>> lens.item_(1).set(None)(data)
            OrderedDict([(2, 20)])
        '''
        return self._compose_optic(optics.ItemLens(key))

    def item_by_value_(self, value):
        # type: (Any) -> BaseUiLens[S, T, X, Y]
        '''A lens that focuses a single item (key-value pair) in a
        dictionary by its value. Set an item to `None` to remove it
        from the dictionary. This lens assumes that there will only be
        a single key with that particular value. If you violate that
        assumption then you're on your own.

            >>> from lenses import lens
            >>> from collections import OrderedDict
            >>> data = OrderedDict([(1, 10), (2, 20)])
            >>> lens.item_by_value_(10)
            UnboundLens(ItemByValueLens(10))
            >>> lens.item_by_value_(10).get()(data)
            (1, 10)
            >>> lens.item_by_value_(30).get()(data) is None
            True
            >>> lens.item_by_value_(10).set((3, 10))(data)
            OrderedDict([(2, 20), (3, 10)])
            >>> lens.item_by_value_(10).set(None)(data)
            OrderedDict([(2, 20)])
        '''
        return self._compose_optic(optics.ItemByValueLens(value))

    def items_(self):
        # type: () -> BaseUiLens[S, T, X, Y]
        '''A traversal focusing key-value tuples that are the items of
        a dictionary. Analogous to `dict.items`.

            >>> from lenses import lens
            >>> from collections import OrderedDict
            >>> data = OrderedDict([(1, 10), (2, 20)])
            >>> lens.items_()
            UnboundLens(ItemsTraversal())
            >>> lens.items_().collect()(data)
            [(1, 10), (2, 20)]
            >>> lens.items_()[1].modify(lambda n: n + 1)(data)
            OrderedDict([(1, 11), (2, 21)])
        '''
        return self._compose_optic(optics.ItemsTraversal())

    def iter_(self):
        # type: () -> BaseUiLens[S, T, X, Y]
        '''A fold that can get values from any iterable object in python
        by iterating over it. Like any fold, you cannot set values.

            >>> from lenses import lens
            >>> lens.iter_()
            UnboundLens(IterableFold())
            >>> lens.iter_().collect()({2, 1, 3})
            [1, 2, 3]
            >>> def numbers():
            ...     yield 1
            ...     yield 2
            ...     yield 3
            ...
            >>> lens.iter_().collect()(numbers())
            [1, 2, 3]
            >>> lens.iter_().collect()([])
            []

        If you want to be able to set values as you iterate then look
        into the EachTraversal.
        '''
        return self._compose_optic(optics.IterableFold())

    def json_(self):
        # type: () -> BaseUiLens[S, T, X, Y]
        '''An isomorphism that focuses a string containing json data as
        its parsed equivalent. Analogous to `json.loads`.

            >>> from lenses import lens
            >>> data = '[{"points": [4, 7]}]'
            >>> lens.json_()
            UnboundLens(JsonIso())
            >>> lens.json_()[0]['points'][1].get()(data)
            7
            >>> lens.json_()[0]['points'][0].set(8)(data)
            '[{"points": [8, 7]}]'
        '''
        return self._compose_optic(optics.JsonIso())

    def just_(self):
        # type: () -> BaseUiLens[S, T, X, Y]
        '''A prism that focuses the value inside a `lenses.maybe.Just`
        object.

            >>> from lenses import lens
            >>> from lenses.maybe import Just, Nothing
            >>> lens.just_()
            UnboundLens(JustPrism())
            >>> lens.just_().collect()(Just(1))
            [1]
            >>> lens.just_().collect()(Nothing())
            []
            >>> lens.just_().set(2)(Just(1))
            Just(2)
            >>> lens.just_().set(2)(Nothing())
            Nothing()
        '''
        return self._compose_optic(optics.JustPrism())

    def keys_(self):
        # type: () -> BaseUiLens[S, T, X, Y]
        '''A traversal focusing the keys of a dictionary. Analogous to
        `dict.keys`.

            >>> from lenses import lens
            >>> from collections import OrderedDict
            >>> data = OrderedDict([(1, 10), (2, 20)])
            >>> lens.keys_()
            UnboundLens(ItemsTraversal() & GetitemLens(0))
            >>> lens.keys_().collect()(data)
            [1, 2]
            >>> lens.keys_().modify(lambda n: n + 1)(data)
            OrderedDict([(2, 10), (3, 20)])
        '''
        return self._compose_optic(
            optics.ItemsTraversal() & optics.GetitemLens(0)
        )

    def listwrap_(self):
        # type: () -> BaseUiLens[S, T, X, Y]
        '''An isomorphism that wraps its state up in a list. This is
        occasionally useful when you need to make hetrogenous data more
        uniform. Analogous to `lambda state: [state]`.

            >>> from lenses import lens
            >>> lens.listwrap_()
            UnboundLens(ListWrapIso())
            >>> lens.listwrap_().get()(0)
            [0]
            >>> lens.listwrap_().set([1])(0)
            1
            >>> l = lens.tuple_(lens[0], lens[1].listwrap_())
            >>> l.each_().each_().collect()([[1, 3], 4])
            [1, 3, 4]

        Also serves as an example that lenses do not always have to
        'zoom in' on a focus; they can also 'zoom out'.
        '''
        return self._compose_optic(optics.ListWrapIso())

    def norm_(self, setter):
        # type: (Callable[[A], X]) -> BaseUiLens[S, T, X, Y]
        '''An isomorphism that applies a function as it sets a new
        focus without regard to the old state. It will get foci without
        transformation. This lens allows you to pre-process values before
        you set them, but still get values as they exist in the state.
        Useful for type conversions or normalising data.

        For best results, your normalisation function should be
        idempotent.  That is, applying the function twice should have
        no effect:

            setter(setter(value)) == setter(value)

        Equivalent to `Isomorphism((lambda s: s), setter)`.

            >>> from lenses import lens
            >>> def real_only(num):
            ...     return num.real
            ...
            >>> lens.norm_(real_only)
            UnboundLens(NormalisingIso(<function real_only at ...>))
            >>> lens[0].norm_(real_only).get()([1.0, 2.0, 3.0])
            1.0
            >>> lens[0].norm_(real_only).set(4+7j)([1.0, 2.0, 3.0])
            [4.0, 2.0, 3.0]

        Types with constructors that do conversion are often good targets
        for this lens:

            >>> lens[0].norm_(int).set(4.0)([1, 2, 3])
            [4, 2, 3]
            >>> lens[1].norm_(int).set('5')([1, 2, 3])
            [1, 5, 3]
        '''
        return self._compose_optic(optics.NormalisingIso(setter))

    def prism_(self, unpack, pack):
        # type: (Callable[[A], Just[X]], Callable[[Y], B]) -> BaseUiLens[S, T, X, Y]
        '''A prism is an optic made from a pair of functions that pack and
        unpack a state where the unpacking process can potentially fail.

        `pack` is a function that takes a focus and returns that focus
        wrapped up in a new state. `unpack` is a function that takes
        a state and unpacks it to get a focus. The unpack function
        must return an instance of `lenses.maybe.Maybe`; `Just` if the
        unpacking succeeded and `Nothing` if the unpacking failed.

        Parsing strings is a common situation when prisms are useful:

            >>> from lenses import lens
            >>> from lenses.maybe import Nothing, Just
            >>> def pack(focus):
            ...     return str(focus)
            ...
            >>> def unpack(state):
            ...     try:
            ...         return Just(int(state))
            ...     except ValueError:
            ...         return Nothing()
            ...
            >>> lens.prism_(unpack, pack)
            UnboundLens(Prism(<function unpack ...>, <function pack ...>))
            >>> lens.prism_(unpack, pack).collect()('42')
            [42]
            >>> lens.prism_(unpack, pack).collect()('fourty two')
            []

        All prisms are also traversals that have exactly zero or one foci.
        '''
        return self._compose_optic(optics.Prism(unpack, pack))

    def recur_(self, cls):
        '''A traversal that recurses through an object focusing everything it
        can find of a particular type. This traversal will probe arbitrarily
        deep into the contents of the state looking for sub-objects. It
        uses some naughty tricks to do this including looking at an object's
        `__dict__` attribute.

        It is somewhat analogous to haskell's uniplate optic.

            >>> from lenses import lens
            >>> lens.recur_(int)
            UnboundLens(RecurTraversal(<... 'int'>))
            >>> data = [[1, 2, 100.0], [3, 'hello', [{}, 4], 5]]
            >>> lens.recur_(int).collect()(data)
            [1, 2, 3, 4, 5]
            >>> (lens.recur_(int) + 1)(data)
            [[2, 3, 100.0], [4, 'hello', [{}, 5], 6]]

        It also works on custom classes:

            >>> class Container():
            ...     def __init__(self, contents):
            ...         self.contents = contents
            ...     def __repr__(self):
            ...         return 'Container({!r})'.format(self.contents)
            >>> data = [Container(1), 2, Container(Container(3)), [4, 5]]
            >>> (lens.recur_(int) + 1)(data)
            [Container(2), 3, Container(Container(4)), [5, 6]]
            >>> lens.recur_(Container).collect()(data)
            [Container(1), Container(Container(3))]

        Be careful with this; it can focus things you might not expect.
        '''
        return self._compose_optic(optics.RecurTraversal(cls))

    def tuple_(self, *lenses):
        # type: (*BaseUiLens[A, B, X, Y]) -> BaseUiLens[S, T, X, Y]
        '''A lens that combines the focuses of other lenses into a
        single tuple. The sublenses must be optics of kind Lens; this
        means no Traversals.

            >>> from lenses import lens
            >>> lens.tuple_()
            UnboundLens(TupleLens())
            >>> tl = lens.tuple_(lens[0], lens[2])
            >>> tl
            UnboundLens(TupleLens(GetitemLens(0), GetitemLens(2)))
            >>> tl.get()([1, 2, 3, 4])
            (1, 3)
            >>> tl.set((5, 6))([1, 2, 3, 4])
            [5, 2, 6, 4]

        This lens is particularly useful when immediately followed by
        an EachLens, allowing you to traverse data even when it comes
        from disparate locations within the state.

            >>> state = ([1, 2, 3], 4, [5, 6])
            >>> tl.each_().each_().collect()(state)
            [1, 2, 3, 5, 6]
            >>> (tl.each_().each_() + 10)(state)
            ([11, 12, 13], 4, [15, 16])
        '''
        true_lenses = [l._optic for l in lenses]
        return self._compose_optic(optics.TupleLens(*true_lenses))

    def values_(self):
        # type: () -> BaseUiLens[S, T, X, Y]
        '''A traversal focusing the values of a dictionary. Analogous to
        `dict.values`.

            >>> from lenses import lens
            >>> from collections import OrderedDict
            >>> data = OrderedDict([(1, 10), (2, 20)])
            >>> lens.values_()
            UnboundLens(ItemsTraversal() & GetitemLens(1))
            >>> lens.values_().collect()(data)
            [10, 20]
            >>> lens.values_().modify(lambda n: n + 1)(data)
            OrderedDict([(1, 11), (2, 21)])
        '''
        return self._compose_optic(
            optics.ItemsTraversal() & optics.GetitemLens(1)
        )

    def zoom_(self):
        # type: () -> BaseUiLens[S, T, X, Y]
        '''Follows its state as if it were a `BoundLens` object.

            >>> from lenses import lens, bind
            >>> data = [bind([1, 2])[1], 4]
            >>> lens.zoom_()
            UnboundLens(ZoomTraversal())
            >>> lens[0].zoom_().get()(data)
            2
            >>> lens[0].zoom_().set(3)(data)
            [[1, 3], 4]
        '''
        return self._compose_optic(optics.ZoomTraversal())

    def zoomattr_(self, name):
        # type: (str) -> BaseUiLens[S, T, X, Y]
        '''A lens that looks up an attribute on its target and follows
        it as if were a `BoundLens` object. Ignores the state, if any,
        of the lens that is being looked up.

            >>> from lenses import lens
            >>> class ClassWithLens(object):
            ...     def __init__(self, items):
            ...         self._private_items = items
            ...     def __repr__(self):
            ...         return 'ClassWithLens({!r})'.format(self._private_items)
            ...     first = lens._private_items[0]
            ...
            >>> data = (ClassWithLens([1, 2, 3]), 4)
            >>> lens.zoomattr_('first')
            UnboundLens(ZoomAttrTraversal('first'))
            >>> lens[0].zoomattr_('first').get()(data)
            1
            >>> lens[0].zoomattr_('first').set(5)(data)
            (ClassWithLens([5, 2, 3]), 4)
        '''
        return self._compose_optic(optics.ZoomAttrTraversal(name))

    def __getattr__(self, name):
        # type: (str) -> Any
        if name.endswith('_'):
            raise AttributeError('Not a valid lens constructor')

        if name.startswith('call_mut_'):

            def caller(*args, **kwargs):
                # type: (*Any, **Any) -> T
                return self.call_mut(name[9:], *args, **kwargs)

            return caller

        if name.startswith('call_'):

            def caller(*args, **kwargs):
                # type: (*Any, **Any) -> T
                return self.call(name[5:], *args, **kwargs)

            return caller

        return self.getzoomattr_(name)

    def __getitem__(self, name):
        # type: (Any) -> BaseUiLens[S, T, X, Y]
        return self.getitem_(name)
