import pytest

from lenses.maybe import Nothing, Just
import lenses


def test_Nothing_map():
    assert Nothing().map(str) == Nothing()


def test_Nothing_add_Nothing():
    assert Nothing() + Nothing() == Nothing()


def test_Nothing_add_Just():
    obj = object()
    assert Nothing() + Just(obj) == Just(obj)


def test_Nothing_repr_invariant():
    assert repr(Nothing()) == repr(Nothing())


def test_Nothing_iter():
    assert list(Nothing()) == []


def test_Nothing_from_iter():
    assert lenses.hooks.from_iter(Just(1), []) == Nothing()


def test_Nothing_not_equals_Just():
    assert Nothing() != Just(object())


def test_Nothing_maybe():
    obj = object()
    assert Nothing().maybe() == None


def test_Nothing_unwrap():
    with pytest.raises(ValueError):
        Nothing().unwrap()


def test_Just_equals_Just_when_subobjects_equal():
    # maybe hypothesis can make this more rigourous
    obj1 = object()
    obj2 = object()
    assert (Just(obj1) == Just(obj2)) is bool(obj1 == obj2)


def test_Just_not_equals_Nothing():
    assert Just(object()) != Nothing()


def test_Just_not_equals_object():
    obj = object
    assert Just(obj) != obj


def test_Just_map():
    assert Just(1).map(str) == Just(str(1))


def test_Just_add_Nothing():
    obj = object()
    assert Just(obj) + Nothing() == Just(obj)


def test_Just_add_Just():
    assert Just([1]) + Just([2]) == Just([1, 2])


def test_Just_repr_conatins_subobject():
    obj = object()
    assert repr(obj) in repr(Just(obj))


def test_Just_iter():
    obj = object()
    assert list(Just(obj)) == [obj]


def test_Just_from_iter():
    obj = object()
    assert lenses.hooks.from_iter(Nothing(), [obj]) == Just(obj)


def test_Just_maybe():
    obj = object()
    assert Just(obj).maybe() is obj

def test_Just_unwrap():
    obj = object()
    assert Just(obj).unwrap() is obj
