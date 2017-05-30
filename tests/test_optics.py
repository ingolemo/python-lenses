import collections

import pytest
# import hypothesis
# import hypothesis.strategies as strat

from lenses import lens
from lenses.maybe import Just
from lenses import optics as b


# def build_lens_strat():
#     recursive_lens = strat.one_of(
#         strat.tuples(strat.just(b.GetitemLens),
#                      strat.integers(min_value=0, max_value=10)),
#     )
#     recursive_lenses = strat.lists(recursive_lens, max_size=5)

#     def nonrecursive_lens(lcons):
#         lst = strat.just(b.TrivialIso())
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


def test_LensLike():
    with pytest.raises(TypeError):
        b.LensLike().view(None)


def test_LensLike_func_not_implemented():
    with pytest.raises(NotImplementedError):
        b.LensLike().func(None, None)


def test_LensLike_no_focus_raises():
    with pytest.raises(ValueError):
        b.EachTraversal().view([])


def test_cannot_to_list_of_with_setter():
    with pytest.raises(TypeError):
        b.ForkedSetter(b.GetitemLens(0), b.GetitemLens(1)).to_list_of([1, 2])


def test_cannot_over_with_fold():
    with pytest.raises(TypeError):
        b.IterableFold().over([1, 2, 3], lambda a: a + 1)


def test_cannot_set_with_fold():
    with pytest.raises(TypeError):
        b.IterableFold().set([1, 2, 3], 4)


def test_cannot_re_with_fold():
    with pytest.raises(TypeError):
        b.IterableFold().re()


def test_composition_of_fold_and_setter_is_invalid():
    with pytest.raises(RuntimeError):
        b.IterableFold() & b.ForkedSetter()


def test_lens_and():
    my_lens = b.BothTraversal() & b.GetitemLens(1)
    assert my_lens.set([(0, 1), (2, 3)], 4) == [(0, 4), (2, 4)]


def test_BothTraversal_view():
    assert b.BothTraversal().view(['1', '2']) == '12'


def test_BothTraversal_set():
    assert b.BothTraversal().set(['1', '2'], 4) == [4, 4]


def test_ComposedLens_nolenses_view():
    obj = object()
    assert b.ComposedLens([]).view(obj) is obj


def test_ComposedLens_nolenses_set():
    obj1, obj2 = object(), object()
    assert b.ComposedLens([]).set(obj1, obj2) is obj2


def test_ComposedLens_nesting_simplifies():
    assert b.ComposedLens([b.ComposedLens([])]).lenses == []


def test_ComposedLens_compose_simplifies():
    l = b.ComposedLens([])
    assert isinstance(l & l, b.TrivialIso)


def test_DecodeIso_view():
    assert b.DecodeIso().view(b'hello') == 'hello'


def test_DecodeIso_view_with_args():
    assert b.DecodeIso('utf-8').view(b'caf\xc3\xa9') == u'caf\xe9'


def test_DecodeIso_set():
    assert b.DecodeIso('ascii', 'replace').set(b'', u'\xe9') == b'?'


def test_EachTraversal_to_list_of():
    assert b.EachTraversal().to_list_of([1, 2, 3]) == [1, 2, 3]


def test_EachTraversal_set():
    assert b.EachTraversal().set([1, 2, 3], 4) == [4, 4, 4]


def test_EachTraversal_to_list_of_on_set():
    assert sorted(b.EachTraversal().to_list_of({1, 2, 3})) == [1, 2, 3]


def test_EachTraversal_set_on_set():
    assert b.EachTraversal().set({1, 2, 3}, 4) == {4}


def test_EachTraversal_over_on_set():
    assert b.EachTraversal().over({1, 2, 3}, lambda a: a + 1) == {2, 3, 4}


def test_EachTraversal_to_list_of_empty():
    assert b.EachTraversal().to_list_of([]) == []


def test_EachTraversal_set_empty():
    assert b.EachTraversal().set([], 4) == []


