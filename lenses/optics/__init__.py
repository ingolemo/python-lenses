from .. import hooks
from ..identity import Identity
from ..const import Const
from ..functorisor import Functorisor
from ..maybe import Just, Nothing
from .. import typeclass


def multiap(func, *args):
    '''Applies `func` to the data inside the `args` functors
    incrementally. `func` must be a curried function that takes
    `len(args)` arguments.

        >>> func = lambda a: lambda b: a + b
        >>> multiap(func, [1, 10], [100])
        [101, 110]
    '''
    functor = typeclass.fmap(args[0], func)
    for arg in args[1:]:
        functor = typeclass.apply(arg, functor)
    return functor


def collect_args(n):
    '''Returns a function that can be called `n` times with a single
    argument before returning all the args that have been passed to it
    in a tuple. Useful as a substitute for functions that can't easily be
    curried.

        >>> collect_args(3)(1)(2)(3)
        (1, 2, 3)
    '''
    args = []

    def arg_collector(arg):
        args.append(arg)
        if len(args) == n:
            return tuple(args)
        else:
            return arg_collector

    return arg_collector


class LensLike(object):
    '''A LensLike. Serves as the backbone of the lenses library. Acts as an
    object-oriented wrapper around a function (`LensLike.func`) that
    does all the hard work. This function is an uncurried form of the
    van Laarhoven lens and has the following type (in ML-style
    notation):

    func :: (value -> functor value), state -> functor state

    A LensLike has a kind that determines what operations are valid on
    that LensLike. Valid kinds are Equality, Isomorphism, Prism, Review,
    Lens, Traversal, Getter, Setter, Fold, and None.

    Fold

    : A Fold is an optic capable of getting, but not necessarily setting,
    multiple foci at once. You can think of a fold as kind of like an
    iterator; it allows you to view many subparts of a larger structure.

    Setter

    : A Setter is an optic that is capable of setting foci in a state
    but not necessarily getting them.

    Getter

    : A Getter is a Fold that is restricted to getting a single foci at
    a time. It can not necessarily set any foci.

    Traversal

    : A Traversal is both a Fold and a Setter. It is capable of both
    setting and getting multiple foci at once.

    Lens

    : A Lens is both a Getter and a Traversal. It is capable of getting
    and setting is single foci at a time.

    Review

    : Currently Unused.

    Prism

    : A Prism is both a Traversal and a Review. Currently unused.

    Isomorphism

    : An Isomorphism is both a Lens and a Prism. Isomorphisms have the
    property that they are reversable; You can take an isomorphism and
    flip it around so that getting the foci becomes setting the foci
    and setting becomes getting.

    Equality

    : An Equality is an Isomorphism. Currently unused.

    None

    : Here "None" is referring to the built-in python `None` object and
    not a custom class like the other kinds. An optic of kind None is
    an invalid optic. Optics of this kind may exist internally, but if
    you manage to create a None optic through normal means then this
    represents a bug in the library.
    '''

    def func(self, f, state):
        '''Intended to be overridden by subclasses. Raises
        NotImplementedError.'''
        message = 'Tried to use unimplemented lens {}.'
        raise NotImplementedError(message.format(type(self)))

    def get(self, state):
        '''Returns the focus within `state`. If multiple items are
        focused then it will attempt to join them together as a monoid.
        See `lenses.typeclass.mappend`.

        Requires kind Fold. This method will raise TypeError if the
        optic has no way to get any foci.

        For technical reasons, this method requires there to be at least
        one foci at the end of the get. It will raise ValueError when
        there is none.
        '''
        if not self._is_kind(Fold):
            raise TypeError('Must be an instance of Fold to .get()')

        guard = object()
        const = Functorisor(lambda a: Const(Nothing()),
                            lambda a: Const(Just(a)))
        result = self.func(const, state).unwrap().maybe(guard)
        if result is guard:
            raise ValueError('No focus to get')
        return result

    def get_all(self, state):
        '''Returns a list of all the foci within `state`.

        Requires kind Fold. This method will raise TypeError if the
        optic has no way to get any foci.
        '''
        if not self._is_kind(Fold):
            raise TypeError('Must be an instance of Fold to .get_all()')

        consttup = Functorisor(lambda a: Const([]),
                               lambda a: Const([a]))
        return self.func(consttup, state).unwrap()

    def modify(self, state, fn):
        '''Applies a function `fn` to all the foci within `state`.

        Requires kind Setter. This method will raise TypeError when the
        optic has no way to set foci.
        '''
        if not self._is_kind(Setter):
            raise TypeError('Must be an instance of Setter to .modify()')

        identfn = Functorisor(lambda a: Identity(a),
                              lambda a: Identity(fn(a)))
        return self.func(identfn, state).unwrap()

    def set(self, state, value):
        '''Sets all the foci within `state` to `value`.

        Requires kind Setter. This method will raise TypeError when the
        optic has no way to set foci.
        '''
        if not self._is_kind(Setter):
            raise TypeError('Must be an instance of Setter to .set()')

        ident = Functorisor(lambda a: Identity(a),
                            lambda a: Identity(value))
        return self.func(ident, state).unwrap()

    def compose(self, other):
        '''Composes another lens with this one. The result is a lens
        that feeds the foci of `self` into the state of `other`.
        '''
        return ComposedLens([self]).compose(other)

    def flip(self):
        '''Flips an isomorphism so that it works in the opposite
        direction. Only works if the lens is actually an isomorphism.
        Intended to be overridden by such subclasses.

        Requires type Isomorphism. Raises TypeError for non-isomorphic
        lenses.
        '''
        if not self._is_kind(Isomorphism):
            raise TypeError('Must be an instance of Isomorphism to .flip()')

    def kind(self):
        '''Returns a class representing the 'kind' of optic.'''
        optics = [Equality, Isomorphism, Prism, Review,
                  Lens, Traversal,
                  Getter, Setter, Fold]
        for optic in optics:
            if self._is_kind(optic):
                return optic

    def _underlying_lens(self):
        return self

    def _is_kind(self, cls):
        return isinstance(self, cls)

    __and__ = compose


