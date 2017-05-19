'''A python module for manipulating deeply nested data structures
without mutating them.

A simple overview for this module is available in the file `readme.md`
or at http://github.com/ingolemo/python-lenses . More detailed
information for each object is available in the relevant docstrings.
`help(lenses.Lens)` is particularly useful.

The entry point to this library is the `lens` function, which returns a
`Lens` object:

    >>> from lenses import lens
    >>> lens()
    UnboundLens(TrivialIso())
    >>> lens([])
    BoundLens([], TrivialIso())
'''

from typing import Optional

from .typevars import S, T
from . import optics
from .ui import Lens, UnboundLens, BoundLens


def lens(obj=None):
    # type: (Optional[S]) -> Lens[S, T, S, T]
    '''Returns a simple Lens bound to `obj`. If `obj is None` then the
    Lens object is unbound.'''
    if obj is None:
        return UnboundLens(optics.TrivialIso())
    return BoundLens(obj, optics.TrivialIso())
