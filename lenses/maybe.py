class Nothing:
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance

    def __repr__(self):
        return 'Nothing()'

    def fmap(self, func):
        return self

    def pure(self, item):
        return Just(item)

    def ap(self, wrapped_func):
        return self


class Just:

    def __init__(self, item):
        self.item = item

    def __eq__(self, other):
        if isinstance(other, Just):
            return self.item == other.item
        return NotImplemented

    def __repr__(self):
        return 'Just({!r})'.format(self.item)

    def fmap(self, func):
        return Just(func(self.item))

    def pure(self, item):
        return Just(item)

    def ap(self, wrapped_func):
        if isinstance(wrapped_func, Just):
            return Just(wrapped_func.item(self.item))
        elif isinstance(wrapped_func, Nothing):
            return Nothing()
        raise TypeError('must be Nothing or Just')