def test_ErrorLens_view():
    class CustomException(Exception): pass
    with pytest.raises(CustomException):
        b.ErrorIso(CustomException('a message')).view(object())


def test_ErrorLens_set():
    class CustomException(Exception): pass
    with pytest.raises(CustomException):
        b.ErrorIso(CustomException('a message')).set(object(), object())


def test_ErrorLens_repr_with_seperate_message():
    lens = b.ErrorIso('test', 'a message')
    assert repr(lens) == "ErrorIso('test', 'a message')"


def test_FilteringPrism_to_list_of():
    l = b.EachTraversal() & b.FilteringPrism(lambda a: a > 0)
    assert l.to_list_of([1, -1, 1]) == [1, 1]


def test_FilteringPrism_set():
    l = b.EachTraversal() & b.FilteringPrism(lambda a: a > 0)
    assert l.set([1, -1, 1], 3) == [3, -1, 3]


def test_GetattrLens_view():
    Tup = collections.namedtuple('Tup', 'attr')
    assert b.GetattrLens('attr').view(Tup(1)) == 1


def test_GetattrLens_set():
    Tup = collections.namedtuple('Tup', 'attr')
    assert b.GetattrLens('attr').set(Tup(1), 2) == Tup(2)


class C(object):

    def __init__(self, attr):
        self.attr = attr

    def __eq__(self, other):
        return self.attr == other.attr

    sublens = lens().attr


def test_GetZoomAttrTraversal_view_attr():
    state = C('c')
    b.GetZoomAttrTraversal('attr').view(state) == 'c'


def test_GetZoomAttrTraversal_set_attr():
    state = C('c')
    b.GetZoomAttrTraversal('attr').set(state, 'b') == C('b')


def test_GetZoomAttrTraversal_view_zoom():
    state = C('c')
    b.GetZoomAttrTraversal('sublens').view(state) == 'c'


def test_GetZoomAttrTraversal_set_zoom():
    state = C('c')
    b.GetZoomAttrTraversal('sublens').set(state, 'b') == C('b')


def test_GetitemLens_view():
    assert b.GetitemLens(0).view([1, 2, 3]) == 1


def test_GetitemLens_set():
    assert b.GetitemLens(0).set([1, 2, 3], 4) == [4, 2, 3]


def test_Lens_view():
    my_lens = b.Lens(lambda a: a[:-1], lambda s, a: a + '!')
    state = 'hello!'
    assert my_lens.view(state) == 'hello'


def test_Lens_set():
    my_lens = b.Lens(lambda a: a[:-1], lambda s, a: a + '!')
    state = 'hello!'
    assert my_lens.set(state, 'bye') == 'bye!'


def test_Lens_over():
    my_lens = b.Lens(lambda a: a[:-1], lambda s, a: a + '!')
    state = 'hello!'
    assert my_lens.over(
        state, lambda a: a.replace('lo', 'p')) == 'help!'


def test_Lens_meaningful_repr():
    getter = lambda s: s
    setter = lambda s, f: f
    l = b.Lens(getter, setter)
    assert repr(getter) in repr(l)
    assert repr(setter) in repr(l)


def test_Isomorphism_view():
    assert b.Isomorphism(int, str).view('1') == 1


def test_IsomorphismLens_set():
    assert b.Isomorphism(int, str).set('1', 2) == '2'


def test_IsomorphismLens_getter():
    assert b.Isomorphism(int, str).getter('1') == 1


def test_IsomorphismLens_setter():
    assert b.Isomorphism(int, str).setter(None, 1) == '1'


def test_IsomorphismLens_unpack():
    assert b.Isomorphism(int, str).unpack('1') == Just(1)


def test_IsomorphismLens_pack():
    assert b.Isomorphism(int, str).pack(1) == '1'


def test_IsomorphismLens_view_from_():
    assert b.Isomorphism(int, str).from_().view(1) == '1'


