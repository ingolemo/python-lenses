# Lenses

Lenses is a python library that helps you to manipulate large
data-structures without mutating them. It is inspired by the lenses in
Haskell, although it's much less principled and the api is more suitable
for python.


## Installation

You can install the latest github version using pip like so:

	pip install git+git://github.com/ingolemo/python-lenses.git

You can uninstall similarly:

	pip uninstall lenses


## How to Use

The lenses library makes liberal use of docstrings, which you can access
as normal with the `pydoc` shell command, the `help` function in the
repl, or by reading the source yourself.

Most users will only need the docs from `lenses.Lens`. If you want to
add hooks to allow parts of the library to work with custom objects then
you should check out the `lenses.setters` module. Most of the fancy lens
code is in the `lenses.baselens` module for those who are curious how
everything works.

An example is given in the `examples` folder.


### The Basics

For most users, the lenses library exports only one thing worth knowing
about; a `lens` function:

	>>> from lenses import lens

If you have a large data structure that you want to manipulate, you can
pass it to this function and you will receive a bound `Lens` object,
which is a lens that has been bound to that specific object. The lens
can then be walked to focus it down on a particular part of the
data-structure. You walk the lens by getting attributes and items from
it (anything that would call `__getattr__` or `__getitem__`):

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
	>>> data = (0, MyClass({'hello': 'world'}))
	>>> lens(data)[1].attr['hello'].set('everyone')
	(0, MyClass({'hello': 'everyone'}))

If you wish to apply a function using a lens you can use the `modify`
method:

	>>> lens([1, 2, 3])[0].modify(lambda a: a + 10)
	[11, 2, 3]

You can call methods on the data using `call`. Note that this
method should return new data to include in the data-structure:

	>>> lens([1, {2}, 3])[1].call('union', {4, 5})
	[1, {2, 4, 5}, 3]

Lenses will also pass most operators through to the data they're focused
on. This makes using lenses in your code much more readable:

	>>> lens([1, 2, 3])[0] + 10
	[11, 2, 3]

Lenses work best when you have to manipulate highly nested data
structures that hold a great deal of state, such as when programming
games:

	>>> from collections import namedtuple
	>>> 
	>>> GameState = namedtuple('GameState', 'worlds current_world current_level')
	>>> World = namedtuple('World', 'levels theme')
	>>> Level = namedtuple('Level', 'map enemies')
	>>> Enemy = namedtuple('Enemy', 'x y')
	>>> 
	>>> old_state = GameState({
	...     1: World({}, 'grassland'),
	...     2: World({
	...         1: Level({}, {
	...             'goomba1': Enemy(100, 45),
	...             'goomba2': Enemy(130, 45),
	...             'goomba3': Enemy(160, 45),
	...         }),
	...     }, 'desert'),
	... }, 1, 1)
	>>> 
	>>> new_state = lens(old_state).worlds[2].levels[1].enemies['goomba3'].x + 1

With the structure above, that last line of code produces a new
`GameState` object where the third enemy on the first level of the
second world has been moved across by one pixel without any of the
objects in the original state being mutated. Without lenses this would
take a rather large amount of plumbing to achieve.

Note that the lens does not make a deep copy of the entire state.
Objects in the state that do not need to change are reused and no new
copies are made. This makes lenses more memory efficient than using
`copy.deepcopy` for sufficiently large states:

	>>> old_state.worlds[1] is new_state.worlds[1]
	True
	>>> old_state.worlds[2] is new_state.worlds[2]
	False


### Unbound Lenses

If you pass no arguments to the `lens` function then you will get an
unbound `Lens` object. An unbound lens can be manipulated in all the
ways that a bound lens can except that you can't call any of the methods
that manipulate the state (such as `get` and `set`).

	>>> unbound_lens = lens()
	>>> key_one = unbound_lens['one']

You can then attach a state to the lens using the `bind` method and call
state manipulating methods as normal:

	>>> key_one.bind({'one': 1, 'two': 2}).get()
	1

Alternatively, you can call the state manipulating method as normal and
pass in a keyword-only `state` argument for the method to act on:

	>>> key_one.get(state={'one': 1, 'two': 2})
	1

You can use unbound Lens objects as descriptors. That is, if you set a
lens as a class attribute and you access that attribute from an
instance, you will get a lens that has been bound to that instance. This
allows you to conveniently store and access lenses that are likely to be
used with particular classes as attributes of those classes. Attribute
access is much more readable than requiring the user of a class to
construct a lens themselves.

	>>> class ClassWithLens:
	...     def __init__(self, items):
	...         self._private_items = items
	...     def __repr__(self):
	...         return 'ClassWithLens({!r})'.format(self._private_items)
	...     first = lens()._private_items[0]
	...
	>>> my_instance = ClassWithLens([1, 2, 3])
	>>> my_instance.first.set(4)
	ClassWithLens([4, 2, 3])

If you ever end up focusing an object with a lens as one of its
attributes then you can use that lens by accessing the attribute with
an extra `_l` at the end:

	>>> data = [ClassWithLens([1, 2, 3]), ClassWithLens([4, 5, 6])]
	>>> lens(data)[1].first_l.set(7)
	[ClassWithLens([1, 2, 3]), ClassWithLens([7, 5, 6])]


