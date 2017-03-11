import lenses.typeclass as tc
from lenses.functorisor import Functorisor
from lenses.identity import Identity
from lenses.maybe import Just, Nothing

ident = Functorisor(lambda a: Identity(a), lambda a: Identity(4))

