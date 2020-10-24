import pyrsistent as pyr
import pytest

from lenses import lens
import lenses.hooks.pyrsistent


def test_pvector_setitem():
    state = pyr.pvector([1, 2, 3])
    assert (lens[0] + 10)(state) == pyr.pvector([11, 2, 3])


def test_pvector_iter():
    state = pyr.pvector([1, 2, 3])
    assert (lens.Each() + 10)(state) == pyr.pvector([11, 12, 13])


def test_pmap_setitem():
    state = pyr.m(a=1, b=2, c=3)
    assert (lens["a"] + 10)(state) == pyr.m(a=11, b=2, c=3)


def test_pmap_iter():
    state = pyr.m(a=1, b=2, c=3)
    assert (lens.Each()[1] + 10)(state) == pyr.m(a=11, b=12, c=13)


def test_pset_iter():
    state = pyr.s(1, 2, 3)
    assert (lens.Each() + 10)(state) == pyr.s(11, 12, 13)


class PairR(pyr.PRecord):
    left = pyr.field()
    right = pyr.field()


def test_precord_setattr():
    state = PairR(left=1, right=2)
    assert (lens.left + 10)(state) == PairR(left=11, right=2)


def test_precord_iter():
    state = PairR(left=1, right=2)
    assert (lens.Each()[1] + 10)(state) == PairR(left=11, right=12)


class PairC(pyr.PClass):
    left = pyr.field()
    right = pyr.field()


def test_pclass_setattr():
    state = PairC(left=1, right=2)
    assert (lens.left + 10)(state) == PairC(left=11, right=2)
