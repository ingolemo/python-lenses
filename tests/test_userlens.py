import pytest

import lenses
from lenses import lens


# Tests for using lens combinators through a UserLens
def test_userlens_get():
    assert lens(10).get() == 10
    assert lens([1, 2, 3])[1].get() == 2


def test_userlens_get_all():
    my_lens = lenses.both().compose(lenses.getitem(1))
    assert lens([[1, 2], [3, 4]], my_lens).get_all() == (2, 4)


def test_userlens_set():
    assert lens(10).set(5) == 5
    assert lens([1, 2, 3])[1].set(5) == [1, 5, 3]


def test_userlens_modify():
    assert lens(10).modify(lambda a: a + 1) == 11
    assert lens([1, 2, 3])[0].modify(lambda a: a + 5) == [6, 2, 3]


def test_userlens_call_method():
    assert lens('hello').call_method('upper') == 'HELLO'


def test_userlens_call_method_args():
    assert lens('h').call_method('center', 5) == '  h  '


def test_userlens_call_method_kwargs():
    assert lens('h').call_method('encode', encoding='utf-8') == b'h'


def test_userlens_add_lens():
    assert lens([1, 2]).add_lens(lenses.trivial()) + [3] == [1, 2, 3]
    assert lens([1, 2]).add_lens(lenses.getitem(1)).set(3) == [1, 3]


def test_userlens_bind():
    assert lens().bind([1, 2, 3]).get() == [1, 2, 3]


def test_userlens_no__bind():
    with pytest.raises(ValueError):
        lens().get()


def test_userlens_no_double_bind():
    with pytest.raises(ValueError):
        lens(1).bind(2).get()


def test_userlens_add():
    assert lens(2) + 1 == 3
    assert lens([[1, 2], 3])[0] + [4] == [[1, 2, 4], 3]


def test_userlens_subtract():
    assert lens(2) - 1 == 1


def test_userlens_multiply():
    assert lens(2) * 2 == 4
    assert lens([[1, 2], [3]])[1] * 3 == [[1, 2], [3, 3, 3]]


def test_userlens_divide():
    assert lens(10) / 2 == 5


def test_userlens_informative_repr():
    obj = object()
    assert repr(obj) in repr(lens(obj))