### Composing Lenses

If you have two lenses, you can join them together using the `add_lens`
method. Joining lenses means that one of the lenses is placed "inside"
of the other so that the focus of one lens is fed into the other one as
its state:

	>>> first = lens()[0]
	>>> second = lens()[1]
	>>> first_then_second = first.add_lens(second)
	>>> first_then_second.bind([[2, 3], [4, 5]]).get()
	3
	>>> second_then_first = second.add_lens(first)
	>>> second_then_first.bind([[2, 3], [4, 5]]).get()
	4

When you call `a.add_lens(b)`, `b` must be an unbound lens and the
resulting lens will be bound to the same object as `a`, if any.


### Lenses that do computation

So far we've seen lenses that extract data out of data-structures, but
lenses are more powerful than that. Lenses can actually perform
arbitrary computation on the data passing through them as long as that
computation can be reversed.

A simple example is that of the `item_` method which returns a lens that
focuses on a single key of a dictionary but returns both the key and the
value:

	>>> l = lens({'one': 1})
	>>> l.item_('one').get()
	('one', 1)
	>>> l.item_('one').set(('three', 3))
	{'three': 3}

There are a number of such more complicated lenses defined on `Lens`. To
help avoid collision with accessing attributes on the state, their names
all end with a single underscore. See `help(lenses.Lens)` in the repl
for more. If you need to access an attribute on the state that has been
shadowed by Lens' methods then you can use `Lens.getattr_(attribute)`.

At their heart, lenses are really just souped-up getters and setters. If
you have a getter and a setter for some data then you can turn those
into a lens using the `getter_setter_` method. Here is a lens that
focuses some text and interprets it as json data:

	>>> import json
	>>> def setter(state, value):
	...     return json.dumps(value)
	...
	>>> json_lens = lens().getter_setter_(json.loads, setter)
	>>> my_data = json_lens.bind('{"numbers":[1, 2, 3]}')
	>>> my_data.get()
	{'numbers': [1, 2, 3]}
	>>> my_data['numbers'][1].set(4)
	'{"numbers": [1, 4, 3]}'

This is just an example; the json lens defined above is already
available with the `json_` method. See the docstrings for both these
methods for details on how to use them.


### Traversals

All the lenses so far have focused a single object inside a state, but
it is possible for a lens to have more than one focus. A lens with
multiple foci is usually referred to as a traversal. A simple traversal
can be made with the `_both` method. `Lens.both_` focuses the two
objects at indices `0` and `1` within the state. It is intended to be
used with tuples of length 2, but will work on any indexable object.

One issue with multi-focus lenses is that the `get` method only ever
returns a single focus. It will return the _first_ item focused by the
traversal. If you want to get all the items focused by a lens then you
can use the `get_all` method which will return those objects in a list:

	>>> lens([0, 1, 2, 3]).both_().get_all()
	[0, 1]

Setting works with a traversal, though all foci will be set to the same
object.

	>>> lens([0, 1, 2, 3]).both_().set(4)
	[4, 4, 2, 3]

Modifying is the most useful operation you can perform. The modification
will be applied to all the foci independently. All the foci must be of
the same type (or at least be of a type that supports the modification
that you want to make).

	>>> lens([0, 1, 2, 3]).both_().modify(lambda a: a + 10)
	[10, 11, 2, 3]
	>>> lens([0, 1.0, 2, 3]).both_().modify(str)
	['0', '1.0', 2, 3]

You can of course use the same shortcut for operators that single-focus
lenses allow:

	>>> lens([0, 1, 2, 3]).both_() + 10
	[10, 11, 2, 3]

Traversals can be composed with normal lenses. The result is a traversal
with the lens applied to each of its original foci:

	>>> both_first = lens([[0, 1], [2, 3]]).both_()[0]
	>>> both_first.get_all()
	[0, 2]
	>>> both_first + 10
	[[10, 1], [12, 3]]

Traversals can also be composed with other traversals just fine. They
will simply increase the number of foci targeted. Note that `get_all`
returns a flat list of foci; none of the structure of the state is
preserved.

	>>> both_twice = lens([[0, 1], [2, 3]]).both_().both_()
	>>> both_twice.get_all()
	[0, 1, 2, 3]
	>>> both_twice + 10
	[[10, 11], [12, 13]]

A slightly more useful traversal method is `each_`. `each_` will focus
all of the items in a data-structure analogous to iterating over it
using python's `iter` and `next`. It supports most of the built-in
iterables out of the box, but if you want to use it on your own objects
then you will need to add a hook yourself.

	>>> lens([1, 2, 3]).each_() + 10
	[11, 12, 13]

The `values_` method returns a traversal that focuses all of the values
in a dictionary. If we return to our `GameState` example from earlier,
we can use `values_` to move _every_ enemy in the same level 1 pixel
over to the right in one line of code:

	>>> _ = lens(old_state).worlds[2].levels[1].enemies.values_().x + 1

Or you could do the same thing to every enemy in the entire game
(assuming that there were other enemies on other levels in the
`GameState`):

	>>> _ = (lens(old_state).worlds.values_()
	...                     .levels.values_()
	...                     .enemies.values_().x) + 1


## License

python-lenses is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see http://www.gnu.org/licenses/.
