import collections

import pytest

from lenses import lens, optics, maybe


# Tests for using Lens' standard methods
def test_lens_get():
    assert lens(10).get() == 10
    assert lens([1, 2, 3])[1].get() == 2


def test_lens_get_state_keyword():
    assert lens()[1].get(state=[1, 2, 3]) == 2


def test_lens_get_all():
    assert lens([[1, 2], [3, 4]]).both_()[1].get_all() == [2, 4]


def test_lens_get_all_state_keyword():
    assert lens().each_().get_all(state=[1, 2, 3]) == [1, 2, 3]


def test_lens_get_monoid():
    assert lens([[1, 2], [3, 4]]).both_().get_monoid() == [1, 2, 3, 4]


def test_lens_get_monoid_state_keyword():
    assert lens().each_().get_monoid(state=[1, 2, 3]) == 6


def test_lens_set():
    assert lens(10).set(5) == 5
    assert lens([1, 2, 3])[1].set(5) == [1, 5, 3]


def test_lens_set_state_keyword():
    assert lens()[1].set(4, state=[1, 2, 3]) == [1, 4, 3]


def test_lens_modify():
    assert lens(10).modify(lambda a: a + 1) == 11
    assert lens([1, 2, 3])[0].modify(lambda a: a + 5) == [6, 2, 3]


def test_lens_modify_state_keyword():
    assert lens()[1].modify(str, state=[1, 2, 3]) == [1, '2', 3]


def test_lens_call():
    assert lens('hello').call('upper') == 'HELLO'


def test_lens_call_implicitly():
    assert lens('hello').call_upper() == 'HELLO'


def test_lens_call_args():
    assert lens('h').call('center', 5) == '  h  '


def test_lens_call_args_implicitly():
    assert lens('h').call_center(5) == '  h  '


def test_lens_call_kwargs():
    assert lens('h').call('encode', encoding='utf-8') == b'h'


def test_lens_call_kwargs_implicitly():
    assert lens('h').call_encode(encoding='utf-8') == b'h'


def test_lens_call_state_keyword():
    assert lens()[1].call('union', {4}, state=[1, {2}, 3]) == [1, {2, 4}, 3]


def test_lens_call_mut():
    assert lens([3, 1, 2]).call_mut('sort') == [1, 2, 3]


def test_lens_call_mut_implicitly():
    assert lens([3, 1, 2]).call_mut_sort() == [1, 2, 3]


def test_lens_call_mut_args():
    assert lens([1, 2]).call_mut('append', 3) == [1, 2, 3]


def test_lens_call_mut_args_implicitly():
    assert lens([1, 2]).call_mut_append(3) == [1, 2, 3]


def test_lens_call_mut_kwargs():
    result = lens(['eine', 'un', 'one']).call_mut('sort', key=len)
    assert result == ['un', 'one', 'eine']


def test_lens_call_mut_kwargs_implicitly():
    result = lens(['eine', 'un', 'one']).call_mut_sort(key=len)
    assert result == ['un', 'one', 'eine']


def test_lens_call_mut_deep():
    state = [object(), object()]
    result = lens(state).call_mut('append', object())
    assert result[0] is not state[0]


def test_lens_call_mut_shallow():
    state = [object(), object()]
    result = lens(state).call_mut('append', object(), shallow=True)
    assert result[0] is state[0]


def test_lens_call_mut_state_keyword():
    assert lens().call_mut('append', 3, state=[1, 2]) == [1, 2, 3]


def test_lens_construct():
    obj = object()
    assert lens(obj).just_().construct() == maybe.Just(obj)


def test_lens_construct_focus_keyword():
    obj = object()
    assert lens().just_().construct(focus=obj) == maybe.Just(obj)


def test_lens_construct_composed():
    obj = object()
    assert lens(obj).just_().iso_(int, str).construct() == maybe.Just(str(obj))


def test_lens_add_lens_trivial_LensLike():
    assert lens([1, 2]).add_lens(optics.TrivialIso()) + [3] == [1, 2, 3]


def test_lens_add_lens_nontrivial_LensLike():
    assert lens([1, 2]).add_lens(optics.GetitemLens(1)).set(3) == [1, 3]


def test_lens_add_lens_trivial_lens():
    assert lens([1, 2]).add_lens(lens()) + [3] == [1, 2, 3]


def test_lens_add_lens_nontrivial_lens():
    assert lens([1, 2]).add_lens(lens()[1]).set(3) == [1, 3]


def test_lens_add_lens_bound_lens():
    with pytest.raises(ValueError):
        lens([1, 2]).add_lens(lens(1))


def test_lens_add_lens_bad_lens():
    with pytest.raises(TypeError):
        lens([1, 2]).add_lens(1)


