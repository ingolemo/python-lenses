import lenses.typeclass as tc
from lenses.functorisor import Functorisor
from lenses.identity import Identity
from lenses.maybe import Just, Nothing

ident = Functorisor(lambda a: Identity(a), lambda a: Identity(4))


def test_traversal_list_using_identity():
    assert tc.traverse([1, 2, 3], ident) == Identity([4, 4, 4])


def test_traversal_empty_list_using_identity():
    assert tc.traverse([], ident) == Identity([])


def test_traversal_just_using_identity():
    assert tc.traverse(Just(1), ident) == Identity(Just(4))


def test_traversal_nothing_using_identity():
    assert tc.traverse(Nothing(), ident) == Identity(Nothing())
