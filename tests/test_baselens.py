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


# Tests for lenses and lens constructor function that are built into the
# library.
def test_lens_and():
    my_lens = b.BothLens() & b.GetitemLens(1)
    assert my_lens.set([(0, 1), (2, 3)], 4) == [(0, 4), (2, 4)]


def test_ComposedLens_nolenses_get():
    obj = object()
    assert b.ComposedLens([]).get(obj) is obj


def test_ComposedLens_nolenses_set():
    obj1, obj2 = object(), object()
    assert b.ComposedLens([]).set(obj1, obj2) is obj2


def test_ComposedLens_nesting_simplifies():
    assert b.ComposedLens([b.ComposedLens([])]).lenses == []


def test_DecodeLens_get():
    assert b.DecodeLens().get(b'hello') == 'hello'


def test_DecodeLens_get_with_args():
    assert b.DecodeLens('utf-8').get(b'caf\xc3\xa9') == 'caf\xe9'


def test_DecodeLens_set():
    assert b.DecodeLens('ascii', 'replace').set(b'', '\xe9') == b'?'


def test_GetattrLens_get():
    Tup = collections.namedtuple('Tup', 'attr')
    assert b.GetattrLens('attr').get(Tup(1)) == 1


def test_GetattrLens_set():
    Tup = collections.namedtuple('Tup', 'attr')
    assert b.GetattrLens('attr').set(Tup(1), 2) == Tup(2)


def test_GetitemLens_get():
    assert b.GetitemLens(0).get([1, 2, 3]) == 1


def test_GetitemLens_set():
    assert b.GetitemLens(0).set([1, 2, 3], 4) == [4, 2, 3]


def test_TrivialLens_get():
    obj = object()
    assert b.TrivialLens().get(obj) is obj


def test_TrivialLens_set():
    obj1, obj2 = object(), object()
    assert b.TrivialLens().set(obj1, obj2) is obj2


def test_BothLens_get():
    assert b.BothLens().get(['1', '2']) == '12'


def test_BothLens_set():
    assert b.BothLens().set(['1', '2'], 4) == [4, 4]


def test_ErrorLens_get():
    with pytest.raises(Exception):
        b.ErrorLens(Exception('a message')).get(object())


def test_ErrorLens_set():
    with pytest.raises(Exception):
        b.ErrorLens(Exception('a message')).set(object(), object())


def test_FilteringLens_get():
    l = b.TraverseLens() & b.FilteringLens(lambda a: a > 0)
    assert l.set([1, -1, 1], 3) == [3, -1, 3]


def test_FilteringLens_set():
    l = b.TraverseLens() & b.FilteringLens(lambda a: a > 0)
    assert l.get_all([1, -1, 1]) == (1, 1)


def test_GetterSetterLens_get():
    my_lens = b.GetterSetterLens(lambda a: a[:-1], lambda s, a: a + '!')
    state = 'hello!'
    assert my_lens.get(state) == 'hello'


def test_GetterSetterLens_set():
    my_lens = b.GetterSetterLens(lambda a: a[:-1], lambda s, a: a + '!')
    state = 'hello!'
    assert my_lens.set(state, 'bye') == 'bye!'


def test_GetterSetterLens_modify():
    my_lens = b.GetterSetterLens(lambda a: a[:-1], lambda s, a: a + '!')
    state = 'hello!'
    assert my_lens.modify(
        state, lambda a: a.replace('lo', 'p')) == 'help!'


def test_ItemLens_get():
    data = {0: 'hello', 1: 'world'}
    assert b.ItemLens(1).get(data) == (1, 'world')


def test_ItemLens_get_nonexistent():
    data = {0: 'hello', 1: 'world'}
    assert b.ItemLens(3).get(data) is None


def test_ItemLens_set():
    data = {0: 'hello', 1: 'world'}
    l = b.ItemLens(1)
    assert l.set(data, (2, 'everyone')) == {0: 'hello', 2: 'everyone'}


def test_ItemByValueLens_get():
    data = {'hello': 0, 'world': 1}
    assert b.ItemByValueLens(1).get(data) == ('world', 1)


def test_ItemByValueLens_get_nonexistent():
    data = {'hello': 0, 'world': 1}
    assert b.ItemByValueLens(2).get(data) is None


def test_ItemByValueLens_set():
    data = {'hello': 0, 'world': 1}
    assert b.ItemByValueLens(1).set(data, ('everyone', 2)) == {
        'hello': 0, 'everyone': 2}


def test_ItemByValueLens_set_nonexistent():
    data = {'hello': 0, 'world': 1}
    assert b.ItemByValueLens(2).set(data, ('test', 2)) == {
        'hello': 0, 'world': 1, 'test': 2}


def test_ItemsLens_get_all():
    data = {0: 'zero', 1: 'one'}
    my_lens = b.ItemsLens()
    assert sorted(my_lens.get_all(data)) == [(0, 'zero'), (1, 'one')]


def test_ItemsLens_modify():
    data = {0: 'zero', 1: 'one'}
    my_lens = b.ItemsLens().compose(b.GetitemLens(0))
    assert my_lens.modify(data, lambda a: a + 1) == {
        1: 'zero', 2: 'one'}


def test_JsonLens_get():
    l = b.JsonLens()
    data = '{"numbers":[1, 2, 3]}'
    assert l.get(data) == {'numbers': [1, 2, 3]}


def test_JsonLens_set():
    l = b.JsonLens()
    data = '{"numbers":[1, 2, 3]}'
    assert l.set(data, {'numbers': []}) == '{"numbers": []}'


def test_TupleLens_get():
    data = {'hello': 0, 'world': 1}
    get = b.GetitemLens
    my_lens = b.TupleLens(get('hello'), get('world'))
    assert my_lens.get(data) == (0, 1)


def test_TupleLens_set():
    data = {'hello': 0, 'world': 1}
    get = b.GetitemLens
    my_lens = b.TupleLens(get('hello'), get('world'))
    assert my_lens.set(data, (3, 4)) == {'hello': 3, 'world': 4}


def test_TraverseLens_get_all():
    assert b.TraverseLens().get_all([0, 1, 2, 3]) == (0, 1, 2, 3)


def test_TraverseLens_set():
    assert b.TraverseLens().set([0, 1, 2, 3], 4) == [4, 4, 4, 4]


def test_TraverseLens_get_all_double():
    l = b.TraverseLens() & b.TraverseLens()
    assert l.get_all([[0, 1], [2, 3]]) == (0, 1, 2, 3)


def test_TraverseLens_set_double():
    l = b.TraverseLens() & b.TraverseLens()
    assert l.set([[0, 1], [2, 3]], 4) == [[4, 4], [4, 4]]


def test_ZoomLens_get():
    l = b.GetitemLens(0) & b.ZoomLens()
    data = [lens([1, 2, 3])[1]]
    assert l.get(data) == 2


def test_ZoomLens_set():
    l = b.GetitemLens(0) & b.ZoomLens()
    data = [lens([1, 2, 3])[1]]
    assert l.set(data, 7) == [[1, 7, 3]]
