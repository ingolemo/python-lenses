from .typeclass import mempty, mappend


class Const:
    def __init__(self, item):
        self.item = item

    def fmap(self, func):
        return Const(self.item)

    @classmethod
    def pure(self, item):
        return Const(mempty(item))

    def ap(self, fn):
        return Const(mappend(self.item, fn.item))
