import collections

import pytest
# import hypothesis
# import hypothesis.strategies as strat

from lenses import lens, bind, optics as b
from lenses.maybe import Just, Nothing


class CustomException(Exception):
    pass


class Pair(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    east = lens.left
    west = lens.right

    def __eq__(self, other):
        return self.left == other.left and self.right == other.right

    def __repr__(self):
        return 'Pair({!r}, {!r})'.format(self.left, self.right)


def test_LensLike():
    with pytest.raises(TypeError):
        b.LensLike().view(None)


def test_LensLike_func_not_implemented():
    with pytest.raises(NotImplementedError):
        b.LensLike().func(None, None)


def test_LensLike_no_focus_raises():
    with pytest.raises(ValueError):
        b.EachTraversal().view([])


def test_cannot_preview_with_setter():
    with pytest.raises(TypeError):
        b.ForkedSetter(b.GetitemLens(0), b.GetitemLens(1)).preview([1, 2])


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
    my_lens = b.EachTraversal() & b.GetitemLens(1)
    assert my_lens.set([(0, 1), (2, 3)], 4) == [(0, 4), (2, 4)]


def test_getter_folder():
    assert list(b.Getter(abs).folder(-1)) == [1]


def test_prism_folder_success():
    obj = object
    assert list(b.JustPrism().folder(Just(obj))) == [obj]


def test_prism_folder_failure():
    assert list(b.JustPrism().folder(Nothing())) == []


def test_Getter_composes_correctly():
    visited = []

    def visit(item):
        visited.append(item)
        return item

    my_lens = b.EachTraversal() & b.Getter(visit) & b.EachTraversal()
    my_lens.to_list_of(([1, 2, 3], [4, 5, 6], [7, 8, 9]))
    assert visited == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


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
    with pytest.raises(CustomException):
        b.ErrorIso(CustomException('a message')).view(object())


def test_ErrorLens_set():
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


def test_GetZoomAttrTraversal_view_attr():
    obj = object()
    state = Pair(obj, 'red herring')
    assert b.GetZoomAttrTraversal('left').view(state) is obj


def test_GetZoomAttrTraversal_set_attr():
    obj = object()
    state = Pair('initial value', 'red herring')
    new_state = Pair(obj, 'red herring')
    assert b.GetZoomAttrTraversal('left').set(state, obj) == new_state


def test_GetZoomAttrTraversal_view_zoom():
    obj = object()
    state = Pair(obj, 'red herring')
    assert b.GetZoomAttrTraversal('east').view(state) is obj


def test_GetZoomAttrTraversal_set_zoom():
    obj = object()
    state = Pair('initial value', 'red herring')
    new_state = Pair(obj, 'red herring')
    assert b.GetZoomAttrTraversal('east').set(state, obj) == new_state


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
    assert my_lens.over(state, lambda a: a.replace('lo', 'p')) == 'help!'


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


def test_IsomorphismLens_view_re():
    assert b.Isomorphism(int, str).re().view(1) == '1'


def test_IsomorphismLens_set_re():
    assert b.Isomorphism(int, str).re().set(1, '2') == 2


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
    result = {'hello': 0, 'everyone': 2}
    assert b.ItemByValueLens(1).set(data, ('everyone', 2)) == result


def test_ItemByValueLens_set_nonexistent():
    data = {'hello': 0, 'world': 1}
    assert b.ItemByValueLens(2).set(data, ('test', 2)) == {
        'hello': 0, 'world': 1, 'test': 2
    }


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
    assert my_lens.over(data, lambda a: a + 1) == {1: 'zero', 2: 'one'}


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


def test_RecurTraversal_to_list_of():
    data = [1, [2], [3, 4], [[5], 6, [7, [8, 9]]]]
    result = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    assert b.RecurTraversal(int).to_list_of(data) == result


def test_RecurTraversal_over():
    data = [
        1,
        [],
        [2],
        Pair(3, 4),
        Pair('one', 'two'),
        Pair([Pair(5, [6, 7]), 256.0], 8),
        Pair(['three', Pair(9, 'four')], 'five'),
    ]
    result = [
        2,
        [],
        [3],
        Pair(4, 5),
        Pair('one', 'two'),
        Pair([Pair(6, [7, 8]), 256.0], 9),
        Pair(['three', Pair(10, 'four')], 'five'),
    ]
    assert b.RecurTraversal(int).over(data, lambda n: n + 1) == result


def test_RecurTraversal_over_with_frozenset():
    data = [1, frozenset([2, 3]), 4]
    result = [11, frozenset([12, 13]), 14]
    lens = b.RecurTraversal(int)
    assert lens.over(data, lambda n: n + 10) == result


def test_RecurTraversal_no_change():
    data = [
        1,
        [],
        [2],
        Pair(3, 4),
        Pair('one', 'two'),
        Pair([Pair(5, [6, 7]), 256.0], 8),
        Pair(['three', Pair(9, 'four')], 'five'),
    ]
    lens = b.RecurTraversal(float)
    result = lens.over(data, lambda a: 512.0)
    assert data is not result
    for n in (0, 1, 2, 3, 4, 6):
        assert data[n] is result[n]


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
    data = [bind([1, 2, 3])[1]]
    assert l.view(data) == 2


def test_ZoomTraversal_set():
    l = b.GetitemLens(0) & b.ZoomTraversal()
    data = [bind([1, 2, 3])[1]]
    assert l.set(data, 7) == [[1, 7, 3]]
