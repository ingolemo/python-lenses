import collections

import pytest

import lenses
from lenses import lens

LensAndState = collections.namedtuple('LensAndState', 'lens state')
lenses_and_states = [
    LensAndState(lenses.trivial, None),
    LensAndState(lenses.getitem(0), [1, 2, 3]),
    LensAndState(lenses.getitem(0), (1, 2, 3)),
    LensAndState(lenses.getitem(0), {0: 'hello', 1: 'world'}),
]  # yapf: disable


@pytest.fixture(params=lenses_and_states)
def lns(request):
    return request.param


# Tests for lens rules and other invariants
def test_get_then_set(lns):
    '''if we get from a state and then immediately set it again we
    should get back the same state'''
    assert lns.lens.set(lns.state, lns.lens.get(lns.state)) == lns.state


def test_set_then_get(lns):
    '''if we set a state and immediately get it we should get back what
    we set'''
    obj = object()
    assert lns.lens.get(lns.lens.set(lns.state, obj)) == obj


def test_set_then_set(lns):
    '''if we set a state using a lens and then immediately set it again,
    it should be as though we only set it once.'''
    obj = object()
    assert (lns.lens.set(
        lns.lens.set(lns.state, obj), obj) == lns.lens.set(lns.state, obj))


# Tests for ensuring lenses work on different type of objects
def test_type_tuple():
    assert lens(((0, 0), (0, 0)))[0][1].set(1) == ((0, 1), (0, 0))


def test_type_namedtuple():
    Tup = collections.namedtuple('Tup', 'attr')
    assert lens(Tup(0)).attr.set(1) == Tup(1)


def test_type_list():
    assert lens([[0, 1], [2, 3]])[1][0].set(4) == [[0, 1], [4, 3]]
    with pytest.raises(AttributeError):
        assert lens([[0, 1], [2, 3]]).attr.set(4)


def test_type_dict():
    assert lens({1: 2, 3: 4})[1].set(5) == {1: 5, 3: 4}
    with pytest.raises(AttributeError):
        assert lens({1: 2, 3: 4}).attr.set(5)


def test_type_custom_class_copy_and_mutate():
    class C:
        def __init__(self, a, b):
            self.a = a
            self.b = b

        def __eq__(self, other):
            return self.a == other.a and self.b == other.b

    assert lens(C(C(0, 1), C(2, 3))).a.b.set(4) == C(C(0, 4), C(2, 3))


def test_type_custom_class_method_lens_setter():
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


# Tests to make sure types that are not supported by lenses return the
# right kinds of errors
def test_type_unsupported_no_setter():
    with pytest.raises(TypeError):
        lens(object())[0].set(None)
    with pytest.raises(AttributeError):
        lens(object()).attr.set(None)


# Tests for using lens combinators through a BoundLens
def test_boundlens_get():
    assert lens(10).get() == 10
    assert lens([1, 2, 3])[1].get() == 2


def test_boundlens_get_all():
    my_lens = lenses.both.compose(lenses.getitem(1))
    assert lens([[1, 2], [3, 4]], my_lens).get_all() == (2, 4)


def test_boundlens_set():
    assert lens(10).set(5) == 5
    assert lens([1, 2, 3])[1].set(5) == [1, 5, 3]


def test_boundlens_modify():
    assert lens(10).modify(lambda a: a + 1) == 11
    assert lens([1, 2, 3])[0].modify(lambda a: a + 5) == [6, 2, 3]


def test_boundlens_call_method():
    assert lens('hello').call_method('upper') == 'HELLO'


def test_boundlens_call_method_args():
    assert lens('h').call_method('center', 5) == '  h  '


def test_boundlens_call_method_kwargs():
    assert lens('h').call_method('encode', encoding='utf-8') == b'h'


def test_boundlens_add_lens():
    assert lens([1, 2]).add_lens(lenses.trivial) + [3] == [1, 2, 3]
    assert lens([1, 2]).add_lens(lenses.getitem(1)).set(3) == [1, 3]


def test_boundlens_add():
    assert lens(2) + 1 == 3
    assert lens([[1, 2], 3])[0] + [4] == [[1, 2, 4], 3]


def test_boundlens_subtract():
    assert lens(2) - 1 == 1


def test_boundlens_multiply():
    assert lens(2) * 2 == 4
    assert lens([[1, 2], [3]])[1] * 3 == [[1, 2], [3, 3, 3]]


def test_boundlens_divide():
    assert lens(10) / 2 == 5


def test_boundlens_informative_repr():
    obj = object()
    assert repr(obj) in repr(lens(obj))


# Tests for lenses and lens constructor function that are built into the
# library.
def test_lens_getattr_l():
    Tup = collections.namedtuple('Tup', 'attr')
    obj = Tup(1)
    assert lenses.getattr_l('attr').get(obj) == 1
    assert lenses.getattr_l('attr').set(obj, 2) == Tup(2)


def test_lens_getitem():
    assert lenses.getitem(0).get([1, 2, 3]) == 1
    assert lenses.getitem(0).set([1, 2, 3], 4) == [4, 2, 3]


def test_lens_trivial():
    obj = object()
    assert lenses.trivial.get(obj) is obj
    assert lenses.trivial.set(obj, None) is None


def test_lens_both():
    assert lenses.both.get(['1', '2']) == '12'
    assert lenses.both.set(['1', '2'], 4) == [4, 4]


def test_lens_item():
    data = {0: 'hello', 1: 'world'}
    my_lens = lenses.item(1)
    assert my_lens.get(data) == (1, 'world')
    assert my_lens.set(data, (2, 'everyone')) == {0: 'hello', 2: 'everyone'}
    with pytest.raises(LookupError):
        lenses.item(3).get(data)


def test_lens_item_by_value():
    data = {'hello': 0, 'world': 1}
    my_lens = lenses.item_by_value(1)
    assert my_lens.get(data) == ('world', 1)
    assert my_lens.set(data, ('everyone', 2)) == {'hello': 0, 'everyone': 2}
    with pytest.raises(LookupError):
        lenses.item_by_value(3).get(data)


def test_lens_tuple_l():
    data = {'hello': 0, 'world': 1}
    my_lens = lenses.tuple_l(lenses.getitem('hello'), lenses.getitem('world'))
    assert my_lens.get(data) == (0, 1)
    assert my_lens.set(data, (3, 4)) == {'hello': 3, 'world': 4}


# Tests for miscellaneous functions
def test_make_lens():
    my_lens = lenses.make_lens(lambda a: a[:-1], lambda a, s: a + '!')
    state = 'hello!'
    assert my_lens.get(state) == 'hello'
    assert my_lens.set(state, 'bye') == 'bye!'
    assert my_lens.modify(state, lambda a: a.replace('lo', 'p')) == 'help!'
