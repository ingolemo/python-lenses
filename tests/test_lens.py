import collections

import pytest

from lenses import lens, bind, optics, maybe


# Tests for using Lens' standard methods
def test_lens_get():
    assert lens.get()(10) == 10
    assert lens[1].get()([1, 2, 3]) == 2


def test_lens_collect():
    assert lens.Both()[1].collect()([[1, 2], [3, 4]]) == [2, 4]


def test_lens_get_monoid():
    assert lens.Both().get_monoid()([[1, 2], [3, 4]]) == [1, 2, 3, 4]


def test_lens_set():
    assert lens.set(5)(10) == 5
    assert lens[1].set(5)([1, 2, 3]) == [1, 5, 3]


def test_lens_modify():
    assert lens.modify(lambda a: a + 1)(10) == 11
    assert lens[0].modify(lambda a: a + 5)([1, 2, 3]) == [6, 2, 3]


def test_lens_call():
    assert lens.call('upper')('hello') == 'HELLO'


def test_lens_call_implicitly():
    assert lens.call_upper()('hello') == 'HELLO'


def test_lens_call_args():
    assert lens.call('center', 5)('h') == '  h  '


def test_lens_call_args_implicitly():
    assert lens.call_center(5)('h') == '  h  '


def test_lens_call_kwargs():
    assert lens.call('encode', encoding='utf-8')('h') == b'h'


def test_lens_call_kwargs_implicitly():
    assert lens.call_encode(encoding='utf-8')('h') == b'h'


def test_lens_call_mut():
    assert lens.call_mut('sort')([3, 1, 2]) == [1, 2, 3]


def test_lens_call_mut_implicitly():
    assert lens.call_mut_sort()([3, 1, 2]) == [1, 2, 3]


def test_lens_call_mut_args():
    assert lens.call_mut('append', 3)([1, 2]) == [1, 2, 3]


def test_lens_call_mut_args_implicitly():
    assert lens.call_mut_append(3)([1, 2]) == [1, 2, 3]


def test_lens_call_mut_kwargs():
    result = lens.call_mut('sort', key=len)(['eine', 'un', 'one'])
    assert result == ['un', 'one', 'eine']


def test_lens_call_mut_kwargs_implicitly():
    result = lens.call_mut_sort(key=len)(['eine', 'un', 'one'])
    assert result == ['un', 'one', 'eine']


def test_lens_call_mut_deep():
    state = [object(), object()]
    result = lens.call_mut('append', object())(state)
    assert result[0] is not state[0]


def test_lens_call_mut_shallow():
    state = [object(), object()]
    result = lens.call_mut('append', object(), shallow=True)(state)
    assert result[0] is state[0]


def test_lens_construct():
    obj = object()
    assert lens.Just().construct(obj) == maybe.Just(obj)


def test_lens_construct_composed():
    obj = object()
    assert lens.Just().Iso(int, str).construct(obj) == maybe.Just(str(obj))


def test_lens_add_lens_trivial_lens():
    my_lens = bind([1, 2]) & lens
    assert my_lens + [3] == [1, 2, 3]


def test_lens_add_lens_nontrivial_lens():
    my_lens = bind([1, 2]) & lens[1]
    assert my_lens.set(3) == [1, 3]


def test_lens_add_lens_bound_lens():
    with pytest.raises(TypeError):
        bind([1, 2]) & bind(1)


def test_lens_add_lens_invalid():
    with pytest.raises(TypeError):
        bind([1, 2]) & 1


def test_unbound_lens_add_lens_trivial_lens():
    my_lens = lens & lens
    assert (my_lens + [3])([1, 2]) == [1, 2, 3]


def test_unbound_lens_add_lens_nontrivial_lens():
    my_lens = lens & lens[1]
    assert my_lens.set(3)([1, 2]) == [1, 3]


def test_unbound_lens_add_lens_bound_lens():
    with pytest.raises(TypeError):
        lens & bind(1)


def test_unbound_lens_add_lens_invalid():
    with pytest.raises(TypeError):
        lens & 1


def test_lens_add_lens_bad_lens():
    with pytest.raises(TypeError):
        bind([1, 2]) & 1


def test_lens_flip():
    l = lens.Iso(str, int).flip()
    assert l.get()('1') == 1


def test_lens_flip_composed():
    l = lens.Decode().Json().flip()
    assert l.get()([1, 2, 3]) == b'[1, 2, 3]'


def test_lens_flip_composed_not_isomorphism():
    with pytest.raises(TypeError):
        lens.Decode()[0].flip()


def test_lens_flip_not_isomorphism():
    with pytest.raises(TypeError):
        lens[1].flip()


def test_lens_descriptor():
    class MyClass(object):
        def __init__(self, items):
            self._private_items = items

        def __eq__(self, other):
            return self._private_items == other._private_items

        first = lens._private_items[0]

    assert MyClass([1, 2, 3]).first.set(4) == MyClass([4, 2, 3])