class Fold(LensLike):
    pass


class Setter(LensLike):
    pass


class Getter(Fold):
    pass


class Traversal(Fold, Setter):
    pass


class Lens(Getter, Traversal):
    pass


class Review(LensLike):
    pass


class Prism(Traversal, Review):
    pass


class Isomorphism(Lens, Prism):
    pass


class Equality(Isomorphism):
    pass


class ComposedLens(LensLike):
    '''A lenses representing the composition of several sub-lenses. This
    class tries to just pass operations down to the sublenses without
    imposing any constraints on what can happen. The sublenses are in
    charge of what capabilities they support.

        >>> from lenses import lens
        >>> lens()[0][1]
        Lens(None, GetitemLens(0) & GetitemLens(1))

    (The ComposedLens is represented above by the `&` symbol)
    '''

    def __init__(self, lenses=()):
        self.lenses = list(self._filter_lenses(lenses))

    @staticmethod
    def _filter_lenses(lenses):
        for lens in lenses:
            lenstype = type(lens)
            if lenstype is TrivialLens:
                continue
            elif lenstype is ComposedLens:
                for lens in lens.lenses:
                    yield lens
            else:
                yield lens

    def func(self, f, state):
        if not self.lenses:
            return TrivialLens().func(f, state)

        res = f
        for lens in reversed(self.lenses):
            res = res.update(lens.func)

        return res(state)

    def flip(self):
        super(ComposedLens, self).flip()
        return ComposedLens([l.flip() for l in reversed(self.lenses)])

    def compose(self, other):
        result = ComposedLens(self.lenses + [other])
        if len(result.lenses) == 0:
            return TrivialLens()
        elif len(result.lenses) == 1:
            return result.lenses[0]
        if result.kind() is None:
            raise RuntimeError('Optic has no valid type')
        return result

    def __repr__(self):
        return ' & '.join(str(l) for l in self.lenses)

    def _is_kind(self, cls):
        return all(lens._is_kind(cls) for lens in self.lenses)


