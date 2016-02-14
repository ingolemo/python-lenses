import collections

import pytest

from lenses import lens, baselens


# Tests for using Lens' standard methods
def test_lens_get():
    assert lens(10).get() == 10
    assert lens([1, 2, 3])[1].get() == 2


def test_lens_get_all():
    assert lens([[1, 2], [3, 4]]).both_()[1].get_all() == (2, 4)


def test_lens_get_monoid():
    assert lens([[1, 2], [3, 4]]).both_().get_monoid() == [1, 2, 3, 4]


def test_lens_set():
    assert lens(10).set(5) == 5
    assert lens([1, 2, 3])[1].set(5) == [1, 5, 3]


def test_lens_modify():
    assert lens(10).modify(lambda a: a + 1) == 11
    assert lens([1, 2, 3])[0].modify(lambda a: a + 5) == [6, 2, 3]


def test_lens_call_method():
    assert lens('hello').call_method('upper') == 'HELLO'


def test_lens_call_method_args():
    assert lens('h').call_method('center', 5) == '  h  '


def test_lens_call_method_kwargs():
    assert lens('h').call_method('encode', encoding='utf-8') == b'h'


def test_lens_add_lens_baselens():
    assert lens([1, 2]).add_lens(baselens.TrivialLens()) + [3] == [1, 2, 3]
    assert lens([1, 2]).add_lens(baselens.GetitemLens(1)).set(3) == [1, 3]


def test_lens_add_lens_lens():
    assert lens([1, 2]).add_lens(lens()) + [3] == [1, 2, 3]
    assert lens([1, 2]).add_lens(lens()[1]).set(3) == [1, 3]


def test_lens_add_lens_bound_lens():
    with pytest.raises(ValueError):
        lens([1, 2]).add_lens(lens(1))


def test_lens_add_lens_bad_lens():
    with pytest.raises(TypeError):
        lens([1, 2]).add_lens(1)


def test_lens_bind():
    assert lens().bind([1, 2, 3]).get() == [1, 2, 3]


def test_lens_no_bind():
    with pytest.raises(ValueError):
        lens().get()


def test_lens_no_double_bind():
    with pytest.raises(ValueError):
        lens(1).bind(2)


# Testing that Lens properly passes though dunder methods
def test_lens_add():
    assert lens(2) + 1 == 3
    assert lens([[1, 2], 3])[0] + [4] == [[1, 2, 4], 3]


def test_lens_subtract():
    assert lens(2) - 1 == 1


def test_lens_multiply():
    assert lens(2) * 2 == 4
    assert lens([[1, 2], [3]])[1] * 3 == [[1, 2], [3, 3, 3]]


def test_lens_divide():
    assert lens(10) / 2 == 5


# Testing that you can use sublenses through Lens properly
def test_lens_trivial():
    assert lens(3).trivial_().get() == 3


def test_lens_getitem():
    assert lens([1, 2, 3]).getitem_(1).get() == 2


def test_lens_getitem_direct():
    assert lens([1, 2, 3])[1].get() == 2


def test_lens_getattr():
    nt = collections.namedtuple('nt', 'attr')
    assert lens(nt(3)).getattr_('attr').get() == 3


def test_lens_getattr_direct():
    nt = collections.namedtuple('nt', 'attr')
    assert lens(nt(3)).attr.get() == 3


def test_lens_both():
    assert lens([1, 2]).both_().get_all() == (1, 2)


def test_lens_nonexistant_sublens():
    with pytest.raises(AttributeError):
        lens(3).flobadob_()


# misc Lens tests
def test_lens_informative_repr():
    obj = object()
    assert repr(obj) in repr(lens(obj))
