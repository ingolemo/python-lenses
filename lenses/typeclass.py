import functools


# monoid
@functools.singledispatch
def mempty(monoid):
    return monoid.mempty()


@functools.singledispatch
def mappend(monoid, other):
    return monoid.mappend(other)


mempty.register(str)(lambda string: '')
mappend.register(str)(lambda string, other: string + other)

mempty.register(list)(lambda lst: [])
mappend.register(list)(lambda lst, other: lst + other)

mempty.register(tuple)(lambda lst: ())
mappend.register(tuple)(lambda tup, other: tup + other)


# functor
@functools.singledispatch
def fmap(functor, func):
    '''Applies a function to the data 'inside' a functor.

    Uses functools.singledispatch so you can write your own functors
    for use with the library.'''
    return functor.fmap(func)


# applicative functor
@functools.singledispatch
def pure(applicative, item):
    return applicative.pure(item)


@functools.singledispatch
def ap(applicative, func):
    return applicative.ap(func)


# traversable
@functools.singledispatch
def traverse(traversable, func):
    return traversable.traverse(func)
