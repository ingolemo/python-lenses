from .typeclass import mempty, mappend


class Const(object):
    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__qualname__, self.item)

    def __eq__(self, other):
        if not isinstance(other, Const):
            return NotImplemented
        return self.item == other.item

    def map(self, func):
        return Const(self.item)

    def pure(self, item):
        return Const(mempty(self.item))

    def apply(self, fn):
        return Const(mappend(fn.item, self.item))

    def unwrap(self):
        return self.item