class GetterSetterLens(Lens):
    '''Turns a pair of getter and setter functions into a van
    Laarhoven lens. A getter function is one that takes a state and
    returns a value derived from that state. A setter function takes
    an old state and a new value and uses them to construct a new state.

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
        >>> average_lens = lens().getter_setter_(getter, setter)
        >>> average_lens
        Lens(None, GetterSetterLens(<function getter...>, <function setter...>))
        >>> average_lens.bind([1, 2, 4, 5]).get()
        3
        >>> average_lens.bind([1, 2, 3]).set(4)
        [1, 2, 9]
        >>> average_lens.bind([1, 2, 3]) - 1
        [1, 2, 0]

    Though GetterSetterLens is more powerful because it can inspect the
    old state to produce a new one, IsomorphismLens is more suited to
    building custom lenses due to the greater availability of functions
    that already fit its API. Only use a GetterSetterLens if you need the
    extra power it affords.
    '''

    def __init__(self, getter, setter):
        self.getter = getter
        self.setter = setter

    def func(self, f, state):
        old_value = self.getter(state)
        fa = f(old_value)
        return typeclass.fmap(fa, lambda a: self.setter(state, a))

    def __repr__(self):
        return 'GetterSetterLens({!r}, {!r})'.format(self.getter, self.setter)


class IsomorphismLens(Isomorphism):
    '''A lens based on an isomorphism. An isomorphism can be formed by
    two functions that mirror each other; they can convert forwards
    and backwards between a state and a focus without losing
    information. The difference between this and a GetterSetterLens is
    that here the backwards functions don't need to know anything about
    the original state in order to produce a new state.

    These equalities should hold for the functions you supply (given
    a reasonable definition for __eq__):

        backwards(forwards(state)) == state
        forwards(backwards(focus)) == focus

    These kinds of conversion functions are very common across the
    python ecosystem. For example, NumPy has `np.array` and
    `np.ndarray.tolist` for converting between python lists and its own
    arrays. IsomorphismLens makes it easy to store data in one form, but
    interact with it in a more convenient form.

        >>> from lenses import lens
        >>> lens().iso_(chr, ord)
        Lens(None, IsomorphismLens(<built-in function chr>, <built-in function ord>))
        >>> lens(65).iso_(chr, ord).get()
        'A'
        >>> lens(65).iso_(chr, ord).set('B')
        66

    Due to their symmetry, isomorphisms can be flipped, thereby swapping
    thier forwards and backwards functions:

        >>> flipped = lens().iso_(chr, ord).flip()
        >>> flipped
        Lens(None, IsomorphismLens(<built-in function ord>, <built-in function chr>))
        >>> flipped.bind('A').get()
        65
    '''

    def __init__(self, forwards, backwards):
        self.forwards = forwards
        self.backwards = backwards

    def flip(self):
        return IsomorphismLens(self.backwards, self.forwards)

    def func(self, f, state):
        return typeclass.fmap(f(self.forwards(state)), self.backwards)

    def __repr__(self):
        return 'IsomorphismLens({!r}, {!r})'.format(self.forwards,
                                                    self.backwards)


class BothLens(Traversal):
    '''A traversal that focuses both items [0] and [1].

        >>> from lenses import lens
        >>> lens().both_()
        Lens(None, BothLens())
        >>> lens([1, 2, 3]).both_().get_all()
        [1, 2]
        >>> lens([1, 2, 3]).both_().set(4)
        [4, 4, 3]
    '''

    def func(self, f, state):
        def multisetter(items):
            s = hooks.setitem_immutable(state, 0, items[0])
            s = hooks.setitem_immutable(s, 1, items[1])
            return s

        f0 = f(state[0])
        f1 = f(state[1])
        return typeclass.fmap(multiap(collect_args(2), f0, f1), multisetter)

    def __repr__(self):
        return 'BothLens()'


