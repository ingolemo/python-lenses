from lenses.functorisor import Functorisor


def test_Functorisor_pure():
    f = Functorisor(lambda a: [], lambda a: [a])
    assert f.pure(1) == []


def test_Functorisor_call():
    f = Functorisor(lambda a: [], lambda a: [a])
    assert f(1) == [1]


def test_Functorisor_map():
    f = Functorisor(lambda a: [], lambda a: [a])
    assert f.map(lambda a: a + 1)(1) == f(2)
