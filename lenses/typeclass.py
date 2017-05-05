from singledispatch import singledispatch
import sys


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


if sys.version_info[0] < 3:
    @mempty.register(long)
    def _mempty_long(self):
        return long(0)

    @mempty.register(unicode)
    def _memty_unicode(self):
        return u''


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
    out = {}
    out.update(dct)
    out.update(other)
    return out


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
