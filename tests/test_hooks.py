import collections

import pytest

import lenses.hooks as s


def test_setitem_imm_custom_class():
    class C(object):
        def __init__(self, item):
            self.item = item

        def __eq__(self, other):
            return self.item == other.item

        def _lens_setitem(self, key, value):
            return C(value)

    assert s.setitem_immutable(C(1), 0, 2) == C(2)


def test_setitem_imm_bytes():
    assert s.setitem_immutable(b'hello', 0, ord(b'j')) == b'jello'


def test_setitem_imm_list():
    assert s.setitem_immutable([1, 2, 3], 0, 4) == [4, 2, 3]


def test_setitem_imm_str():
    assert s.setitem_immutable(u'hello', 0, u'j') == u'jello'


def test_setitem_imm_tuple():
    assert s.setitem_immutable((1, 2, 3), 0, 4) == (4, 2, 3)


def test_setattr_imm_custom_class():
    class C(object):
        def __init__(self, attr):
            self.attr = attr

        def __eq__(self, other):
            return self.attr == other.attr

        def _lens_setattr(self, name, value):
            if name == 'fake_attr':
                return C(value)
            else:
                raise AttributeError(name)

    assert s.setattr_immutable(C(1), 'fake_attr', 2) == C(2)


def test_setattr_imm_custom_class_raw():
    class C(object):
        def __init__(self, attr):
            self.attr = attr

        def __eq__(self, other):
            return self.attr == other.attr

    assert s.setattr_immutable(C(1), 'attr', 2) == C(2)


def test_setattr_imm_namedtuple():
    Tup = collections.namedtuple('Tup', 'attr')
    assert s.setattr_immutable(Tup(1), 'attr', 2) == Tup(2)


def test_to_iter_custom_class():
    class C(object):
        def __init__(self, attr):
            self.attr = attr

        def __eq__(self, other):
            return self.attr == other.attr

        def _lens_to_iter(self):
            yield self.attr

    assert list(s.to_iter(C(1))) == [1]


def test_from_iter_custom_class():
    class C(object):
        def __init__(self, attr):
            self.attr = attr

        def __eq__(self, other):
            return self.attr == other.attr

        def _lens_from_iter(self, iterable):
            return C(next(iter(iterable)))

    assert s.from_iter(C(1), [2]) == C(2)


def test_from_iter_bytes():
    assert s.from_iter(b'', s.to_iter(b'123')) == b'123'


def test_from_iter_list():
    assert s.from_iter([], (1, 2, 3)) == [1, 2, 3]


def test_from_iter_set():
    assert s.from_iter(set(), [1, 2, 3]) == {1, 2, 3}


def test_from_iter_str():
    assert s.from_iter(u'', ['1', '2', '3']) == u'123'


def test_from_iter_tuple():
    assert s.from_iter((), [1, 2, 3]) == (1, 2, 3)


def test_from_iter_dict():
    data = {'jane': 5, 'jim': 6, 'joanne': 8}
    new_keys = [(k.capitalize(), v) for k, v in s.to_iter(data)]
    assert s.from_iter(data, new_keys) == {'Jane': 5, 'Jim': 6, 'Joanne': 8}


def test_from_iter_unknown():
    with pytest.raises(NotImplementedError):
        s.from_iter(object(), [1, 2, 3])
