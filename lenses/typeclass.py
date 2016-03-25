from functools import singledispatch


# monoid
@singledispatch
def mempty(monoid):
    return monoid.mempty()


@singledispatch
def mappend(monoid, other):
    return monoid + other


@mempty.register(int)
def _mempty_int(self):
    return 0


@mempty.register(str)
def _mempty_str(string):
    return ''


@mempty.register(list)
def _mempty_list(lst):
    return []


@mempty.register(tuple)
def _mempty_tuple(tup):
    return ()


@mempty.register(dict)
def _mempty_dict(dct):
    return {}


@mappend.register(dict)
def _mappend_dict(dct, other):
    return {**dct, **other}


# functor
@singledispatch
def fmap(functor, func):
    '''Applies a function to the data 'inside' a functor.

    Uses functools.singledispatch so you can write your own functors
    for use with the library.'''
    return functor.map(func)


@fmap.register(list)
def _fmap_list(lst, func):
    return [func(a) for a in lst]


@fmap.register(tuple)
def _fmap_tuple(tup, func):
    return tuple(func(a) for a in tup)


# applicative functor
@singledispatch
def pure(applicative, item):
    return applicative.pure(item)


@singledispatch
def apply(applicative, func):
    return applicative.apply(func)


@pure.register(list)
def _pure_list(lst, item):
    return [item]


@apply.register(list)
def _apply_list(lst, funcs):
    return [f(i) for i in lst for f in funcs]


@pure.register(tuple)
def _pure_tuple(tup, item):
    return (item,)


@apply.register(tuple)
def _apply_tuple(tup, funcs):
    return tuple(f(i) for i in tup for f in funcs)


# traversable
@singledispatch
def traverse(traversable, func):
    return traversable.traverse(func)


@traverse.register(list)
def _traverse_list(lst, func):
    if lst == []:
        return func.get_pure([])
    head, rest = lst[0], lst[1:]

    def cons(a):
        return lambda b: [a] + b

    if rest:
        return apply(traverse(rest, func), fmap(func(head), cons))
    else:
        return fmap(func(head), lambda a: [a])
