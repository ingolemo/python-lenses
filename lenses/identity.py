from .typeclass import apply, pure


class Identity(object):
    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__qualname__, self.item)

    def __eq__(self, other):
        if not isinstance(other, Identity):
            return NotImplemented
        return self.item == other.item

    def map(self, fn):
        return Identity(fn(self.item))

    @classmethod
    def pure(cls, item):
        return cls(item)

    def apply(self, fn):
        return Identity(fn.item(self.item))

    def traverse(self, fn):
        applicative = fn(self.item)
        return apply(applicative, pure(applicative, Identity))

    def unwrap(self):
        return self.item
