import collections

import pytest

from lenses import lens


def test_trivial_lens():
    obj = object()
    l = lens(obj)
    assert l.get() == obj
    assert l.set(None) == None


def test_tuple_lens():
    assert lens(((0, 0), (0, 0)))[0][1].set(1) == ((0, 1), (0, 0))


def test_namedtuple_lens():
    Tup = collections.namedtuple('Tup', 'attr')
    assert lens(Tup(0)).attr.set(1) == Tup(1)


def test_list_lens():
    assert lens([[0, 1], [2, 3]])[1][0].set(4) == [[0, 1], [4, 3]]
    with pytest.raises(AttributeError):
        assert lens([[0, 1], [2, 3]]).attr.set(4)


def test_dict_lens():
    assert lens({1: 2, 3: 4})[1].set(5) == {1: 5, 3: 4}
    with pytest.raises(AttributeError):
        assert lens({1: 2, 3: 4}).attr.set(5)


def test_custom_class_lens():
    class C:
        def __init__(self, a, b):
            self.a = a
            self.b = b

        def __eq__(self, other):
            return self.a == other.a and self.b == other.b

    assert lens(C(C(0, 1), C(2, 3))).a.b.set(4) == C(C(0, 4), C(2, 3))


def test_no_setter():
    with pytest.raises(TypeError):
        lens(object())[0].set(None)
    with pytest.raises(AttributeError):
        lens(object()).attr.set(None)


def test_lens_setter():
    class C:
        def __init__(self, a, b):
            self.a = a
            self.b = b

        def __eq__(self, other):
            return self.a == other.a and self.b == other.b

        def lens_setter(self, kind, key, value):
            if kind == 'setattr':
                if key == 'a':
                    return C(value, self.b)
                elif key == 'b':
                    return C(self.a, value)

    assert lens(C(C(0, 1), C(2, 3))).a.b.set(4) == C(C(0, 4), C(2, 3))


def test_get():
    assert lens(10).get() == 10
    assert lens([1, 2, 3])[1].get() == 2


def test_set():
    assert lens(10).set(5) == 5
    assert lens([1, 2, 3])[1].set(5) == [1, 5, 3]


def test_modify():
    assert lens(10).modify(lambda a: a + 1) == 11
    assert lens([1, 2, 3])[0].modify(lambda a: a + 5) == [6, 2, 3]


def test_call_method():
    assert lens('hello').call_method('upper') == 'HELLO'


def test_call_method_args():
    assert lens('h').call_method('center', 5) == '  h  '


def test_call_method_kwargs():
    assert lens('h').call_method('encode', encoding='utf-8') == b'h'


def test_adding_lens():
    assert lens(2) + 1 == 3
    assert lens([[1, 2], 3])[0] + [4] == [[1, 2, 4], 3]


def test_subtracting_lens():
    assert lens(2) - 1 == 1


def test_multiply_lens():
    assert lens(2) * 2 == 4
    assert lens([[1, 2], [3]])[1] * 3 == [[1, 2], [3, 3, 3]]


def test_divide_lens():
    assert lens(10) / 2 == 5


def test_informative_lens_repr():
    obj = object()
    assert repr(obj) in repr(lens(obj))
