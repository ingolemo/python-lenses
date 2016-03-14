from lenses.maybe import Nothing, Just


def test_Maybe_mempty():
    assert Just(object()).mempty() == Nothing()


def test_Nothing_is_singleton():
    assert Nothing() is Nothing()


def test_Nothing_fmap():
    assert Nothing().fmap(str) is Nothing()


def test_Nothing_mappend_Nothing():
    assert Nothing().mappend(Nothing()) == Nothing()


def test_Nothing_mappend_Just():
    obj = object()
    assert Nothing().mappend(Just(obj)) == Just(obj)


def test_Nothing_pure():
    obj = object()
    assert Nothing().pure(obj) == Just(obj)


def test_Nothing_ap_Nothing():
    assert Nothing().ap(Nothing()) == Nothing()


def test_Nothing_ap_Just():
    assert Nothing().ap(Just(str)) == Nothing()


def test_Nothing_repr_invariant():
    assert repr(Nothing()) == repr(Nothing())


def test_Nothing_not_equals_Just():
    assert Nothing() != Just(object())


def test_Just_equals_Just_when_subobjects_equal():
    # maybe hypothesis can make this more rigourous
    obj1 = object()
    obj2 = object()
    assert (Just(obj1) == Just(obj2)) is bool(obj1 == obj2)


def test_Just_not_equals_Nothing():
    assert Just(object()) != Nothing()


def test_Just_fmap():
    assert Just(1).fmap(str) == Just(str(1))


def test_Just_mappend_Nothing():
    obj = object()
    assert Just(obj).mappend(Nothing()) == Just(obj)


def test_Just_mappend_Just():
    assert Just([1]).mappend(Just([2])) == Just([1, 2])


def test_Just_pure():
    obj = object()
    assert Just(object()).pure(obj) == Just(obj)


def test_Just_ap_Just():
    assert Just(1).ap(Just(str)) == Just(str(1))


def test_Just_ap_Nothing():
    assert Just(1).ap(Nothing()) == Nothing()


def test_Just_repr_conatins_subobject():
    obj = object()
    assert repr(obj) in repr(Just(obj))
