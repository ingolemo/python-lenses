"""A python module for manipulating deeply nested data structures
without mutating them.

A simple overview for this module is available in the readme or
at [http://github.com/ingolemo/python-lenses] . More detailed
information for each object is available in the relevant
docstrings. `help(lenses.UnboundLens)` is particularly useful.

The entry point to this library is the `lens` object:

    >>> from lenses import lens
    >>> lens
    UnboundLens(TrivialIso())

You can also obtain a bound lens with the `bind` function.

    >>> from lenses import bind
    >>> bind([1, 2, 3])
    BoundLens([1, 2, 3], TrivialIso())
"""

from typing import TypeVar

from . import optics
from . import ui

# included so you can run pydoc lenses.UnboundLens
from .ui import UnboundLens

S = TypeVar("S")


def bind(state: S) -> ui.BoundLens[S, S, S, S]:
    "Returns a simple BoundLens object bound to `state`."
    return ui.BoundLens(state, optics.TrivialIso())


lens = ui.UnboundLens(optics.TrivialIso())  # type: ui.UnboundLens

__all__ = ["lens", "bind", "optics"]