class DecodeLens(IsomorphismLens):
    '''An isomorphism that decodes and encodes its focus on the fly.
    Lets you focus a byte string as a unicode string. The arguments have
    the same meanings as `bytes.decode`. Analogous to `bytes.decode`.

        >>> from lenses import lens
        >>> lens().decode_(encoding='utf8')
        Lens(None, DecodeLens('utf8', 'strict'))
        >>> lens(b'hello').decode_().get()  # doctest: +SKIP
        'hello'
        >>> lens(b'hello').decode_().set('world')  # doctest: +SKIP
        b'world'
    '''

    def __init__(self, encoding='utf-8', errors='strict'):
        self.encoding = encoding
        self.errors = errors

    def forwards(self, state):
        return state.decode(self.encoding, self.errors)

    def backwards(self, focus):
        return focus.encode(self.encoding, self.errors)

    def __repr__(self):
        repr = 'DecodeLens({!r}, {!r})'
        return repr.format(self.encoding, self.errors)


class EachLens(Traversal):
    '''A traversal that iterates over its state, focusing everything it
    iterates over. It uses `lenses.hooks.fromiter` to reform the state
    afterwards so it should work with any iterable that function
    supports. Analogous to `iter`.

        >>> from lenses import lens
        >>> data = [1, 2, 3]
        >>> lens().each_()
        Lens(None, EachLens())
        >>> lens(data).each_().get_all()
        [1, 2, 3]
        >>> lens(data).each_().modify(lambda n: n + 1)
        [2, 3, 4]
        >>> lens(data).each_(filter_none=True).set(None)
        []

    For technical reasons, this lens iterates over dictionaries by their
    items and not just their keys.

        >>> data = {'one': 1}
        >>> lens(data).each_().get_all()
        [('one', 1)]
        >>> lens(data).each_()[1] + 1
        {'one': 2}
    '''

    def __init__(self, filter_func=None, filter_none=False, *_):
        if filter_none:
            self.filter_func = lambda a: a is not None
        elif filter_func is None:
            self.filter_func = lambda a: True
        else:
            self.filter_func = filter_func

    def func(self, f, state):
        items = list(filter(self.filter_func, hooks.to_iter(state)))

        def build_new_state_from_iter(a):
            return hooks.from_iter(state, filter(self.filter_func, a))

        if items == []:
            return f.pure(build_new_state_from_iter(items))

        collector = collect_args(len(items))
        applied = multiap(collector, *map(f, items))
        return typeclass.fmap(applied, build_new_state_from_iter)

    def __repr__(self):
        return 'EachLens()'


class ErrorLens(Traversal):
    '''A lens that raises an exception whenever it tries to focus
    something. If `message is None` then the exception will be raised
    unmodified. If `message is not None` then when the lens is asked to
    focus something it will run `message.format(state)` and the
    exception will be called with the resulting formatted message as
    it's only argument. Useful for debugging.

        >>> from lenses import lens
        >>> lens().error_(Exception())
        Lens(None, ErrorLens(Exception()))
        >>> lens().error_(Exception, '{}')  # doctest: +SKIP
        Lens(None, ErrorLens(<class 'Exception'>, '{}'))
        >>> lens(True).error_(Exception).get()
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        Exception
        >>> lens(True).error_(Exception('An error occurred')).set(False)
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        Exception: An error occurred
        >>> lens(True).error_(ValueError, 'applied to {}').get()
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: applied to True
    '''

    def __init__(self, exception, message=None):
        self.exception = exception
        self.message = message

    def func(self, f, state):
        if self.message is None:
            raise self.exception
        raise self.exception(self.message.format(state))

    def __repr__(self):
        if self.message is None:
            return 'ErrorLens({!r})'.format(self.exception)
        return 'ErrorLens({!r}, {!r})'.format(self.exception, self.message)


