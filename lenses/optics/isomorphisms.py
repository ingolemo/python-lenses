from typing import Callable

from .base import Isomorphism


class DecodeIso(Isomorphism):
    """An isomorphism that decodes and encodes its focus on the fly.
    Lets you focus a byte string as a unicode string. The arguments have
    the same meanings as `bytes.decode`. Analogous to `bytes.decode`.

        >>> DecodeIso()
        DecodeIso('utf-8', 'strict')
        >>> DecodeIso().view(b'hello')  # doctest: +SKIP
        'hello'
        >>> DecodeIso().set(b'hello', 'world')  # doctest: +SKIP
        b'world'
    """

    def __init__(self, encoding: str = "utf-8", errors: str = "strict") -> None:
        self.encoding = encoding
        self.errors = errors

    def forwards(self, state):
        return state.decode(self.encoding, self.errors)

    def backwards(self, focus):
        return focus.encode(self.encoding, self.errors)

    def __repr__(self):
        repr = "DecodeIso({!r}, {!r})"
        return repr.format(self.encoding, self.errors)


class JsonIso(Isomorphism):
    """An isomorphism that focuses a string containing json data as its
    parsed equivalent. Analogous to `json.loads`.

        >>> JsonIso()
        JsonIso()
        >>> state = '[{"points": [4, 7]}]'
        >>> JsonIso().view(state) # doctest: +SKIP
        [{'points': [4, 7]}]
        >>> JsonIso().set(state, [{'points': [3]}])
        '[{"points": [3]}]'
    """

    def __init__(self) -> None:
        self.json_mod = __import__("json")

    def forwards(self, state):
        return self.json_mod.loads(state)

    def backwards(self, focus):
        return self.json_mod.dumps(focus)

    def __repr__(self):
        return "JsonIso()"


class NormalisingIso(Isomorphism):
    """An isomorphism that applies a function as it sets a new focus
    without regard to the old state. It will get foci without
    transformation. This lens allows you to pre-process values before
    you set them, but still get values as they exist in the state.
    Useful for type conversions or normalising data.

    For best results, your normalisation function should be idempotent.
    That is, applying the function twice should have no effect:

        setter(setter(value)) == setter(value)

    Equivalent to `Isomorphism((lambda s: s), setter)`.

        >>> def real_only(num):
        ...     return num.real
        ...
        >>> NormalisingIso(real_only)
        NormalisingIso(<function real_only at ...>)
        >>> NormalisingIso(real_only).view(1.0)
        1.0
        >>> NormalisingIso(real_only).set(1.0, 4+7j)
        4.0

    Types with constructors that do conversion are often good targets
    for this lens:

        >>> NormalisingIso(int).set(1, '4')
        4
    """

    def __init__(self, setter):
        self.backwards = setter

    def forwards(self, state):
        return state

    def __repr__(self):
        return "NormalisingIso({!r})".format(self.backwards)
