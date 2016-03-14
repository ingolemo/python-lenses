from . import typeclass


class Maybe:
    def __init__(self, item, is_nothing):
        self.item = item
        self.is_nothing = is_nothing

    def __eq__(self, other):
        if self.is_nothing and other.is_nothing:
            return True
        if not self.is_nothing and not other.is_nothing:
            return self.item == other.item
        return False

    def __repr__(self):
        if self.is_nothing:
            return 'Nothing()'
        return 'Just({!r})'.format(self.item)

    def ap(self, fn):
        if self.is_nothing or fn.is_nothing:
            return Nothing()
        return Just(fn.item(self.item))

    def fmap(self, fn):
        if self.is_nothing:
            return Nothing()
        return Just(fn(self.item))

    def mappend(self, other):
        if self.is_nothing:
            return other
        if other.is_nothing:
            return self
        return Just(typeclass.mappend(self.item, other.item))

    def maybe(self, guard=None):
        if self.is_nothing:
            return guard
        return self.item

    def mempty(self):
        return Nothing()

    def pure(self, item):
        return Just(item)

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
