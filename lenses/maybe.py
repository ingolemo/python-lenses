from . import setter
from . import typeclass


class Maybe:
    '''A class that can contain a value or not. If it contains a value
    then it will be an instance of Just. If it doesn't then it will be
    an instance of Nothing. You can wrap an existing value By calling
    the Just constructor:

        >>> from lenses.maybe import Just, Nothing
        >>> Just(1)
        Just(1)

    To extract it again you can use the `maybe` method:

        >>> Just(1).maybe()
        1
    '''

    def __init__(self, item, is_nothing):
        self.item = item
        self.is_nothing = is_nothing

    def __add__(self, other):
        if self.is_nothing:
            return other
        if other.is_nothing:
            return self
        return Just(typeclass.mappend(self.item, other.item))

    def __eq__(self, other):
        if self.is_nothing and other.is_nothing:
            return True
        if not self.is_nothing and not other.is_nothing:
            return self.item == other.item
        return False

    def __iter__(self):
        if self.is_nothing:
            return
        yield self.item

    def __repr__(self):
        if self.is_nothing:
            return 'Nothing()'
        return 'Just({!r})'.format(self.item)

    def map(self, fn):
        '''Apply a function to the value inside the Maybe.'''
        if self.is_nothing:
            return Nothing()
        return Just(fn(self.item))

    def maybe(self, guard=None):
        '''Unwraps the value, returning it is there is one, else
        returning the guard.'''
        if self.is_nothing:
            return guard
        return self.item

    def traverse(self, func):
        if self.is_nothing:
            return func.get_pure(self)
        return typeclass.fmap(func(self.item), Just)


class Nothing(Maybe):
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        super().__init__(None, True)


class Just(Maybe):
    def __init__(self, item):
        super().__init__(item, False)


@typeclass.mempty.register(Maybe)
def _maybe_mempty(self):
    return Nothing()


@typeclass.fmap.register(Maybe)
def _maybe_fmap(self, fn):
    return self.map(fn)


@typeclass.pure.register(Maybe)
def _maybe_pure(self, item):
    return Just(item)


@typeclass.apply.register(Maybe)
def _maybe_apply(self, fn):
    if self.is_nothing or fn.is_nothing:
        return Nothing()
    return Just(fn.item(self.item))


@setter.fromiter.register(Maybe)
def _maybe_fromiter(self, iter):
    i = list(iter)
    if i == []:
        return Nothing()
    return Just(i[0])
