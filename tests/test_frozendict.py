import frozendict
import pytest

from lenses import lens


def test_frozendict_setitem():
    state = frozendict.frozendict(one=1, two=2, three=3)
    result = frozendict.frozendict(one=11, two=2, three=3)
    assert lens['one'].set(11)(state) == result


def test_frozendict_setitem_nonstring():
    state = frozendict.frozendict({1: 'one', 2: 'two', 3: 'three'})
    result = frozendict.frozendict({1: 'four', 2: 'two', 3: 'three'})
    assert lens[1].set('four')(state) == result


def test_frozendict_get():
    state = frozendict.frozendict(one=1, two=2, three=3)
    result = frozendict.frozendict(one=1, two=2, three=3, four=4)
    assert lens.Get('four').set(4)(state) == result


def test_frozendict_iter():
    state = frozendict.frozendict(one=1, two=2, three=3)
    result = frozendict.frozendict(one=11, two=12, three=13)
    assert (lens.Each()[1] + 10)(state) == result
