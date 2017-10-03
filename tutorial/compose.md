# Composing Lenses

If we have two lenses, we can join them together using the `&`
operator. Joining lenses means that the second lens is placed "inside"
of the first so that the focus of the first lens is fed into the second
one as its state:

	>>> from lenses import lens

	>>> index_zero = lens[0]
	>>> index_one = lens[1]
	>>> get_zero_then_one = (index_zero & index_one).get()
	>>> get_zero_then_one([[2, 3], [4, 5]])
	3
	>>> get_one_then_zero = (index_one & index_zero).get()
	>>> get_one_then_zero([[2, 3], [4, 5]])
	4

When we call `a & b`, `b` must be an unbound lens and the
resulting lens will be bound to the same object as `a`, if any.

It is important to note that doing two operations on two different lenses
and then composing them is the equivalent to doing those two operations
on the same lens:

	>>> lens[0][1]
	UnboundLens(GetitemLens(0) & GetitemLens(1))
	>>> lens[0] & lens[1]
	UnboundLens(GetitemLens(0) & GetitemLens(1))

The first is actually implemented in terms of the second, internally.

When we need to do more than two operations on the same lens we will
often refer to this as "composing" two lenses even though the `&` operator
is nowhere in sight.


## Binding

The lenses library also exports a `bind` function:

	>>> from lenses import lens, bind

The bind function takes a single argument — a state — and it will
return a `BoundLens` object that has been bound to that state.

	>>> bind([1, 2, 3])
	BoundLens([1, 2, 3], TrivialIso())

A bound lens is almost exactly like an unbound lens. It has almost all
the same methods and they work in almost exactly the same way. The major
difference is that those methods that would normally return a function
expecting us to pass a state will instead act immediately:

	>>> bind([1, 2, 3])[1].get()
	2

Here, the `get` method is acting on the state that the lens was bound
to originally.

The methods that are affected are `get`, `set`, `modify`, `call`, and
`call_mut`. All of the operators are also affected.

	>>> bind([1, 2, 3])[1].set(4)
	[1, 4, 3]
	>>> bind([1, 2, 3])[1].modify(str)
	[1, '2', 3]
	>>> bind([1, 255, 3])[1].call('bit_length')
	[1, 8, 3]
	>>> bind([1, [4, 2, 3], 5])[1].call_mut('sort')
	[1, [2, 3, 4], 5]
	>>> bind([1, 2, 3])[1] + 10
	[1, 12, 3]
	>>> bind([1, 2, 3])[1] * 10
	[1, 20, 3]


## Descriptors

The main place where we would use a bound lens is as part of a descriptor.

When you set an unbound lens as a class attribute and you access that
attribute from an instance, you will get a bound lens that has been
bound to that instance. This allows you to conveniently store and access
lenses that are likely to be used with particular classes as attributes
of those classes. Attribute access is much more readable than requiring
the user of a class to construct a lens themselves.

Here we have a vector class that stores its data in a private `_coords`
attribute, but allows access to parts of that data through `x` and `y`
attributes.

	>>> class Vector(object):
	...     def __init__(self, x, y):
	...         self._coords = [x, y]
	...     def __repr__(self):
	...         return 'Vector({0!r}, {1!r})'.format(*self._coords)
	...     x = lens._coords[0]
	...     y = lens._coords[1]
	...
	>>> my_vector = Vector(1, 2)
	>>> my_vector.x.set(3)
	Vector(3, 2)

Here `Vector.x` and `Vector.y` are unbound lenses, but `my_vector.x` and
`my_vector.y` are both bound lenses that are bound to `my_vector`. A
lens used in this way is similar to python's `property` decorator,
except that the api is more powerful and the setter acts immutably.

If you ever end up focusing an object with a sublens as one of its
attributes, lenses are smart enough to follow that sublens to its focus.

	>>> data = [Vector(1, 2), Vector(3, 4)]
	>>> lens[1].y.set(5)(data)
	[Vector(1, 2), Vector(3, 5)]
