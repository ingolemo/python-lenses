from typing import Callable

from .base import Isomorphism


class DecodeIso(Isomorphism):
    '''An isomorphism that decodes and encodes its focus on the fly.
    Lets you focus a byte string as a unicode string. The arguments have
    the same meanings as `bytes.decode`. Analogous to `bytes.decode`.

        >>> from lenses import lens
        >>> lens().decode_(encoding='utf8')
        Lens(None, DecodeIso('utf8', 'strict'))
        >>> lens(b'hello').decode_().get()  # doctest: +SKIP
        'hello'
        >>> lens(b'hello').decode_().set('world')  # doctest: +SKIP
        b'world'
    '''

    def __init__(self, encoding='utf-8', errors='strict'):
        # type: (str, str) -> None
        self.encoding = encoding
        self.errors = errors

    def forwards(self, state):
        return state.decode(self.encoding, self.errors)

    def backwards(self, focus):
        return focus.encode(self.encoding, self.errors)

    def __repr__(self):
        repr = 'DecodeIso({!r}, {!r})'
        return repr.format(self.encoding, self.errors)


class JsonIso(Isomorphism):
    '''An isomorphism that focuses a string containing json data as its
    parsed equivalent. Analogous to `json.loads`.

        >>> from lenses import lens
        >>> data = '[{"points": [4, 7]}]'
        >>> lens().json_()
        Lens(None, JsonIso())
        >>> lens(data).json_()[0]['points'][1].get()
        7
        >>> lens(data).json_()[0]['points'][0].set(8)
        '[{"points": [8, 7]}]'
    '''

    def __init__(self):
        # type: () -> None
        self.json_mod = __import__('json')

    def forwards(self, state):
        return self.json_mod.loads(state)

    def backwards(self, focus):
        return self.json_mod.dumps(focus)

    def __repr__(self):
        return 'JsonIso()'


class ListWrapIso(Isomorphism):
    '''An isomorphism that wraps its state up in a list. This is
    occasionally useful when you need to make hetrogenous data more
    uniform. Analogous to `lambda state: [state]`.

        >>> from lenses import lens
        >>> lens().listwrap_()
        Lens(None, ListWrapIso())
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
        # type: () -> None
        pass

    def forwards(self, state):
        return [state]

    def backwards(self, focus):
        return focus[0]

    def __repr__(self):
        return 'ListWrapIso()'


class NormalisingIso(Isomorphism):
    '''An isomorphism that applies a function as it sets a new focus
    without regard to the old state. It will get foci without
    transformation. This lens allows you to pre-process values before
    you set them, but still get values as they exist in the state.
    Useful for type conversions or normalising data.

    For best results, your normalisation function should be idempotent.
    That is, applying the function twice should have no effect:

        setter(setter(value)) == setter(value)

    Equivalent to `Isomorphism((lambda s: s), setter)`.

        >>> from lenses import lens
        >>> def real_only(num):
        ...     return num.real
        ...
        >>> lens().norm_(real_only)
        Lens(None, NormalisingIso(<function real_only at ...>))
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
        return 'NormalisingIso({!r})'.format(self.backwards)
