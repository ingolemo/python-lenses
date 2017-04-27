from .. import hooks
from .. import typeclass

from .base import *


def multiap(func, *args):
    '''Applies `func` to the data inside the `args` functors
    incrementally. `func` must be a curried function that takes
    `len(args)` arguments.

        >>> func = lambda a: lambda b: a + b
        >>> multiap(func, [1, 10], [100])
        [101, 110]
    '''
    functor = typeclass.fmap(args[0], func)
    for arg in args[1:]:
        functor = typeclass.apply(arg, functor)
    return functor


def collect_args(n):
    '''Returns a function that can be called `n` times with a single
    argument before returning all the args that have been passed to it
    in a tuple. Useful as a substitute for functions that can't easily be
    curried.

        >>> collect_args(3)(1)(2)(3)
        (1, 2, 3)
    '''
    args = []

    def arg_collector(arg):
        args.append(arg)
        if len(args) == n:
            return tuple(args)
        else:
            return arg_collector

    return arg_collector


class BothLens(Traversal):
    '''A traversal that focuses both items [0] and [1].

        >>> from lenses import lens
        >>> lens().both_()
        Lens(None, BothLens())
        >>> lens([1, 2, 3]).both_().get_all()
        [1, 2]
        >>> lens([1, 2, 3]).both_().set(4)
        [4, 4, 3]
    '''

    def func(self, f, state):
        def multisetter(items):
            s = hooks.setitem_immutable(state, 0, items[0])
            s = hooks.setitem_immutable(s, 1, items[1])
            return s

        f0 = f(state[0])
        f1 = f(state[1])
        return typeclass.fmap(multiap(collect_args(2), f0, f1), multisetter)

    def __repr__(self):
        return 'BothLens()'


class EachLens(Traversal):
    '''A traversal that iterates over its state, focusing everything it
    iterates over. It uses `lenses.hooks.fromiter` to reform the state
    afterwards so it should work with any iterable that function
    supports. Analogous to `iter`.

        >>> from lenses import lens
        >>> data = [1, 2, 3]
        >>> lens().each_()
        Lens(None, EachLens())
        >>> lens(data).each_().get_all()
        [1, 2, 3]
        >>> lens(data).each_().modify(lambda n: n + 1)
        [2, 3, 4]
        >>> lens(data).each_(filter_none=True).set(None)
        []

    For technical reasons, this lens iterates over dictionaries by their
    items and not just their keys.

        >>> data = {'one': 1}
        >>> lens(data).each_().get_all()
        [('one', 1)]
        >>> lens(data).each_()[1] + 1
        {'one': 2}
    '''

    def __init__(self, filter_func=None, filter_none=False, *_):
        if filter_none:
            self.filter_func = lambda a: a is not None
        elif filter_func is None:
            self.filter_func = lambda a: True
        else:
            self.filter_func = filter_func

    def func(self, f, state):
        items = list(filter(self.filter_func, hooks.to_iter(state)))

        def build_new_state_from_iter(a):
            return hooks.from_iter(state, filter(self.filter_func, a))

        if items == []:
            return f.pure(build_new_state_from_iter(items))

        collector = collect_args(len(items))
        applied = multiap(collector, *map(f, items))
        return typeclass.fmap(applied, build_new_state_from_iter)

    def __repr__(self):
        return 'EachLens()'


class GetZoomAttrTraversal(Traversal):
    '''A traversal that focuses an attribute of an object, though if
    that attribute happens to be a lens it will zoom the lens. This
    is used internally to make lenses that are attributes of objects
    transparent. If you already know whether you are focusing a lens or
    a non-lens you should be explicit and use a ZoomAttrTraversal or a
    GetAttrLens respectively.

        >>> from lenses import lens
        >>> from collections import namedtuple
        >>> Triple = namedtuple('Triple', 'left middle right')
        >>> state = Triple(1, 10, lens().middle)
        >>> lens().left
        Lens(None, GetZoomAttrTraversal('left'))
        >>> lens(state).left.get()
        1
        >>> lens(state).left.set(3)
        Triple(left=3, middle=10, right=Lens(None, GetZoomAttrTraversal('middle')))
        >>> lens(state).right.get()
        10
        >>> lens(state).right.set(13)
        Triple(left=1, middle=13, right=Lens(None, GetZoomAttrTraversal('middle')))
    '''

    def __init__(self, name):
        from lenses.optics import GetattrLens
        self.name = name
        self._getattr_cache = GetattrLens(name)

    def func(self, f, state):
        attr = getattr(state, self.name)
        try:
            sublens = attr._underlying_lens()
        except AttributeError:
            sublens = self._getattr_cache
        return sublens.func(f, state)

    def __repr__(self):
        return 'GetZoomAttrTraversal({!r})'.format(self.name)



class ItemsLens(Traversal):
    '''A traversal focusing key-value tuples that are the items of a
    dictionary. Analogous to `dict.items`.

        >>> from lenses import lens
        >>> from collections import OrderedDict
        >>> data = OrderedDict([(1, 10), (2, 20)])
        >>> lens().items_()
        Lens(None, ItemsLens())
        >>> lens(data).items_().get_all()
        [(1, 10), (2, 20)]
        >>> lens(data).items_()[1].modify(lambda n: n + 1)
        OrderedDict([(1, 11), (2, 21)])
    '''

    def func(self, f, state):
        items = list(state.items())
        if items == []:
            return f.pure(state)

        def dict_builder(args):
            data = state.copy()
            data.clear()
            data.update(a for a in args if a is not None)
            return data

        collector = collect_args(len(items))
        return typeclass.fmap(multiap(collector, *map(f, items)), dict_builder)

    def __repr__(self):
        return 'ItemsLens()'


class ZoomAttrLens(Traversal):
    '''A lens that looks up an attribute on its target and follows it as
    if were a bound `Lens` object. Ignores the state, if any, of the
    lens that is being looked up.

        >>> from lenses import lens
        >>> class ClassWithLens(object):
        ...     def __init__(self, items):
        ...         self._private_items = items
        ...     def __repr__(self):
        ...         return 'ClassWithLens({!r})'.format(self._private_items)
        ...     first = lens()._private_items[0]
        ...
        >>> data = (ClassWithLens([1, 2, 3]), 4)
        >>> lens().zoomattr_('first')
        Lens(None, ZoomAttrLens('first'))
        >>> lens(data)[0].zoomattr_('first').get()
        1
        >>> lens(data)[0].zoomattr_('first').set(5)
        (ClassWithLens([5, 2, 3]), 4)
    '''

    def __init__(self, name):
        self.name = name

    def func(self, f, state):
        l = getattr(state, self.name)
        return l._underlying_lens().func(f, state)

    def __repr__(self):
        return 'ZoomAttrLens({!r})'.format(self.name)


class ZoomLens(Traversal):
    '''Follows its state as if it were a bound `Lens` object.

        >>> from lenses import lens
        >>> data = [lens([1, 2])[1], 4]
        >>> lens().zoom_()
        Lens(None, ZoomLens())
        >>> lens(data)[0].zoom_().get()
        2
        >>> lens(data)[0].zoom_().set(3)
        [[1, 3], 4]
    '''

    def func(self, f, state):
        return state._underlying_lens().func(f, state.state)

    def __repr__(self):
        return 'ZoomLens()'
