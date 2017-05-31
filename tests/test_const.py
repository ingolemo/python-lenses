from lenses import const


def test_const_eq():
    obj = object()
    assert const.Const(obj) == const.Const(obj)


def test_const_not_eq():
    assert const.Const(0) != 0


def test_const_pure():
    assert const.Const([1, 2]).pure([1, 2, 3]) == const.Const([])
    assert const.Const((1, 2)).pure((1, 2)) == const.Const((0, 0))


def test_const_descriptive_repr():
    obj = object()
    assert repr(obj) in repr(const.Const(obj))
