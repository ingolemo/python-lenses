from typing import Any, Callable, Generic, Iterable, Optional, Type, TypeVar, cast

import copy
import functools
import operator

from .. import optics
from ..maybe import Just as mJust, Nothing as mNothing

S = TypeVar("S")
T = TypeVar("T")
A = TypeVar("A")
B = TypeVar("B")
X = TypeVar("X")
Y = TypeVar("Y")


def _carry_binary_op(name):
    def operation(self, other):
        def modifier(focus):
            return getattr(operator, name)(focus, other)

        return self.modify(modifier)

    return operation, "self.modify(operator.{}, other)".format(name)


def _carry_reverse_op(name):
    opname = name.replace("__r", "__")

    def operation(self, other):
        def modifier(focus):
            return getattr(operator, opname)(other, focus)

        return self.modify(modifier)

    doc = "self.modify(lambda s, o: operator.{}(o, s), other)".format(opname)
    return operation, doc


def _carry_unary_op(name):
    def operation(self):
        def modifier(focus):
            return getattr(operator, name)(focus)

        return self.modify(modifier)

    return operation, "self.modify(operator.{})".format(name)


def _add_extra_methods(cls: Type["BaseUiLens"]) -> Type["BaseUiLens"]:
    binary = """__lt__ __le__ __eq__ __ne__ __gt__ __ge__
                __add__ __sub__ __mul__ __matmul__ __truediv__
                __floordiv__ __div__ __mod__ __divmod__ __pow__
                __lshift__ __rshift__ __xor__ __or__""".split()
    reverse = """__radd__ __rsub__ __rmul__ __rmatmul__ __rtruediv__
                 __rfloordiv__ __rdiv__ __rmod__ __rdivmod__ __rpow__
                 __rlshift__ __rrshift__ __rxor__ __ror__""".split()
    unary = "__neg__ __pos__ __invert__".split()

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
    """This class contains all the methods that are common to both
    the BoundLens and UnboundLens classes. It is not intended to be
    instantiated directly."""

    __slots__ = ()

    def call(self, method_name: str, *args: Any, **kwargs: Any) -> T:
        """Call a method on the focus. The method must return a new
        value for the focus.

            >>> from lenses import lens
            >>> lens[2].call('upper')(['alpha', 'beta', 'gamma'])
            ['alpha', 'beta', 'GAMMA']

        As a shortcut, you can include the name of the method you want
        to call immediately after `call_`:

            >>> lens[2].call_upper()(['alpha', 'beta', 'gamma'])
            ['alpha', 'beta', 'GAMMA']
        """
        caller = operator.methodcaller(method_name, *args, **kwargs)
        return self.modify(caller)

    def call_mut(self, method_name: str, *args: Any, **kwargs: Any) -> T:
        """Call a method on the focus that will mutate it in place.
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
        """
        shallow = False
        if "shallow" in kwargs:
            shallow = kwargs["shallow"]
            del kwargs["shallow"]

        def func(a: A) -> B:
            a = copy.copy(a) if shallow else copy.deepcopy(a)
            getattr(a, method_name)(*args, **kwargs)
            return cast(B, a)

        return self.modify(func)

    def bitwise_and(self, other: Any) -> T:
        """Uses the bitwise and operator on the focus. A convenience
        method since lenses use __and__ for doing composition.

            >>> from lenses import lens
            >>> lens.Each().bitwise_and(5)([1, 2, 3, 4])
            [1, 0, 1, 4]
        """

        def func(a: A) -> B:
            return a & other

        return self.modify(func)

    def Contains(self, item: A) -> "BaseUiLens[S, S, bool, bool]":
        """A lens that focuses a boolean that tells you whether the
        state contains some item.

            >>> from lenses import lens
            >>> lens.Contains(1)
            UnboundLens(ContainsLens(1))
            >>> lens.Contains(1).get()([2, 3])
            False
            >>> lens.Contains(1).get()([1, 2, 3])
            True
            >>> lens.Contains(1).set(False)([1, 2, 3])
            [2, 3]
            >>> lens.Contains(1).set(True)([2, 3])
            [2, 3, 1]

        The behaviour of this lens depends on the implementation of
        ``lenses.hooks.contains_add`` and ``lenses.hooks.contains_remove``.
        """
        return self._compose_optic(optics.ContainsLens(item))

    def Decode(
        self, encoding: str = "utf-8", errors: str = "strict"
    ) -> "BaseUiLens[S, T, bytes, str]":
        """An isomorphism that decodes and encodes its focus on the
        fly. Lets you focus a byte string as a unicode string. The
        arguments have the same meanings as `bytes.decode`. Analogous to
        `bytes.decode`.

            >>> from lenses import lens
            >>> lens.Decode(encoding='utf8')
            UnboundLens(DecodeIso('utf8', 'strict'))
            >>> lens.Decode().get()(b'hello')  # doctest: +SKIP
            'hello'
            >>> lens.Decode().set('world')(b'hello')  # doctest: +SKIP
            b'world'
        """
        return self._compose_optic(optics.DecodeIso(encoding, errors))

    def Each(self) -> "BaseUiLens[S, T, X, Y]":
        """A traversal that iterates over its state, focusing everything
        it iterates over. It uses `lenses.hooks.fromiter` to reform
        the state afterwards so it should work with any iterable that
        function supports. Analogous to `iter`.

            >>> from lenses import lens
            >>> data = [1, 2, 3]
            >>> lens.Each()
            UnboundLens(EachTraversal())
            >>> lens.Each().collect()(data)
            [1, 2, 3]
            >>> (lens.Each() + 1)(data)
            [2, 3, 4]

        For technical reasons, this lens iterates over dictionaries by
        their items and not just their keys.

            >>> data = {'one': 1}
            >>> lens.Each().collect()(data)
            [('one', 1)]
            >>> (lens.Each()[1] + 1)(data)
            {'one': 2}
        """
        return self._compose_optic(optics.EachTraversal())

    def Error(
        self, exception: Exception, message: Optional[str] = None
    ) -> "BaseUiLens[S, T, X, Y]":
        """An optic that raises an exception whenever it tries to focus
        something. If `message is None` then the exception will be
        raised unmodified. If `message is not None` then when the lens
        is asked to focus something it will run `message.format(state)`
        and the exception will be called with the resulting formatted
        message as it's only argument. Useful for debugging.

            >>> from lenses import lens
            >>> lens.Error(Exception())
            UnboundLens(ErrorIso(Exception()))
            >>> lens.Error(Exception, '{}')
            UnboundLens(ErrorIso(<...Exception...>, '{}'))
            >>> lens.Error(Exception).get()(True)
            Traceback (most recent call last):
              File "<stdin>", line 1, in ?
            Exception
            >>> lens.Error(Exception('An error occurred')).set(False)(True)
            Traceback (most recent call last):
              File "<stdin>", line 1, in ?
            Exception: An error occurred
            >>> lens.Error(ValueError, 'applied to {}').get()(True)
            Traceback (most recent call last):
              File "<stdin>", line 1, in ?
            ValueError: applied to True
        """
        return self._compose_optic(optics.ErrorIso(exception, message))

    def F(self, getter: Callable[[A], X]) -> "BaseUiLens[S, T, X, Y]":
        """An optic that wraps a getter function. A getter function is
        one that takes a state and returns a value derived from that
        state. The function is called on the focus before it is returned.

            >>> from lenses import lens
            >>> lens.F(abs)
            UnboundLens(Getter(<built-in function abs>))
            >>> lens.F(abs).get()(-1)
            1
            >>> lens.Each().F(abs).collect()([-1, 2, -3])
            [1, 2, 3]

        This optic cannot be used to set or modify values.
        """
        return self._compose_optic(optics.Getter(getter))

    def Filter(self, predicate: Callable[[A], bool]) -> "BaseUiLens[S, T, X, Y]":
        """A prism that only focuses a value if the predicate returns
        `True` when called with that value as an argument. Best used
        when composed after a traversal. It only prevents the traversal
        from visiting foci, it does not filter out values the way that
        python's regular `filter` function does.

            >>> from lenses import lens
            >>> lens.Filter(all)
            UnboundLens(FilteringPrism(<built-in function all>))
            >>> data = [[1, 2], [0], ['a'], ['', 'b']]
            >>> lens.Each().Filter(all).collect()(data)
            [[1, 2], ['a']]
            >>> lens.Each().Filter(all).set(2)(data)
            [2, [0], 2, ['', 'b']]

        The filtering is done to foci before the lens' manipulation is
        applied. This means that the resulting foci can still violate
        the predicate if the manipulating function doesn't respect it:

            >>> lens.Each().Filter(bool).set(None)(['', 2, ''])
            ['', None, '']
        """
        return self._compose_optic(optics.FilteringPrism(predicate))

    def Fold(self, func: Callable[[A], Iterable[X]]) -> "BaseUiLens[S, T, X, Y]":
        """A fold that takes a function that returns an iterable and
        focuses all the values in that iterable.

            >>> from lenses import lens
            >>> def ends(state):
            ...     yield state[0]
            ...     yield state[-1]
            >>> lens.Fold(ends).collect()([1, 2, 3])
            [1, 3]
        """
        return self._compose_optic(optics.Fold(func))

    def Fork(self, *lenses: "BaseUiLens[A, B, X, Y]") -> "BaseUiLens[S, T, X, Y]":
        """A setter representing the parallel composition of several
        sub-lenses.

            >>> from lenses import lens
            >>> lens.Fork(lens[0], lens[2])
            UnboundLens(ForkedSetter(GetitemLens(0), GetitemLens(2)))
            >>> lens.Fork(lens[0][1], lens[2]).set(1)([[0, 0], 0, 0])
            [[0, 1], 0, 1]
        """
        true_lenses = [l._optic for l in lenses]
        return self._compose_optic(optics.ForkedSetter(*true_lenses))

    def Get(self, key: Any, default: Optional[Y] = None) -> "BaseUiLens[S, T, X, Y]":
        """A lens that focuses an item inside a container by calling
        its `get` method, allowing you to specify a default value for
        missing keys.  Analogous to `dict.get`.

            >>> from lenses import lens
            >>> lens.Get('foo')
            UnboundLens(GetitemOrElseLens('foo', default=None))
            >>> lens.Get('baz').get()({'foo': 'bar'})
            >>> lens.Get('baz', []).get()({'foo': 'bar'})
            []
            >>> from collections import OrderedDict
            >>> lens.Get('baz').set('qux')(OrderedDict({'foo': 'bar'}))
            OrderedDict([('foo', 'bar'), ('baz', 'qux')])
        """
        return self._compose_optic(optics.GetitemOrElseLens(key, default))

    def GetAttr(self, name: str) -> "BaseUiLens[S, T, X, Y]":
        """A lens that focuses an attribute of an object. Analogous to
        `getattr`.

            >>> from lenses import lens
            >>> from collections import namedtuple
            >>> Pair = namedtuple('Pair', 'left right')
            >>> lens.GetAttr('left')
            UnboundLens(GetattrLens('left'))
            >>> lens.GetAttr('left').get()(Pair(1, 2))
            1
            >>> lens.GetAttr('right').set(3)(Pair(1, 2))
            Pair(left=1, right=3)
        """
        return self._compose_optic(optics.GetattrLens(name))

    def GetItem(self, key: Any) -> "BaseUiLens[S, T, X, Y]":
        """A lens that focuses an item inside a container. Analogous to
        `operator.itemgetter`.

            >>> from lenses import lens
            >>> lens[0]
            UnboundLens(GetitemLens(0))
            >>> lens.GetItem(0)
            UnboundLens(GetitemLens(0))
            >>> lens[0].get()([1, 2, 3])
            1
            >>> lens['hello'].get()({'hello': 'world'})
            'world'
            >>> lens[0].set(4)([1, 2, 3])
            [4, 2, 3]
            >>> lens['hello'].set('universe')({'hello': 'world'})
            {'hello': 'universe'}
        """
        return self._compose_optic(optics.GetitemLens(key))

    def Lens(
        self, getter: Callable[[A], X], setter: Callable[[A, Y], B]
    ) -> "BaseUiLens[S, T, X, Y]":
        """An optic that wraps a pair of getter and setter functions. A
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
            >>> average_lens = lens.Lens(getter, setter)
            >>> average_lens
            UnboundLens(Lens(<function getter...>, <function setter...>))
            >>> average_lens.get()([1, 2, 4, 5])
            3
            >>> average_lens.set(4)([1, 2, 3])
            [1, 2, 9]
            >>> (average_lens - 1)([1, 2, 3])
            [1, 2, 0]
        """
        return self._compose_optic(optics.Lens(getter, setter))

    def GetZoomAttr(self, name: str) -> "BaseUiLens[S, T, X, Y]":
        """A traversal that focuses an attribute of an object, though if
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
        """
        return self._compose_optic(optics.GetZoomAttrTraversal(name))

    def Instance(self, type_: Type) -> "BaseUiLens[S, T, X, Y]":
        """A prism that focuses a value only when that value is an
        instance of `type_`.

            >>> from lenses import lens
            >>> lens.Instance(int)
            UnboundLens(InstancePrism(...))
            >>> lens.Instance(int).collect()(1)
            [1]
            >>> lens.Instance(float).collect()(1)
            []
            >>> lens.Instance(int).set(2)(1)
            2
            >>> lens.Instance(float).set(2)(1)
            1
        """
        return self._compose_optic(optics.InstancePrism(type_))

    def Iso(
        self, forwards: Callable[[A], X], backwards: Callable[[Y], B]
    ) -> "BaseUiLens[S, T, X, Y]":
        """A lens based on an isomorphism. An isomorphism can be
        formed by two functions that mirror each other; they can convert
        forwards and backwards between a state and a focus without losing
        information. The difference between this and a regular Lens is
        that here the backwards functions don't need to know anything
        about the original state in order to produce a new state.

        These equalities should hold for the functions you supply (given
        a reasonable definition for __eq__)::

            backwards(forwards(state)) == state
            forwards(backwards(focus)) == focus

        These kinds of conversion functions are very common across
        the python ecosystem. For example, NumPy has `np.array` and
        `np.ndarray.tolist` for converting between python lists and its
        own arrays. Isomorphism makes it easy to store data in one form,
        but interact with it in a more convenient form.

            >>> from lenses import lens
            >>> lens.Iso(chr, ord)
            UnboundLens(Isomorphism(<... chr>, <... ord>))
            >>> lens.Iso(chr, ord).get()(65)
            'A'
            >>> lens.Iso(chr, ord).set('B')(65)
            66

        Due to their symmetry, isomorphisms can be flipped, thereby
        swapping thier forwards and backwards functions:

            >>> flipped = lens.Iso(chr, ord).flip()
            >>> flipped
            UnboundLens(Isomorphism(<... ord>, <... chr>))
            >>> flipped.get()('A')
            65
        """
        return self._compose_optic(optics.Isomorphism(forwards, backwards))

    def Item(self, key: Any) -> "BaseUiLens[S, T, X, Y]":
        """A lens that focuses a single item (key-value pair) in a
        dictionary by its key. Set an item to `None` to remove it from
        the dictionary.

            >>> from lenses import lens
            >>> from collections import OrderedDict
            >>> data = OrderedDict([(1, 10), (2, 20)])
            >>> lens.Item(1)
            UnboundLens(ItemLens(1))
            >>> lens.Item(1).get()(data)
            (1, 10)
            >>> lens.Item(3).get()(data) is None
            True
            >>> lens.Item(1).set((1, 11))(data)
            OrderedDict([(1, 11), (2, 20)])
            >>> lens.Item(1).set(None)(data)
            OrderedDict([(2, 20)])
        """
        return self._compose_optic(optics.ItemLens(key))

    def ItemByValue(self, value: Any) -> "BaseUiLens[S, T, X, Y]":
        """A lens that focuses a single item (key-value pair) in a
        dictionary by its value. Set an item to `None` to remove it
        from the dictionary. This lens assumes that there will only be
        a single key with that particular value. If you violate that
        assumption then you're on your own.

            >>> from lenses import lens
            >>> from collections import OrderedDict
            >>> data = OrderedDict([(1, 10), (2, 20)])
            >>> lens.ItemByValue(10)
            UnboundLens(ItemByValueLens(10))
            >>> lens.ItemByValue(10).get()(data)
            (1, 10)
            >>> lens.ItemByValue(30).get()(data) is None
            True
            >>> lens.ItemByValue(10).set((3, 10))(data)
            OrderedDict([(2, 20), (3, 10)])
            >>> lens.ItemByValue(10).set(None)(data)
            OrderedDict([(2, 20)])
        """
        return self._compose_optic(optics.ItemByValueLens(value))

    def Items(self) -> "BaseUiLens[S, T, X, Y]":
        """A traversal focusing key-value tuples that are the items of
        a dictionary. Analogous to `dict.items`.

            >>> from lenses import lens
            >>> from collections import OrderedDict
            >>> data = OrderedDict([(1, 10), (2, 20)])
            >>> lens.Items()
            UnboundLens(ItemsTraversal())
            >>> lens.Items().collect()(data)
            [(1, 10), (2, 20)]
            >>> lens.Items()[1].modify(lambda n: n + 1)(data)
            OrderedDict([(1, 11), (2, 21)])
        """
        return self._compose_optic(optics.ItemsTraversal())

    def Iter(self) -> "BaseUiLens[S, T, X, Y]":
        """A fold that can get values from any iterable object in python
        by iterating over it. Like any fold, you cannot set values.

            >>> from lenses import lens
            >>> lens.Iter()
            UnboundLens(IterableFold())
            >>> data = {2, 1, 3}
            >>> lens.Iter().collect()(data) == list(data)
            True
            >>> def numbers():
            ...     yield 1
            ...     yield 2
            ...     yield 3
            ...
            >>> lens.Iter().collect()(numbers())
            [1, 2, 3]
            >>> lens.Iter().collect()([])
            []

        If you want to be able to set values as you iterate then look
        into the EachTraversal.
        """
        return self._compose_optic(optics.IterableFold())

    def Json(self) -> "BaseUiLens[S, T, X, Y]":
        """An isomorphism that focuses a string containing json data as
        its parsed equivalent. Analogous to `json.loads`.

            >>> from lenses import lens
            >>> data = '[{"points": [4, 7]}]'
            >>> lens.Json()
            UnboundLens(JsonIso())
            >>> lens.Json()[0]['points'][1].get()(data)
            7
            >>> lens.Json()[0]['points'][0].set(8)(data)
            '[{"points": [8, 7]}]'
        """
        return self._compose_optic(optics.JsonIso())

    def Just(self) -> "BaseUiLens[S, T, X, Y]":
        """A prism that focuses the value inside a `lenses.maybe.Just`
        object.

            >>> from lenses import lens
            >>> from lenses.maybe import Just, Nothing
            >>> lens.Just()
            UnboundLens(JustPrism())
            >>> lens.Just().collect()(Just(1))
            [1]
            >>> lens.Just().collect()(Nothing())
            []
            >>> lens.Just().set(2)(Just(1))
            Just(2)
            >>> lens.Just().set(2)(Nothing())
            Nothing()
        """
        return self._compose_optic(optics.JustPrism())

    def Keys(self) -> "BaseUiLens[S, T, X, Y]":
        """A traversal focusing the keys of a dictionary. Analogous to
        `dict.keys`.

            >>> from lenses import lens
            >>> from collections import OrderedDict
            >>> data = OrderedDict([(1, 10), (2, 20)])
            >>> lens.Keys()
            UnboundLens(ItemsTraversal() & GetitemLens(0))
            >>> lens.Keys().collect()(data)
            [1, 2]
            >>> lens.Keys().modify(lambda n: n + 1)(data)
            OrderedDict([(2, 10), (3, 20)])
        """
        return self._compose_optic(optics.ItemsTraversal() & optics.GetitemLens(0))

    def Norm(self, setter: Callable[[A], X]) -> "BaseUiLens[S, T, X, Y]":
        """An isomorphism that applies a function as it sets a new
        focus without regard to the old state. It will get foci without
        transformation. This lens allows you to pre-process values before
        you set them, but still get values as they exist in the state.
        Useful for type conversions or normalising data.

        For best results, your normalisation function should be
        idempotent.  That is, applying the function twice should have
        no effect::

            setter(setter(value)) == setter(value)

        Equivalent to `Isomorphism((lambda s: s), setter)`.

            >>> from lenses import lens
            >>> def real_only(num):
            ...     return num.real
            ...
            >>> lens.Norm(real_only)
            UnboundLens(NormalisingIso(<function real_only at ...>))
            >>> lens[0].Norm(real_only).get()([1.0, 2.0, 3.0])
            1.0
            >>> lens[0].Norm(real_only).set(4+7j)([1.0, 2.0, 3.0])
            [4.0, 2.0, 3.0]

        Types with constructors that do conversion are often good targets
        for this lens:

            >>> lens[0].Norm(int).set(4.0)([1, 2, 3])
            [4, 2, 3]
            >>> lens[1].Norm(int).set('5')([1, 2, 3])
            [1, 5, 3]
        """
        return self._compose_optic(optics.NormalisingIso(setter))

    def Parts(self) -> "BaseUiLens[S, T, X, Y]":
        """Takes a Fold and turns it into a Getter by focusing a list
        of all the foci. If you use this method on a Traversal you will
        get back a Lens.

            >>> from lenses import lens
            >>> lens.Parts()
            UnboundLens(PartsLens(TrivialIso()))
            >>> lens.Each().Each().Parts()[0]
            UnboundLens(PartsLens(EachTraversal() & EachTraversal()) & GetitemLens(0))
            >>> state = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
            >>> lens.Each().Each().Parts()[0].get()(state)
            0
            >>> lens.Each().Each().Parts()[0].set(9)(state)
            [[9, 1, 2], [3, 4, 5], [6, 7, 8]]
        """
        return self._wrap_optic(optics.PartsLens)

    def Prism(
        self,
        unpack: Callable[[A], mJust[X]],
        pack: Callable[[Y], B],
        ignore_none: bool = False,
        ignore_errors: Optional[tuple] = None,
    ) -> "BaseUiLens[S, T, X, Y]":
        """A prism is an optic made from a pair of functions that pack and
        unpack a state where the unpacking process can potentially fail.

        `pack` is a function that takes a focus and returns that focus
        wrapped up in a new state. `unpack` is a function that takes
        a state and unpacks it to get a focus. The unpack function may
        choose to fail to unpack a focus, either by returning None or
        raising an exception (or both).

        All prisms are also traversals that have exactly zero or one foci.

        You must pass one or both of the ``ignore_none=True`` or
        ``ignore_errors=True`` keyword arguments. If you pass the former
        then the prism will fail to focus anything when your unpacking
        function returns ``None``. If you pass the latter then it will
        fail to focus when your unpacking function raises an error.

            >>> from lenses import lens
            >>> lens.Prism(int, str)
            Traceback (most recent call last):
              File "<stdin>", line 1 in ?
            ValueError: Must specify what to ignore
            >>> lens.Prism(int, str, ignore_errors=True)
            UnboundLens(Prism(..., ...))
            >>> lens.Prism(int, str, ignore_errors=True).collect()('42')
            [42]
            >>> lens.Prism(int, str, ignore_errors=True).collect()('fourty two')
            []

        If you set ``ignore_errors`` to ``True`` then it will catch any
        and all exceptions. A better alternative is to set it to a tuple of
        exception types to ignore (such as you would pass to ``isinstance``).

            >>> errors = (ValueError,)
            >>> lens.Prism(int, str, ignore_errors=errors)
            UnboundLens(Prism(..., ...))
            >>> lens.Prism(int, str, ignore_errors=errors).collect()('42')
            [42]
            >>> lens.Prism(int, str, ignore_errors=errors).collect()('fourty two')
            []
            >>> lens.Prism(int, str, ignore_errors=errors).collect()([1, 2, 3])
            Traceback (most recent call last):
              File "<stdin>", line 1 in ?
            TypeError: int() argument must be ...
        """

        if not (ignore_none or ignore_errors):
            raise ValueError("Must specify what to ignore")

        if ignore_errors is True:
            ignore_errors = (Exception,)

        @functools.wraps(unpack)
        def new_unpack(state):
            try:
                result = unpack(state)
            except Exception as e:
                if ignore_errors and isinstance(e, ignore_errors):
                    return mNothing()
                else:
                    raise e
            if ignore_none:
                return mNothing() if result is None else mJust(result)
            return mJust(result)

        return self._compose_optic(optics.Prism(new_unpack, pack))

    def Recur(self, cls):
        """A traversal that recurses through an object focusing everything it
        can find of a particular type. This traversal will probe arbitrarily
        deep into the contents of the state looking for sub-objects. It
        uses some naughty tricks to do this including looking at an object's
        `__dict__` attribute.

        It is somewhat analogous to haskell's uniplate optic.

            >>> from lenses import lens
            >>> lens.Recur(int)
            UnboundLens(RecurTraversal(<... 'int'>))
            >>> data = [[1, 2, 100.0], [3, 'hello', [{}, 4], 5]]
            >>> lens.Recur(int).collect()(data)
            [1, 2, 3, 4, 5]
            >>> (lens.Recur(int) + 1)(data)
            [[2, 3, 100.0], [4, 'hello', [{}, 5], 6]]

        It also works on custom classes:

            >>> class Container(object):
            ...     def __init__(self, contents):
            ...         self.contents = contents
            ...     def __repr__(self):
            ...         return 'Container({!r})'.format(self.contents)
            >>> data = [Container(1), 2, Container(Container(3)), [4, 5]]
            >>> (lens.Recur(int) + 1)(data)
            [Container(2), 3, Container(Container(4)), [5, 6]]
            >>> lens.Recur(Container).collect()(data)
            [Container(1), Container(Container(3))]

        Be careful with this; it can focus things you might not expect.
        """
        return self._compose_optic(optics.RecurTraversal(cls))

    def Traversal(
        self,
        folder: Callable[[A], Iterable[X]],
        builder: Callable[[A, Iterable[Y]], B],
    ) -> "BaseUiLens[S, T, X, Y]":
        """An optic that wraps folder and builder functions.

        The folder function is a function that takes a single argument -
        the state - and returns an iterable containing all the foci that
        exist in that state. Generators are a good option for writing
        folder functions.

        A builder function takes the old state and an list of values
        and constructs a new state with the old state's values swapped
        out. The number of values passed to builder for any given state
        should always be the same as the number of values that the folder
        function would have returned for that same state.

            >>> from lenses import lens
            >>> def ends_folder(state):
            ...     'Yields the first and last elements of a list'
            ...     yield state[0]
            ...     yield state[-1]
            >>> def ends_builder(state, values):
            ...     'Sets the first and last elements of a list'
            ...     result = list(state)
            ...     result[0] = values[0]
            ...     result[-1] = values[1]
            ...     return result
            >>> both_ends = lens.Traversal(ends_folder, ends_builder)
            >>> both_ends
            UnboundLens(Traversal(...ends_folder..., ...ends_builder...))
            >>> both_ends.collect()([1, 2, 3, 4])
            [1, 4]
            >>> both_ends.set(5)([1, 2, 3, 4])
            [5, 2, 3, 5]
        """

        return self._compose_optic(optics.Traversal(folder, builder))

    def Tuple(self, *lenses: "BaseUiLens[A, B, X, Y]") -> "BaseUiLens[S, T, X, Y]":
        """A lens that combines the focuses of other lenses into a
        single tuple. The sublenses must be optics of kind Lens; this
        means no Traversals.

            >>> from lenses import lens
            >>> lens.Tuple()
            UnboundLens(TupleLens())
            >>> tl = lens.Tuple(lens[0], lens[2])
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
            >>> tl.Each().Each().collect()(state)
            [1, 2, 3, 5, 6]
            >>> (tl.Each().Each() + 10)(state)
            ([11, 12, 13], 4, [15, 16])
        """
        true_lenses = [l._optic for l in lenses]
        return self._compose_optic(optics.TupleLens(*true_lenses))

    def Values(self) -> "BaseUiLens[S, T, X, Y]":
        """A traversal focusing the values of a dictionary. Analogous to
        `dict.values`.

            >>> from lenses import lens
            >>> from collections import OrderedDict
            >>> data = OrderedDict([(1, 10), (2, 20)])
            >>> lens.Values()
            UnboundLens(ItemsTraversal() & GetitemLens(1))
            >>> lens.Values().collect()(data)
            [10, 20]
            >>> lens.Values().modify(lambda n: n + 1)(data)
            OrderedDict([(1, 11), (2, 21)])
        """
        return self._compose_optic(optics.ItemsTraversal() & optics.GetitemLens(1))

    def Zoom(self) -> "BaseUiLens[S, T, X, Y]":
        """Follows its state as if it were a `BoundLens` object.

        >>> from lenses import lens, bind
        >>> data = [bind([1, 2])[1], 4]
        >>> lens.Zoom()
        UnboundLens(ZoomTraversal())
        >>> lens[0].Zoom().get()(data)
        2
        >>> lens[0].Zoom().set(3)(data)
        [[1, 3], 4]
        """
        return self._compose_optic(optics.ZoomTraversal())

    def ZoomAttr(self, name: str) -> "BaseUiLens[S, T, X, Y]":
        """A lens that looks up an attribute on its target and follows
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
            >>> lens.ZoomAttr('first')
            UnboundLens(ZoomAttrTraversal('first'))
            >>> lens[0].ZoomAttr('first').get()(data)
            1
            >>> lens[0].ZoomAttr('first').set(5)(data)
            (ClassWithLens([5, 2, 3]), 4)
        """
        return self._compose_optic(optics.ZoomAttrTraversal(name))

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError("no attribute {}".format(name))

        if name.startswith("call_mut_"):

            def caller(*args: Any, **kwargs: Any) -> T:
                return self.call_mut(name[9:], *args, **kwargs)

            return caller

        if name.startswith("call_"):

            def caller(*args: Any, **kwargs: Any) -> T:
                return self.call(name[5:], *args, **kwargs)

            return caller

        return self.GetZoomAttr(name)

    def __getitem__(self, name: Any) -> "BaseUiLens[S, T, X, Y]":
        return self.GetItem(name)
