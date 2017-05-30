from typing import Callable, Generic, Iterable, List, Optional, cast

from ..const import Const
from ..functorisor import Functorisor
from ..identity import Identity
from .. import typeclass
from ..maybe import Just, Nothing
from ..typevars import S, T, A, B


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

    : A Getter is a Fold that is restricted to getting a single focus at
    a time. It can not necessarily set any foci.

    Traversal

    : A Traversal is both a Fold and a Setter. It is capable of both
    setting and getting multiple foci at once.

    Lens

    : A Lens is both a Getter and a Traversal. It is capable of getting
    and setting a single focus at a time.

    Review

    : A Review is an optic that is capable of being constructed
    from. Constructing allows you to supply a focus and get back a
    complete state. You cannot neccessarily use reviews to get or set
    any values.

    Prism

    : A Prism is both a Traversal and a Review. It is capable of getting
    and setting a single focus that may or may not exist. You can also
    use it to construct.

    Isomorphism

    : An Isomorphism is both a Lens and a Prism. They can be used to
    get, set, and construct. Isomorphisms have the property that they
    are reversable; You can take an isomorphism and flip it around
    so that getting the focus becomes setting the focus and setting
    becomes getting.

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

    def preview(self, state):
        # type: (S) -> Just[B]
        '''Previews a potentially non-existant focus within
        `state`. Returns `Just(focus)` if it exists, Nothing otherwise.

        Requires kind Fold.
        '''
        if not self._is_kind(Fold):
            raise TypeError('Must be an instance of Fold to .preview()')

        const = Functorisor(lambda a: Const(Nothing()),
                            lambda a: Const(Just(a)))
        return self.func(const, state).unwrap()

    def view(self, state):
        # type: (S) -> B
        '''Returns the focus within `state`. If multiple items are
        focused then it will attempt to join them together as a monoid.
        See `lenses.typeclass.mappend`.

        Requires kind Fold. This method will raise TypeError if the
        optic has no way to get any foci.

        For technical reasons, this method requires there to be at least
        one foci at the end of the view. It will raise ValueError when
        there is none.
        '''
        if not self._is_kind(Fold):
            raise TypeError('Must be an instance of Fold to .view()')

        guard = object()
        result = self.preview(state).maybe(guard)
        if result is guard:
            raise ValueError('No focus to view')
        return cast(B, result)

    def to_list_of(self, state):
        # type: (S) -> List[B]
        '''Returns a list of all the foci within `state`.

        Requires kind Fold. This method will raise TypeError if the
        optic has no way to get any foci.
        '''
        if not self._is_kind(Fold):
            raise TypeError('Must be an instance of Fold to .to_list_of()')

        consttup = Functorisor(lambda a: Const([]),
                               lambda a: Const([a]))
        return self.func(consttup, state).unwrap()

    def over(self, state, fn):
        # type: (S, Callable[[A], B]) -> T
        '''Applies a function `fn` to all the foci within `state`.

        Requires kind Setter. This method will raise TypeError when the
        optic has no way to set foci.
        '''
        if not self._is_kind(Setter):
            raise TypeError('Must be an instance of Setter to .over()')

        identfn = Functorisor(lambda a: Identity(a),
                              lambda a: Identity(fn(a)))
        return self.func(identfn, state).unwrap()

    def set(self, state, value):
        # type: (S, B) -> T
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
        # type: (LensLike) -> LensLike
        '''Composes another lens with this one. The result is a lens
        that feeds the foci of `self` into the state of `other`.
        '''
        return ComposedLens([self]).compose(other)

    def from_(self):
        # type: () -> LensLike
        '''Flips an isomorphism so that it works in the opposite
        direction. Only works if the lens is actually an isomorphism.

        Requires kind Isomorphism. Raises TypeError for non-isomorphic
        lenses.
        '''
        if not self._is_kind(Isomorphism):
            raise TypeError('Must be an instance of Isomorphism to .from_()')
        message = 'Optic has no implementation of .from_()'
        raise NotImplementedError(message)

    def re(self):
        # type: () -> LensLike
        if not self._is_kind(Review):
            raise TypeError('Must be an instance of Review to .re()')
        message = 'Optic has no implementation of .re()'
        raise NotImplementedError(message)

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
    '''An optic that wraps a getter function. A getter function is one
    that takes a state and returns a value derived from that state. The
    function is called on the focus before it is returned.

        >>> Getter(abs)
        Getter(<built-in function abs>)
        >>> Getter(abs).view(-1)
        1
    '''

    def __init__(self, getter):
        # type: (Callable[[S], A]) -> None
        self.getter = getter

    def func(self, f, state):
        return Const(typeclass.fmap(f(state).unwrap(), self.getter))

    def __repr__(self):
        return 'Getter({!r})'.format(self.getter)