def test_lens_descriptor_doesnt_bind_from_class():
    class MyClass(object):
        def __init__(self, items):
            self._private_items = items

        def __eq__(self, other):
            return self._private_items == other._private_items

        first = lens._private_items[0]

    import lenses
    assert isinstance(MyClass.first, lenses.ui.UnboundLens)


def test_lens_descriptor_zoom():
    class MyClass(object):
        def __init__(self, items):
            self._private_items = items

        def __eq__(self, other):
            return self._private_items == other._private_items

        def __repr__(self):
            return 'M({!r})'.format(self._private_items)

        first = lens._private_items[0]

    data = (MyClass([1, 2, 3]),)
    assert bind(data)[0].first.get() == 1
    assert bind(data)[0].first.set(4) == (MyClass([4, 2, 3]),)


def test_lens_unbound_and_no_state():
    assert lens[1].get()([1, 2, 3]) == 2


# Testing that Lens properly passes though dunder methods
def test_lens_add():
    assert bind(2) + 1 == 3
    assert bind([[1, 2], 3])[0] + [4] == [[1, 2, 4], 3]


def test_lens_add_different_types():
    assert bind(2) + 1.0 == 3.0


def test_lens_radd():
    assert 1 + bind(2) == 3


def test_lens_subtract():
    assert bind(2) - 1 == 1


def test_lens_multiply():
    assert bind(2) * 2 == 4
    assert bind([[1, 2], [3]])[1] * 3 == [[1, 2], [3, 3, 3]]


def test_lens_divide():
    assert bind(10) / 2 == 5


def test_lens_neg():
    assert -bind(1) == -1


# Testing that you can use sublenses through Lens properly
def test_lens_trivial():
    assert bind(3).get() == 3


def test_lens_getitem():
    assert bind([1, 2, 3]).GetItem(1).get() == 2


def test_lens_getitem_direct():
    assert bind([1, 2, 3])[1].get() == 2


def test_lens_getattr():
    nt = collections.namedtuple('nt', 'attr')
    assert bind(nt(3)).GetAttr('attr').get() == 3


def test_lens_getattr_direct():
    nt = collections.namedtuple('nt', 'attr')
    assert bind(nt(3)).attr.get() == 3


def test_lens_both():
    assert bind([1, 2]).Both().collect() == [1, 2]


# Tests for ensuring lenses work on different type of objects
def test_type_tuple():
    assert bind(((0, 0), (0, 0)))[0][1].set(1) == ((0, 1), (0, 0))


def test_type_namedtuple():
    Tup = collections.namedtuple('Tup', 'attr')
    assert bind(Tup(0)).attr.set(1) == Tup(1)


def test_type_list():
    assert bind([[0, 1], [2, 3]])[1][0].set(4) == [[0, 1], [4, 3]]
    with pytest.raises(AttributeError):
        assert bind([[0, 1], [2, 3]]).attr.set(4)


def test_type_dict():
    assert bind({1: 2, 3: 4})[1].set(5) == {1: 5, 3: 4}
    with pytest.raises(AttributeError):
        assert bind({1: 2, 3: 4}).attr.set(5)


def test_type_custom_class_copy_and_mutate():
    class C(object):
        def __init__(self, a, b):
            self.a = a
            self.b = b

        def __eq__(self, other):
            return self.a == other.a and self.b == other.b

    assert bind(C(C(0, 1), C(2, 3))).a.b.set(4) == C(C(0, 4), C(2, 3))


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

    assert bind(C(C(9))).a.a.set(4) == C(C(4))


def test_type_custom_class_immutable():
    class C(object):
        def __init__(self, a):
            self._a = a

        @property
        def a(self):
            return self._a

    with pytest.raises(AttributeError):
        bind(C(9)).a.set(7)


def test_type_unsupported_no_setitem():
    with pytest.raises(TypeError):
        bind(object())[0].set(None)


def test_type_unsupported_no_setattr():
    with pytest.raises(AttributeError):
        bind(object()).attr.set(None)


# test various kinds
def test_trivial_kind():
    assert lens.kind() == 'Isomorphism'


def test_compose_iso_and_lens_kind():
    assert (lens & lens[0]).kind() == 'Lens'


def test_compose_iso_and_fold_kind():
    assert (lens & lens.Iter()).kind() == 'Fold'


def test_compose_lens_and_fold_kind():
    assert (lens[0] & lens.Iter()).kind() == 'Fold'


def test_compose_iso_and_setter_kind():
    assert (lens & lens.Fork(lens, lens)) == 'Setter'


def test_compose_lens_and_setter_kind():
    assert (lens[0] & lens.Fork(lens, lens)) == 'Setter'


def test_compose_fold_and_setter_kind_errors():
    with pytest.raises(RuntimeError):
        lens.Iter() & lens.Fork(lens, lens)


def test_bound_iso_kind():
    assert bind(True).kind() == 'Isomorphism'


# misc Lens tests
def test_lens_informative_repr():
    obj = object()
    assert repr(obj) in repr(bind(obj))
