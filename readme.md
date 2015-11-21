# Lenses

Lenses is a python library that helps you to manipulate large
data-structures without mutating them.

## Installation

	pip install lenses

## How to Use

For most users, the lenses library exports only one thing worth knowing
about; a `lens` function:

	>>> from lenses import lens

If you have a large data structure that you want to manipulate, you can
pass it to this function and you will receive a BoundLens, which is a
Lens that has been bound to that specific object. The lens can then be
walked to focus it down on a particular part of the data-structure. You
walk the lens by getting attributes and items from it (anything that
would call `__getattr__` or `__getitem__`):

	>>> data = [1, 2, 3]
	>>> my_lens = lens(data)[1]

Once you arrive at the data you want, you can get hold of it with the
`get` method:

	>>> my_lens.get()
	2

Just getting data using the lens isn't very impressive. Better is the
`set` method, which allows you to set that particular piece of data
within the larger data structure. It returns a copy of the original data
structure with that one single piece of data changed. Note that the lens
never mutates the original data structure:

	>>> my_lens.set(5)
	[1, 5, 3]
	>>> data
	[1, 2, 3]

Lenses allow you to manipulate arbitrarily nested objects:

	>>> data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
	>>> lens(data)[1][0].set(20)
	[[1, 2, 3], [20, 5, 6], [7, 8, 9]]
	>>> lens(data)[2].set(20)
	[[1, 2, 3], [4, 5, 6], 20]

And they support more than just lists. Any mutable python object that
can by copied with `copy.copy` will work. Immutable objects need special
support, but support for any python object can be added so long as you
know how to construct a new version of that object with the appropriate
data changed. tuples and namedtuples are supported out of the box.

	>>> class MyClass:
	...     def __init__(self, attribute):
	...         self.attr = attribute
	...     def __repr__(self):
	...         return 'MyClass(' + repr(self.attr) + ')'
	...
	>>> data = (0, MyClass({'first': 'hello', 'second': 'world'}))
	>>> lens(data)[1].attr['first'].set('goodbye)
	(0, MyClass({'first': 'goodbye', 'second': 'world'}))

If you wish to apply a function using a lens you can use the `modify`
method:

	>>> lens([1, 2, 3])[0].modify(lambda a: a + 10)
	[11, 2, 3]

You can call methods on the data using `call_method`. Note that this
method should return new data to include in the data-structure:

	>>> lens([1, {0, 3}, 2])[1].call_method('union', {3, 8})
	[1, {0, 8, 3}, 2]

Lenses will also pass most operators through to the data they're focused
on. This makes using lenses in your code much more readable:

	>>> lens([1, 2, 3])[0] + 10
	[11, 2, 3]

## TODO

* add decent api for unbound lenses
* document unbound lenses
* add lens combinators