class Traversal(Fold, Setter):
    pass


class Lens(Getter, Traversal):
    '''An optic that wraps a pair of getter and setter functions. A getter
    function is one that takes a state and returns a value derived from
    that state. A setter function takes an old state and a new value
    and uses them to construct a new state.

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
        >>> average = Lens(getter, setter)
        >>> average
        Lens(<function getter...>, <function setter...>)
        >>> average.view([1, 2, 4, 5])
        3
        >>> average.set([1, 2, 3], 4)
        [1, 2, 9]
    '''

    def __init__(self, getter, setter):
        # type: (Callable[[S], A], Callable[[S, B], T]) -> None
        self.getter = getter
        self.setter = setter

    def func(self, f, state):
        old_value = self.getter(state)
        fa = f(old_value)
        return typeclass.fmap(fa, lambda a: self.setter(state, a))

    def __repr__(self):
        return 'Lens({!r}, {!r})'.format(self.getter, self.setter)


class Review(LensLike):
    '''A review is an optic that is capable of constructing states from
    a focus.

        >>> Review(abs)
        Review(<built-in function abs>)
        >>> Review(abs).re().view(-1)
        1
    '''

    def __init__(self, pack):
        # type: (Callable[[B], T]) -> None
        self.pack = pack

    def re(self):
        return Getter(self.pack)

    def __repr__(self):
        return 'Review({!r})'.format(self.pack)


class Prism(Traversal, Review):
    '''A prism is an optic made from a pair of functions that pack and
    unpack a state where the unpacking process can potentially fail.

    `pack` is a function that takes a focus and returns that focus
    wrapped up in a new state. `unpack` is a function that takes a state
    and unpacks it to get a focus. The unpack function must return an
    instance of `lenses.maybe.Maybe`; `Just` if the unpacking succeeded
    and `Nothing` if the unpacking failed.

    Parsing strings is a common situation when prisms are useful:

        >>> from lenses.maybe import Nothing, Just
        >>> def pack(focus):
        ...     return str(focus)
        >>> def unpack(state):
        ...     try:
        ...         return Just(int(state))
        ...     except ValueError:
        ...         return Nothing()
        >>> Prism(unpack, pack)
        Prism(<function unpack ...>, <function pack ...>)
        >>> Prism(unpack, pack).preview('42')
        Just(42)
        >>> Prism(unpack, pack).preview('fourty two')
        Nothing()

    All prisms are also traversals that have exactly zero or one foci.
    '''

    def __init__(self, unpack, pack):
        self.unpack = unpack
        self.pack = pack

    def func(self, f, state):
        result = self.unpack(state)
        if result.is_nothing():
            return f.pure(state)
        return typeclass.fmap(f(result.unwrap()), self.pack)

    def __repr__(self):
        return 'Prism({!r}, {!r})'.format(self.unpack,
                                          self.pack)


class Isomorphism(Lens, Prism):
    '''A lens based on an isomorphism. An isomorphism can be formed by
    two functions that mirror each other; they can convert forwards
    and backwards between a state and a focus without losing
    information. The difference between this and a regular Lens is
    that here the backwards functions don't need to know anything about
    the original state in order to produce a new state.

    These equalities should hold for the functions you supply (given
    a reasonable definition for __eq__):

        backwards(forwards(state)) == state
        forwards(backwards(focus)) == focus

    These kinds of conversion functions are very common across the
    python ecosystem. For example, NumPy has `np.array` and
    `np.ndarray.tolist` for converting between python lists and its own
    arrays. Isomorphism makes it easy to store data in one form, but
    interact with it in a more convenient form.

        >>> Isomorphism(chr, ord)
        Isomorphism(<built-in function chr>, <built-in function ord>)
        >>> Isomorphism(chr, ord).view(65)
        'A'
        >>> Isomorphism(chr, ord).set(65, 'B')
        66

    Due to their symmetry, isomorphisms can be flipped, thereby swapping
    thier forwards and backwards functions:

        >>> flipped = Isomorphism(chr, ord).from_()
        >>> flipped
        Isomorphism(<built-in function ord>, <built-in function chr>)
        >>> flipped.view('A')
        65
    '''

    def __init__(self, forwards, backwards):
        # type: (Callable[[S], A], Callable[[B], T]) -> None
        self.forwards = forwards
        self.backwards = backwards

    def getter(self, state):
        return self.forwards(state)

    def setter(self, old_state, focus):
        return self.backwards(focus)

    def unpack(self, state):
        return Just(self.forwards(state))

    def pack(self, focus):
        return self.backwards(focus)

    def re(self):
        return Isomorphism(self.backwards, self.forwards)

    def from_(self):
        return Isomorphism(self.backwards, self.forwards)

    def func(self, f, state):
        return typeclass.fmap(f(self.forwards(state)), self.backwards)

    def __repr__(self):
        return 'Isomorphism({!r}, {!r})'.format(self.forwards,
                                                self.backwards)