class FilteringLens(Traversal):
    '''A traversal that only traverses a focus if the predicate returns
    `True` when called with that focus as an argument. Best used when
    composed after a traversal. It only prevents the traversal from
    visiting foci, it does not filter out values the way that python's
    regular `filter` function does.

        >>> from lenses import lens
        >>> lens().filter_(all)
        Lens(None, FilteringLens(<built-in function all>))
        >>> data = [[1, 2], [0], ['a'], ['', 'b']]
        >>> lens(data).each_().filter_(all).get_all()
        [[1, 2], ['a']]
        >>> lens(data).each_().filter_(all).set(2)
        [2, [0], 2, ['', 'b']]

    The filtering is done to foci before the lens' manipulation is
    applied. This means that the resulting foci can still violate the
    predicate if the manipulating function doesn't respect it:

        >>> lens(['', 2, '']).each_().filter_(bool).set(None)
        ['', None, '']
    '''

    def __init__(self, predicate):
        self.predicate = predicate

    def func(self, f, state):
        return f(state) if self.predicate(
            state) else typeclass.pure(f(state), state)

    def __repr__(self):
        return 'FilteringLens({!r})'.format(self.predicate)


class GetattrLens(GetterSetterLens):
    '''A lens that focuses an attribute of an object. Analogous to
    `getattr`.

        >>> from lenses import lens
        >>> from collections import namedtuple
        >>> Pair = namedtuple('Pair', 'left right')
        >>> lens().getattr_('left')
        Lens(None, GetattrLens('left'))
        >>> lens(Pair(1, 2)).getattr_('left').get()
        1
        >>> lens(Pair(1, 2)).getattr_('right').set(3)
        Pair(left=1, right=3)
    '''

    def __init__(self, name):
        self.name = name

    def getter(self, state):
        return getattr(state, self.name)

    def setter(self, state, focus):
        return hooks.setattr_immutable(state, self.name, focus)

    def __repr__(self):
        return 'GetattrLens({!r})'.format(self.name)


class GetZoomAttrLens(Lens):
    '''A lens that focuses an attribute of an object, though if that attribute
    happens to be a lens it will zoom the lens.

        >>> from lenses import lens
        >>> from collections import namedtuple
        >>> Triple = namedtuple('Triple', 'left middle right')
        >>> state = Triple(1, 10, lens().middle)
        >>> lens().left
        Lens(None, GetZoomAttrLens('left'))
        >>> lens(state).left.get()
        1
        >>> lens(state).left.set(3)
        Triple(left=3, middle=10, right=Lens(None, GetZoomAttrLens('middle')))
        >>> lens(state).right.get()
        10
        >>> lens(state).right.set(13)
        Triple(left=1, middle=13, right=Lens(None, GetZoomAttrLens('middle')))
    '''

    def __init__(self, name):
        self.name = name
        self._getattr_cache = GetattrLens(name)

    def func(self, f, state):
        attr = getattr(state, self.name)
        try:
            sublens = attr._underlying_lens()
        except AttributeError:
            sublens = self._getattr_cache
        return sublens.func(f, state)

    def __repr__(self):
        return 'GetZoomAttrLens({!r})'.format(self.name)


class GetitemLens(GetterSetterLens):
    '''A lens that focuses an item inside a container. Analogous to
    `operator.itemgetter`.

        >>> from lenses import lens
        >>> lens()[0]
        Lens(None, GetitemLens(0))
        >>> lens().getitem_(0)
        Lens(None, GetitemLens(0))
        >>> lens([1, 2, 3])[0].get()
        1
        >>> lens({'hello': 'world'})['hello'].get()
        'world'
        >>> lens([1, 2, 3])[0].set(4)
        [4, 2, 3]
        >>> lens({'hello': 'world'})['hello'].set('universe')
        {'hello': 'universe'}
    '''

    def __init__(self, key):
        self.key = key

    def getter(self, state):
        return state[self.key]

    def setter(self, state, focus):
        return hooks.setitem_immutable(state, self.key, focus)

    def __repr__(self):
        return 'GetitemLens({!r})'.format(self.key)


