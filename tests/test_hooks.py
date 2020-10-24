import collections

import pytest
import hypothesis
from hypothesis import strategies as strats

import lenses.hooks as s


class Box(object):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def __contains__(self, item):
        return item in self.value

    def _lens_contains_add(self, item):
        return Box(s.contains_add(self.value, item))

    def _lens_contains_remove(self, item):
        return Box(s.contains_remove(self.value, item))


def test_setitem_imm_custom_class():
    class C(object):
        def __init__(self, item):
            self.item = item

        def __eq__(self, other):
            return self.item == other.item

        def _lens_setitem(self, key, value):
            return C(value)

    assert s.setitem(C(1), 0, 2) == C(2)


def test_setitem_imm_bytes():
    assert s.setitem(b"hello", 0, ord(b"j")) == b"jello"


def test_setitem_imm_list():
    assert s.setitem([1, 2, 3], 0, 4) == [4, 2, 3]


def test_setitem_imm_str():
    assert s.setitem(u"hello", 0, u"j") == u"jello"


def test_setitem_imm_tuple():
    assert s.setitem((1, 2, 3), 0, 4) == (4, 2, 3)


def test_setattr_imm_custom_class():
    class C(object):
        def __init__(self, attr):
            self.attr = attr

        def __eq__(self, other):
            return self.attr == other.attr

        def _lens_setattr(self, name, value):
            if name == "fake_attr":
                return C(value)
            else:
                raise AttributeError(name)

    assert s.setattr(C(1), "fake_attr", 2) == C(2)


def test_setattr_imm_custom_class_raw():
    class C(object):
        def __init__(self, attr):
            self.attr = attr

        def __eq__(self, other):
            return self.attr == other.attr

    assert s.setattr(C(1), "attr", 2) == C(2)


def test_setattr_imm_namedtuple():
    Tup = collections.namedtuple("Tup", "attr")
    assert s.setattr(Tup(1), "attr", 2) == Tup(2)


@hypothesis.given(
    strats.one_of(
        strats.lists(strats.integers()),
        strats.iterables(strats.integers()).map(tuple),
        strats.dictionaries(strats.text(), strats.integers()),
        strats.iterables(strats.integers()).map(set),
        strats.lists(strats.integers()).map(Box),
    )
)
def test_contains(container):
    item = object()
    added = s.contains_add(container, item)
    assert isinstance(added, type(container))
    assert item in added
    removed = s.contains_remove(added, item)
    assert isinstance(removed, type(container))
    assert item not in removed


def test_contains_add_failure():
    with pytest.raises(NotImplementedError):
        s.contains_add(True, object())


def test_contains_remove_failure():
    with pytest.raises(NotImplementedError):
        s.contains_remove(True, object())


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
    assert s.from_iter(b"", s.to_iter(b"123")) == b"123"


def test_from_iter_list():
    assert s.from_iter([], (1, 2, 3)) == [1, 2, 3]


def test_from_iter_set():
    assert s.from_iter(set(), [1, 2, 3]) == {1, 2, 3}


def test_from_iter_str():
    assert s.from_iter(u"", ["1", "2", "3"]) == u"123"


def test_from_iter_tuple():
    assert s.from_iter((), [1, 2, 3]) == (1, 2, 3)


def test_from_iter_namedtuple():
    Tup = collections.namedtuple("Tup", "attr1 attr2 attr3")
    iterTup = s.from_iter(Tup(1, 2, 3), [4, 5, 6])
    assert iterTup == Tup(4, 5, 6)
    assert type(iterTup) is Tup


def test_from_iter_dict():
    data = {"jane": 5, "jim": 6, "joanne": 8}
    new_keys = [(k.capitalize(), v) for k, v in s.to_iter(data)]
    assert s.from_iter(data, new_keys) == {"Jane": 5, "Jim": 6, "Joanne": 8}


def test_from_iter_unknown():
    with pytest.raises(NotImplementedError):
        s.from_iter(object(), [1, 2, 3])