class Equality(Isomorphism):
    pass


class ComposedLens(LensLike):
    '''A lenses representing the composition of several sub-lenses. This
    class tries to just pass operations down to the sublenses without
    imposing any constraints on what can happen. The sublenses are in
    charge of what capabilities they support.

        >>> import lenses
        >>> gi = lenses.optics.GetitemLens
        >>> ComposedLens((gi(0), gi(1)))
        GetitemLens(0) & GetitemLens(1)

    (The ComposedLens is represented above by the `&` symbol)
    '''

    def __init__(self, lenses=()):
        # type: (Iterable[LensLike]) -> None
        self.lenses = list(self._filter_lenses(lenses))

    @staticmethod
    def _filter_lenses(lenses):
        for lens in lenses:
            lenstype = type(lens)
            if lenstype is TrivialIso:
                continue
            elif lenstype is ComposedLens:
                for lens in lens.lenses:
                    yield lens
            else:
                yield lens

    def func(self, f, state):
        if not self.lenses:
            return TrivialIso().func(f, state)

        res = f
        for lens in reversed(self.lenses):
            res = res.update(lens.func)

        return res(state)

    def from_(self):
        return ComposedLens([l.from_() for l in reversed(self.lenses)])

    def re(self):
        return ComposedLens([l.re() for l in self.lenses])

    def compose(self, other):
        result = ComposedLens(self.lenses + [other])
        if len(result.lenses) == 0:
            return TrivialIso()
        elif len(result.lenses) == 1:
            return result.lenses[0]
        if result.kind() is None:
            raise RuntimeError('Optic has no valid type')
        return result

    def __repr__(self):
        return ' & '.join(str(l) for l in self.lenses)

    def _is_kind(self, cls):
        return all(lens._is_kind(cls) for lens in self.lenses)


class ErrorIso(Isomorphism):
    '''An optic that raises an exception whenever it tries to focus
    something. If `message is None` then the exception will be raised
    unmodified. If `message is not None` then when the lens is asked
    to focus something it will run `message.format(state)` and the
    exception will be called with the resulting formatted message as
    it's only argument. Useful for debugging.

        >>> ErrorIso(Exception())
        ErrorIso(Exception())
        >>> ErrorIso(Exception, '{}')  # doctest: +SKIP
        ErrorLens(<class 'Exception'>, '{}')
        >>> ErrorIso(Exception).view(True)
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        Exception
        >>> ErrorIso(Exception('An error occurred')).set(True, False)
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        Exception: An error occurred
        >>> ErrorIso(ValueError, 'applied to {}').view(True)
        Traceback (most recent call last):
          File "<stdin>", line 1, in ?
        ValueError: applied to True
    '''

    def __init__(self, exception, message=None):
        # type: (Exception, Optional[str]) -> None
        self.exception = exception
        self.message = message

    def func(self, f, state):
        if self.message is None:
            raise self.exception
        raise self.exception(self.message.format(state))

    def __repr__(self):
        if self.message is None:
            return 'ErrorIso({!r})'.format(self.exception)
        return 'ErrorIso({!r}, {!r})'.format(self.exception, self.message)


class TrivialIso(Isomorphism):
    '''A trivial isomorphism that focuses the whole state. It doesn't
    manipulate the state in any way. Mostly used as a "null" lens.
    Analogous to `lambda a: a`.

        >>> TrivialIso()
        TrivialIso()
        >>> TrivialIso().view(True)
        True
        >>> TrivialIso().set(True, False)
        False
    '''

    def __init__(self):
        # type: () -> None
        pass

    def forwards(self, state):
        return state

    def backwards(self, focus):
        return focus

    def __repr__(self):
        return 'TrivialIso()'

__all__ = [
    'LensLike', 'Fold', 'Setter', 'Getter', 'Traversal', 'Lens',
    'Review', 'Prism', 'Isomorphism', 'Equality', 'ComposedLens',
    'TrivialIso', 'ErrorIso',
]