class GetitemOrElseLens(GetitemLens):
    '''A lens that focuses an item inside a container by calling its `get`
    method, allowing you to specify a default value for missing keys.
    Analogous to `dict.get`.

        >>> from lenses import lens
        >>> lens().get_('foo')
        Lens(None, GetitemOrElseLens('foo'))
        >>> lens({'foo': 'bar'}).get_('baz').get()
        >>> lens({'foo': 'bar'}).get_('baz', []).get()
        []
        >>> from collections import OrderedDict
        >>> lens(OrderedDict({'foo': 'bar'})).get_('baz').set('qux')
        OrderedDict([('foo', 'bar'), ('baz', 'qux')])
    '''

    def __init__(self, key, default=None):
        self.key = key
        self.default = default

    def getter(self, state):
        return state.get(self.key, self.default)

    def __repr__(self):
        return 'GetitemOrElseLens({!r})'.format(self.key)


class ItemLens(GetterSetterLens):
    '''A lens that focuses a single item (key-value pair) in a
    dictionary by its key. Set an item to `None` to remove it from the
    dictionary.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().item_(1)
        Lens(None, ItemLens(1))
        >>> lens(data).item_(1).get()
        (1, 10)
        >>> lens(data).item_(3).get() is None
        True
        >>> lens(data).item_(1).set((1, 11))
        OrderedDict([(1, 11), (2, 20)])
        >>> lens(data).item_(1).set(None)
        OrderedDict([(2, 20)])
    '''

    def __init__(self, key):
        self.key = key

    def getter(self, state):
        try:
            return self.key, state[self.key]
        except KeyError:
            return None

    def setter(self, state, focus):
        data = state.copy()
        if focus is None:
            del data[self.key]
            return data
        if focus[0] != self.key:
            del data[self.key]
        data[focus[0]] = focus[1]
        return data

    def __repr__(self):
        return 'ItemLens({!r})'.format(self.key)


class ItemByValueLens(GetterSetterLens):
    '''A lens that focuses a single item (key-value pair) in a
    dictionary by its value. Set an item to `None` to remove it from the
    dictionary. This lens assumes that there will only be a single key
    with that particular value. If you violate that assumption then
    you're on your own.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().item_by_value_(10)
        Lens(None, ItemByValueLens(10))
        >>> lens(data).item_by_value_(10).get()
        (1, 10)
        >>> lens(data).item_by_value_(30).get() is None
        True
        >>> lens(data).item_by_value_(10).set((3, 10))
        OrderedDict([(2, 20), (3, 10)])
        >>> lens(data).item_by_value_(10).set(None)
        OrderedDict([(2, 20)])
    '''

    def __init__(self, value):
        self.value = value

    def getter(self, state):
        for dkey, dvalue in state.items():
            if dvalue == self.value:
                return dkey, dvalue

    def setter(self, state, focus):
        data = state.copy()
        for key, val in state.items():
            if val == self.value:
                del data[key]
        if focus is not None:
            data[focus[0]] = focus[1]
        return data

    def __repr__(self):
        return 'ItemByValueLens({!r})'.format(self.value)


class ItemsLens(Traversal):
    '''A traversal focusing key-value tuples that are the items of a
    dictionary. Analogous to `dict.items`.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().items_()
        Lens(None, ItemsLens())
        >>> lens(data).items_().get_all()
        [(1, 10), (2, 20)]
        >>> lens(data).items_()[1].modify(lambda n: n + 1)
        OrderedDict([(1, 11), (2, 21)])
    '''

    def func(self, f, state):
        items = list(state.items())
        if items == []:
            return f.pure(state)

        def dict_builder(args):
            data = state.copy()
            data.clear()
            data.update(a for a in args if a is not None)
            return data

        collector = collect_args(len(items))
        return typeclass.fmap(multiap(collector, *map(f, items)), dict_builder)

    def __repr__(self):
        return 'ItemsLens()'


