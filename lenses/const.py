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

    def fmap(self, func):
        return Const(self.item)

    @classmethod
    def pure(cls, item):
        return cls(mempty(item))

    def ap(self, fn):
        return Const(mappend(fn.item, self.item))
