from lenses.identity import Identity


def test_identity_eq():
    obj = object()
    assert Identity(obj) == Identity(obj)


def test_identity_not_eq():
    assert Identity(0) != 0


def test_identity_pure():
    obj = object()
    assert Identity(1).pure(obj) == Identity(obj)


def test_identity_descriptive_repr():
    obj = object()
    assert repr(obj) in repr(Identity(obj))