def test_IsomorphismLens_set_from_():
    assert b.Isomorphism(int, str).from_().set(1, '2') == 2


def test_ItemLens_view():
    data = {0: 'hello', 1: 'world'}
    assert b.ItemLens(1).view(data) == (1, 'world')


def test_ItemLens_view_nonexistent():
    data = {0: 'hello', 1: 'world'}
    assert b.ItemLens(3).view(data) is None


def test_ItemLens_set():
    data = {0: 'hello', 1: 'world'}
    l = b.ItemLens(1)
    assert l.set(data, (2, 'everyone')) == {0: 'hello', 2: 'everyone'}


def test_ItemByValueLens_view():
    data = {'hello': 0, 'world': 1}
    assert b.ItemByValueLens(1).view(data) == ('world', 1)


def test_ItemByValueLens_view_nonexistent():
    data = {'hello': 0, 'world': 1}
    assert b.ItemByValueLens(2).view(data) is None


def test_ItemByValueLens_set():
    data = {'hello': 0, 'world': 1}
    assert b.ItemByValueLens(1).set(data, ('everyone', 2)) == {
        'hello': 0, 'everyone': 2}


def test_ItemByValueLens_set_nonexistent():
    data = {'hello': 0, 'world': 1}
    assert b.ItemByValueLens(2).set(data, ('test', 2)) == {
        'hello': 0, 'world': 1, 'test': 2}


def test_ItemsTraversal_to_list_of():
    data = {0: 'zero', 1: 'one'}
    my_lens = b.ItemsTraversal()
    assert sorted(my_lens.to_list_of(data)) == [(0, 'zero'), (1, 'one')]


def test_ItemsTraversal_to_list_of_empty():
    my_lens = b.ItemsTraversal()
    assert sorted(my_lens.to_list_of({})) == []


def test_ItemsTraversal_over():
    data = {0: 'zero', 1: 'one'}
    my_lens = b.ItemsTraversal() & b.GetitemLens(0)
    assert my_lens.over(data, lambda a: a + 1) == {
        1: 'zero', 2: 'one'}


def test_ItemsTraversal_over_empty():
    my_lens = b.ItemsTraversal() & b.GetitemLens(0)
    assert my_lens.over({}, lambda a: a + 1) == {}


def test_JsonIso_view():
    l = b.JsonIso()
    data = '{"numbers":[1, 2, 3]}'
    assert l.view(data) == {'numbers': [1, 2, 3]}


def test_JsonIso_set():
    l = b.JsonIso()
    data = '{"numbers":[1, 2, 3]}'
    assert l.set(data, {'numbers': []}) == '{"numbers": []}'


def test_TrivialIso_view():
    obj = object()
    assert b.TrivialIso().view(obj) is obj


def test_TrivialIso_set():
    obj1, obj2 = object(), object()
    assert b.TrivialIso().set(obj1, obj2) is obj2


def test_TupleLens_view_with_LensLike():
    data = {'hello': 0, 'world': 1}
    get = b.GetitemLens
    my_lens = b.TupleLens(get('hello'), get('world'))
    assert my_lens.view(data) == (0, 1)


def test_TupleLens_set_with_LensLike():
    data = {'hello': 0, 'world': 1}
    get = b.GetitemLens
    my_lens = b.TupleLens(get('hello'), get('world'))
    assert my_lens.set(data, (3, 4)) == {'hello': 3, 'world': 4}


def test_TupleLens_only_works_with_lenses():
    with pytest.raises(TypeError):
        b.TupleLens(b.EachTraversal())


def test_ZoomTraversal_view():
    l = b.GetitemLens(0) & b.ZoomTraversal()
    data = [lens([1, 2, 3])[1]]
    assert l.view(data) == 2


def test_ZoomTraversal_set():
    l = b.GetitemLens(0) & b.ZoomTraversal()
    data = [lens([1, 2, 3])[1]]
    assert l.set(data, 7) == [[1, 7, 3]]