def test_lens_bind():
    assert lens().bind([1, 2, 3]).get() == [1, 2, 3]


def test_lens_no_bind():
    with pytest.raises(ValueError):
        lens().get()


def test_lens_no_double_bind():
    with pytest.raises(ValueError):
        lens(1).bind(2)


def test_lens_flip():
    l = lens().iso_(str, int).flip()
    assert l.bind('1').get() == 1


def test_lens_flip_composed():
    l = lens().decode_().json_().flip()
    assert l.bind([1, 2, 3]).get() == b'[1, 2, 3]'


def test_lens_flip_composed_not_isomorphism():
    with pytest.raises(TypeError):
        lens().decode_()[0].flip()


def test_lens_flip_bound():
    with pytest.raises(ValueError):
        lens(1).iso_(str, int).flip()


def test_lens_flip_not_isomorphism():
    with pytest.raises(TypeError):
        lens()[1].flip()


def test_lens_descriptor():
    class MyClass(object):

        def __init__(self, items):
            self._private_items = items

        def __eq__(self, other):
            return self._private_items == other._private_items

        first = lens()._private_items[0]
    assert MyClass([1, 2, 3]).first.set(4) == MyClass([4, 2, 3])


def test_lens_descriptor_doesnt_bind_from_class():
    class MyClass(object):

        def __init__(self, items):
            self._private_items = items

        def __eq__(self, other):
            return self._private_items == other._private_items

        first = lens()._private_items[0]

    assert MyClass.first.state is None


def test_lens_descriptor_zoom():
    class MyClass(object):

        def __init__(self, items):
            self._private_items = items

        def __eq__(self, other):
            return self._private_items == other._private_items

        def __repr__(self):
            return'M({!r})'.format(self._private_items)

        first = lens()._private_items[0]

    data = (MyClass([1, 2, 3]),)
    assert lens(data)[0].first.get() == 1
    assert lens(data)[0].first.set(4) == (MyClass([4, 2, 3]),)


def test_lens_error_on_bound_and_state():
    with pytest.raises(ValueError):
        lens([1, 2, 3])[1].get(state=[4, 5, 6])


def test_lens_error_on_unbound_and_no_state():
    with pytest.raises(ValueError):
        lens()[1].get()


# Testing that Lens properly passes though dunder methods
def test_lens_add():
    assert lens(2) + 1 == 3
    assert lens([[1, 2], 3])[0] + [4] == [[1, 2, 4], 3]


def test_lens_subtract():
    assert lens(2) - 1 == 1


def test_lens_multiply():
    assert lens(2) * 2 == 4
    assert lens([[1, 2], [3]])[1] * 3 == [[1, 2], [3, 3, 3]]


def test_lens_divide():
    assert lens(10) / 2 == 5


# Testing that you can use sublenses through Lens properly
def test_lens_trivial():
    assert lens(3).get() == 3


def test_lens_getitem():
    assert lens([1, 2, 3]).getitem_(1).get() == 2


def test_lens_getitem_direct():
    assert lens([1, 2, 3])[1].get() == 2


def test_lens_getattr():
    nt = collections.namedtuple('nt', 'attr')
    assert lens(nt(3)).getattr_('attr').get() == 3


def test_lens_getattr_direct():
    nt = collections.namedtuple('nt', 'attr')
    assert lens(nt(3)).attr.get() == 3


def test_lens_both():
    assert lens([1, 2]).both_().get_all() == [1, 2]


def test_lens_nonexistant_sublens():
    with pytest.raises(AttributeError):
        lens(3).flobadob_()


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
    class C(object):

        def __init__(self, a, b):
            self.a = a
            self.b = b

        def __eq__(self, other):
            return self.a == other.a and self.b == other.b

    assert lens(C(C(0, 1), C(2, 3))).a.b.set(4) == C(C(0, 4), C(2, 3))


def test_type_custom_class_lens_setattr():
    class C(object):

        def __init__(self, a):
            self._a = a

        @property
        def a(self):
            return self._a

        def __eq__(self, other):
            return self.a == other.a

        def _lens_setattr(self, key, value):
            if key == 'a':
                return C(value)

    assert lens(C(C(9))).a.a.set(4) == C(C(4))


def test_type_custom_class_immutable():
    class C(object):

        def __init__(self, a):
            self._a = a

        @property
        def a(self):
            return self._a

    with pytest.raises(AttributeError):
        lens(C(9)).a.set(7)


def test_type_unsupported_no_setitem():
    with pytest.raises(TypeError):
        lens(object())[0].set(None)


def test_type_unsupported_no_setattr():
    with pytest.raises(AttributeError):
        lens(object()).attr.set(None)


# misc Lens tests
def test_lens_informative_repr():
    obj = object()
    assert repr(obj) in repr(lens(obj))
