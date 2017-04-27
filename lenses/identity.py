from .typeclass import apply, pure


class Identity(object):
    '''The identiy functor applies functions to its contents
    with no additional funtionality. It is the trivial or null
    functor.

    It is needed for lenses to be able to set values.
    '''

    def __init__(self, item):
        self.item = item

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.item)

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

    def unwrap(self):
        return self.item