class JsonLens(IsomorphismLens):
    '''An isomorphism that focuses a string containing json data as its
    parsed equivalent. Analogous to `json.loads`.

        >>> from lenses import lens
        >>> data = '[{"points": [4, 7]}]'
        >>> lens().json_()
        Lens(None, JsonLens())
        >>> lens(data).json_()[0]['points'][1].get()
        7
        >>> lens(data).json_()[0]['points'][0].set(8)
        '[{"points": [8, 7]}]'
    '''

    def __init__(self):
        self.json_mod = __import__('json')

    def forwards(self, state):
        return self.json_mod.loads(state)

    def backwards(self, focus):
        return self.json_mod.dumps(focus)

    def __repr__(self):
        return 'JsonLens()'


class KeysLens(ComposedLens):
    '''A traversal focusing the keys of a dictionary. Analogous to
    `dict.keys`.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().keys_()
        Lens(None, KeysLens())
        >>> lens(data).keys_().get_all()
        [1, 2]
        >>> lens(data).keys_().modify(lambda n: n + 1)
        OrderedDict([(2, 10), (3, 20)])
    '''

    def __init__(self):
        self.lenses = [ItemsLens(), GetitemLens(0)]

    def __repr__(self):
        return 'KeysLens()'


class ListWrapLens(IsomorphismLens):
    '''An isomorphism that wraps its state up in a list. This is
    occasionally useful when you need to make hetrogenous data more
    uniform. Analogous to `lambda state: [state]`.

        >>> from lenses import lens
        >>> lens().listwrap_()
        Lens(None, ListWrapLens())
        >>> lens(0).listwrap_().get()
        [0]
        >>> lens(0).listwrap_().set([1])
        1
        >>> l = lens().tuple_(lens()[0], lens()[1].listwrap_())
        >>> l.bind([[1, 3], 4]).each_().each_().get_all()
        [1, 3, 4]

    Also serves as an example that lenses do not always have to
    'zoom in' on a focus; they can also 'zoom out'.
    '''

    def __init__(self):
        pass

    def forwards(self, state):
        return [state]

    def backwards(self, focus):
        return focus[0]

    def __repr__(self):
        return 'ListWrapLens()'


class NormalisingLens(IsomorphismLens):
    '''An isomorphism that applies a function as it sets a new focus
    without regard to the old state. It will get foci without
    transformation. This lens allows you to pre-process values before
    you set them, but still get values as they exist in the state.
    Useful for type conversions or normalising data.

    For best results, your normalisation function should be idempotent.
    That is, applying the function twice should have no effect:

        setter(setter(value)) == setter(value)

    Equivalent to `IsomophismLens((lambda s: s), setter)`.

        >>> from lenses import lens
        >>> def real_only(num):
        ...     return num.real
        ...
        >>> lens().norm_(real_only)
        Lens(None, NormalisingLens(<function real_only at ...>))
        >>> lens([1.0, 2.0, 3.0])[0].norm_(real_only).get()
        1.0
        >>> lens([1.0, 2.0, 3.0])[0].norm_(real_only).set(4+7j)
        [4.0, 2.0, 3.0]

    Types with constructors that do conversion are often good targets
    for this lens:

        >>> lens([1, 2, 3])[0].norm_(int).set(4.0)
        [4, 2, 3]
        >>> lens([1, 2, 3])[1].norm_(int).set('5')
        [1, 5, 3]
    '''

    def __init__(self, setter):
        self.backwards = setter

    def forwards(self, state):
        return state

    def __repr__(self):
        return 'NormalisingLens({!r})'.format(self.backwards)


class TrivialLens(IsomorphismLens):
    '''A trivial isomorphism that focuses the whole state. It doesn't
    manipulate the state in any way. Mostly used as a "null" lens.
    Analogous to `lambda a: a`.

        >>> from lenses import lens
        >>> lens()
        Lens(None, TrivialLens())
        >>> lens(True).get()
        True
        >>> lens(True).set(False)
        False
    '''

    def __init__(self):
        pass

    def forwards(self, state):
        return state

    def backwards(self, focus):
        return focus

    def __repr__(self):
        return 'TrivialLens()'


