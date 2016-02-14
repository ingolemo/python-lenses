from lenses import MethodLens


def test_methodlens():
    class C(object):

        def __init__(self, a):
            self.a = a

        def attr_get(self):
            return self.a + 100

        def attr_set(self, new_value):
            return type(self)(new_value - 100)

        attr = MethodLens(attr_get, attr_set, doc='focuses self.a + 100')

    assert C(3).attr().get() == 103
    assert (C(3).attr().set(107)).a == 7
    assert (C(4).attr() + 5).a == 9


def test_methodlens_decorator():
    class C(object):

        def __init__(self, a):
            self.a = a

        @MethodLens
        def attr(self):
            return self.a + 100

        @attr.setter
        def attr(self, new_value):
            return type(self)(new_value - 100)

    assert C(3).attr().get() == 103
    assert (C(3).attr().set(107)).a == 7
    assert (C(4).attr() + 5).a == 9


def test_methodlens_property():
    class C(object):

        def __init__(self, a):
            self.a = a

        @MethodLens
        def attr(self):
            return self.a + 100

        @property
        @attr.setter
        def attr(self, new_value):
            return type(self)(new_value - 100)

    assert C(3).attr.get() == 103
    assert (C(3).attr.set(107)).a == 7
    assert (C(4).attr + 5).a == 9
