from lenses.functorisor import Functorisor


def test_Functorisor_get_pure():
    f = Functorisor(lambda a: [], lambda a: [a])
    assert f.get_pure(1) == []


def test_Functorisor_call():
    f = Functorisor(lambda a: [], lambda a: [a])
    assert f(1) == [1]


def test_Functorisor_fmap():
    f = Functorisor(lambda a: [], lambda a: [a])
    assert f.fmap(lambda a: a + 1)(1) == f(2)


def test_Functorisor_replace_func():
    f = Functorisor(lambda a: [], lambda a: [a])
    assert f.replace_func(lambda a: None)(1) is None
