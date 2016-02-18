import collections

import pytest
# import hypothesis
# import hypothesis.strategies as strat

from lenses import lens
from lenses import baselens as b


# def build_lens_strat():
#     recursive_lens = strat.one_of(
#         strat.tuples(strat.just(b.GetitemLens),
#                      strat.integers(min_value=0, max_value=10)),
#     )
#     recursive_lenses = strat.lists(recursive_lens, max_size=5)

#     def nonrecursive_lens(lcons):
#         lst = strat.just(b.TrivialLens())
#         dst = strat.just(1)
#         for a_lens, data in lcons:
#             if a_lens is b.GetitemLens:
#                 lst = lst.map(a_lens(data).compose)
#                 dst = strat.lists(dst, min_size=data + 1)
#         return strat.tuples(lst, dst)
#     return recursive_lenses.flatmap(nonrecursive_lens)

# lens_strat = build_lens_strat()


# # Tests for lens rules and other invariants
# @hypothesis.given(lens_strat)
# def test_get_then_set(lns):
#     '''if we get from a state and then immediately set it again we
#     should get back the same state'''
#     ls, state = lns
#     assert ls.set(state, ls.get(state)) == state


# @hypothesis.given(lens_strat)
# def test_set_then_get(lns):
#     '''if we set a state and immediately get it we should get back what
#     we set'''
#     ls, state = lns
#     obj = object()
#     assert ls.get(ls.set(state, obj)) == obj


# @hypothesis.given(lens_strat)
# def test_set_then_set(lns):
#     '''if we set a state using a lens and then immediately set it again,
#     it should be as though we only set it once.'''
#     ls, state = lns
#     obj = object()
#     assert ls.set(ls.set(state, obj), obj) == ls.set(state, obj)


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


# Tests for lenses and lens constructor function that are built into the
# library.
def test_lens_and():
    my_lens = b.BothLens() & b.GetitemLens(1)
    assert my_lens.set([(0, 1), (2, 3)], 4) == [(0, 4), (2, 4)]


def test_lens_compose_nolenses():
    obj = object()
    assert b.ComposedLens([]).get(obj) is obj


def test_lens_double_compose_simplifies():
    assert b.ComposedLens([b.ComposedLens([])]).lenses == []


def test_lens_decode():
    assert b.DecodeLens().get(b'hello') == 'hello'
    assert b.DecodeLens('utf-8').get(b'caf\xc3\xa9') == 'caf\xe9'
    assert b.DecodeLens('ascii', 'replace').set(b'', '\xe9') == b'?'


def test_lens_getattr():
    Tup = collections.namedtuple('Tup', 'attr')
    obj = Tup(1)
    assert b.GetattrLens('attr').get(obj) == 1
    assert b.GetattrLens('attr').set(obj, 2) == Tup(2)


def test_lens_getitem():
    assert b.GetitemLens(0).get([1, 2, 3]) == 1
    assert b.GetitemLens(0).set([1, 2, 3], 4) == [4, 2, 3]


def test_lens_trivial():
    obj = object()
    assert b.TrivialLens().get(obj) is obj
    assert b.TrivialLens().set(obj, None) is None


def test_lens_both():
    assert b.BothLens().get(['1', '2']) == '12'
    assert b.BothLens().set(['1', '2'], 4) == [4, 4]


def test_lens_filtering():
    l = b.TraverseLens() & b.FilteringLens(lambda a: a > 0)
    assert l.set([1, -1, 1], 3) == [3, -1, 3]
    assert l.get_all([1, -1, 1]) == (1, 1)


def test_lens_item():
    data = {0: 'hello', 1: 'world'}
    l = b.ItemLens(1)
    assert l.get(data) == (1, 'world')
    assert l.set(data, (2, 'everyone')) == {0: 'hello', 2: 'everyone'}
    assert b.ItemLens(3).get(data) is None


def test_lens_item_by_value():
    data = {'hello': 0, 'world': 1}
    my_lens = b.ItemByValueLens(1)
    assert my_lens.get(data) == ('world', 1)
    assert my_lens.set(data, ('everyone', 2)) == {
        'hello': 0, 'everyone': 2}
    with pytest.raises(LookupError):
        b.ItemByValueLens(3).get(data)


def test_lens_items():
    data = {0: 'zero', 1: 'one'}
    my_lens = b.ItemsLens()
    assert sorted(my_lens.get_all(data)) == [(0, 'zero'), (1, 'one')]

    my_lens = b.ItemsLens().compose(b.GetitemLens(0))
    assert sorted(my_lens.get_all(data)) == [0, 1]
    assert my_lens.modify(data, lambda a: a +
                          1) == {1: 'zero', 2: 'one'}


def test_lens_json():
    l = b.JsonLens()
    data = '{"numbers":[1, 2, 3]}'
    assert l.get(data) == {'numbers': [1, 2, 3]}
    assert l.set(data, dict(numbers=[])) == '{"numbers": []}'


def test_lens_tuple_l():
    data = {'hello': 0, 'world': 1}
    get = b.GetitemLens
    my_lens = b.TupleLens(get('hello'), get('world'))
    assert my_lens.get(data) == (0, 1)
    assert my_lens.set(data, (3, 4)) == {'hello': 3, 'world': 4}


def test_lens_traverse():
    traversal = b.TraverseLens()
    assert traversal.get_all([0, 1, 2, 3]) == (0, 1, 2, 3)
    assert traversal.set([0, 1, 2, 3], 4) == [4, 4, 4, 4]

    double_traversal = traversal.compose(traversal)
    assert double_traversal.get_all([[0, 1], [2, 3]]) == (0, 1, 2, 3)
    assert double_traversal.set([[0, 1], [2, 3]], 4) == [[4, 4], [4, 4]]


# Tests for miscellaneous functions
def test_lens_from_getter_setter():
    my_lens = b.GetterSetterLens(lambda a: a[:-1], lambda s, a: a + '!')
    state = 'hello!'
    assert my_lens.get(state) == 'hello'
    assert my_lens.set(state, 'bye') == 'bye!'
    assert my_lens.modify(
        state, lambda a: a.replace('lo', 'p')) == 'help!'