class TupleLens(GetterSetterLens):
    '''A lens that combines the focuses of other lenses into a single
    tuple. The sublenses must be optics of kind Lens; this means no
    Traversals.

        >>> from lenses import lens
        >>> lens().tuple_()
        Lens(None, TupleLens())
        >>> tl = lens().tuple_(lens()[0], lens()[2])
        >>> tl
        Lens(None, TupleLens(GetitemLens(0), GetitemLens(2)))
        >>> tl.bind([1, 2, 3, 4]).get()
        (1, 3)
        >>> tl.bind([1, 2, 3, 4]).set((5, 6))
        [5, 2, 6, 4]

    This lens is particularly useful when immediately followed by
    an EachLens, allowing you to traverse data even when it comes
    from disparate locations within the state.

        >>> state = ([1, 2, 3], 4, [5, 6])
        >>> tl.bind(state).each_().each_().get_all()
        [1, 2, 3, 5, 6]
        >>> tl.bind(state).each_().each_() + 10
        ([11, 12, 13], 4, [15, 16])
    '''

    def __init__(self, *lenses):
        self.lenses = [l._underlying_lens() for l in lenses]
        for lens in self.lenses:
            if not lens._is_kind(Lens):
                raise TypeError('TupleLens only works with lenses')

    def getter(self, state):
        return tuple(lens.get(state) for lens in self.lenses)

    def setter(self, state, focus):
        for lens, new_value in zip(self.lenses, focus):
            state = lens.set(state, new_value)
        return state

    def __repr__(self):
        args = ', '.join(repr(lens) for lens in self.lenses)
        return 'TupleLens({})'.format(args)


class ValuesLens(ComposedLens):
    '''A traversal focusing the values of a dictionary. Analogous to
    `dict.values`.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().values_()
        Lens(None, ValuesLens())
        >>> lens(data).values_().get_all()
        [10, 20]
        >>> lens(data).values_().modify(lambda n: n + 1)
        OrderedDict([(1, 11), (2, 21)])
    '''

    def __init__(self):
        self.lenses = [ItemsLens(), GetitemLens(1)]

    def __repr__(self):
        return 'ValuesLens()'


class ZoomAttrLens(Traversal):
    '''A lens that looks up an attribute on its target and follows it as
    if were a bound `Lens` object. Ignores the state, if any, of the
    lens that is being looked up.

        >>> from lenses import lens
        >>> class ClassWithLens(object):
        ...     def __init__(self, items):
        ...         self._private_items = items
        ...     def __repr__(self):
        ...         return 'ClassWithLens({!r})'.format(self._private_items)
        ...     first = lens()._private_items[0]
        ...
        >>> data = (ClassWithLens([1, 2, 3]), 4)
        >>> lens().zoomattr_('first')
        Lens(None, ZoomAttrLens('first'))
        >>> lens(data)[0].zoomattr_('first').get()
        1
        >>> lens(data)[0].zoomattr_('first').set(5)
        (ClassWithLens([5, 2, 3]), 4)
    '''

    def __init__(self, name):
        self.name = name

    def func(self, f, state):
        l = getattr(state, self.name)
        return l._underlying_lens().func(f, state)

    def __repr__(self):
        return 'ZoomAttrLens({!r})'.format(self.name)


class ZoomLens(Traversal):
    '''Follows its state as if it were a bound `Lens` object.

        >>> from lenses import lens
        >>> data = [lens([1, 2])[1], 4]
        >>> lens().zoom_()
        Lens(None, ZoomLens())
        >>> lens(data)[0].zoom_().get()
        2
        >>> lens(data)[0].zoom_().set(3)
        [[1, 3], 4]
    '''

    def func(self, f, state):
        return state._underlying_lens().func(f, state.state)

    def __repr__(self):
        return 'ZoomLens()'
