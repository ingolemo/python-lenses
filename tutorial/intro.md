# Introduction

For most users, the lenses library exports only one thing worth knowing
about; a `lens` object:

	>>> from lenses import lens

The `lens` object is an instance of `lenses.UnboundLens`. An unbound
lens represents a computation that you want to perform in order to access
your data from within some data-structure.

Here's some simple data:

	>>> data = [1, 2, 3]

Suppose that we wanted to access that `2` in the middle. Ordinarily in
python we would index into the list like so:

	>>> data[1]
	2

A bit of terminology; the data-structure that we are trying to pull
information out of (in this case; `[1, 2, 3]`) is referred to as the
_state_. The piece of data inside the state that we are trying to access
(in this case; `2`) is called the _focus_. The lenses documentation uses
these terms consistantly. For those who are unaware, the word "focus"
has an unusual plural; _foci_.

We can represent this pattern of access using lenses by doing the same
thing to `lens`:

	>>> getitem_one = lens[1]

The `getitem_one` variable is now a lens object that knows how to retrieve
values from states by indexing them with a `1`. All lenses have readable
reprs, which means that you can always print a lens to see how it is
structured:

	>>> getitem_one
	UnboundLens(GetitemLens(1))

Now that we have a representation of our data access we can use it to
actually access our focus. We do this by calling the `get` method on the
lens. The `get` method returns a function that that does the equivalent
of indexing `1`. The returned function takes one argument — the state.

	>>> getitem_one_getter = getitem_one.get()
	>>> getitem_one_getter(data)
	2

We ran through this code quite slowly for explaination purposes, but
there's no reason you can't do all of this on one line without all those
intermediate variables, if you find that more useful:

	>>> lens[1].get()(data)
	2

Now, the above code was an aweful lot of work just to do the equivalent
of `data[1]`. However, we can use this same lens to do other tasks. One
thing we can do is create a function that can set our focus to some
other value. We can do that with the `set` method. The `set` method
takes a single argument that is the new value you want to set and,
again, it returns a function that can do the task of setting.

	>>> getitem_one_set_to_four = getitem_one.set(4)
	>>> getitem_one_set_to_four(data)
	[1, 4, 3]

It may seem like our `getitem_one_set_to_four` function does the
equivalent of `data[1] = 4`, but this is not quite true. The setter
function we produced is actually an immutable setter; it takes an
old state and produces a new state with the focus set to a different
value. The original state remains unchanged:

	>>> data
	[1, 2, 3]

Lenses are especially well suited to working with nested data structures.
Here we have a two dimensional list:

	>>> data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

To access that `8` we simply create a lens and "walk" to the focus the same
way we would without the lens:

	>>> two_one_lens = lens[2][1]
	>>> two_one_lens.get()(data)
	8
	>>> two_one_lens.set(10)(data)
	[[1, 2, 3], [4, 5, 6], [7, 10, 9]]

Lenses are smart enough to only make copies of the parts of our state
that we need to change. The third sublist is a different list from the
one in the original because it has different contents, but the first
and second sublists are reused to save time and memory:

	>>> new_data = _
	>>> data[0] is new_data[0]
	True
	>>> data[1] is new_data[1]
	True
	>>> data[2] is new_data[2]
	False

Lenses support more than just lists. Any mutable python object that can
by copied with `copy.copy` will work. Immutable objects need special
support, but support for any python object can be added so long as you
know how to construct a new version of that object with the appropriate
data changed. `tuples` and `namedtuples` are supported out of the box.

Here's an example using a tuple:

	>>> data = 1, 2, 3
	>>> lens[1].get()(data)
	2
	>>> lens[1].set(4)(data)
	(1, 4, 3)

Here's a dictionary:

	>>> data = {'hello': 'world'}
	>>> lens['hello'].get()(data)
	'world'
	>>> lens['hello'].set('everyone')(data)
	{'hello': 'everyone'}

So far we have only created lenses by indexing, but we can also access
attributes. Here we focus the `contents` attribute of a custom `Container`
class:

	>>> class Container(object):
	...     def __init__(self, contents):
	...         self.contents = contents
	...     def __repr__(self):
	...         return 'Container({!r})'.format(self.contents)
	>>> data = Container(1)
	>>> lens.contents.set(2)(data)
	Container(2)

Of course, nesting all of these things also works. In this example we
change a value in a dictionary, which is an attribute of our custom class,
which is one of the elements in a tuple:

	>>> data = (0, Container({'hello': 'world'}))
	>>> lens[1].contents['hello'].set('everyone')(data)
	(0, Container({'hello': 'everyone'}))

Getting and setting a focus inside a state is pretty neat. But most
of the time, when you are accessing data, you want to set the new data
based on the old value. You _could_ get the value, do your computation,
and the set the new value like this:

	>>> data = [1, 2, 3]
	>>> my_lens = lens[1]
	>>> value = my_lens.get()(data)
	>>> my_lens.set(value * 10)(data)
	[1, 20, 3]

Fortunately, this kind of operation is so common that lenses support
it natively. If you have a function that you want to call on your focus
then you can do that with the `modify` method:

	>>> data = [1, -2, 3]
	>>> lens[1].modify(abs)(data)
	[1, 2, 3]

You can, of course, use a `lambda` if you need a function on-demand:

	>>> data = [1, 2, 3]
	>>> lens[1].modify(lambda n: n * 10)(data)
	[1, 20, 3]

Often times, the function that we want to call on our focus is actually
one of the focus's methods. To call a method on the focus, we can use the
`call` method. It takes a string with the name of the method to call.

	>>> data = ['one', 'two', 'three']
	>>> lens[1].call('upper')(data)
	['one', 'TWO', 'three']

The method that you are calling __must__ return the new focus that you want
to appear in the new state. Many methods work by mutating their data.
Such methods will not work the way you expect with `call`:

	>>> data = [1, [3, 4, 2], 5]
	>>> lens[1].call('sort')(data)
	[1, None, 5]

Furthermore, any mutation that method performs will surface in the
original state:

	>>> data
	[1, [2, 3, 4], 5]

You can still call such methods safely by using lens's `call_mut` method.
The `call_mut` method works by making a deep copy of the focus before
calling anything on it.

	>>> data = [1, [3, 4, 2], 5]
	>>> lens[1].call_mut('sort')(data)
	[1, [2, 3, 4], 5]

If you can be sure that the method you want to call will only mutate
the focus itself and not any of its sub-data then you can pass a
`shallow=True` keyword argument to `call_mut` and it will only make a
shallow copy.

	>>> data = [1, [3, 4, 2], 5]
	>>> lens[1].call_mut('sort', shallow=True)(data)
	[1, [2, 3, 4], 5]

You can pass extra arguments to both `call` and `call_mut` and they will
be forwarded on:

	>>> data = [1, 2, 3]
	>>> lens[1].call('__mul__', 10)(data)
	[1, 20, 3]

Since wanting to call an object's dunder methods is so common, lenses
will also pass most operators through to the data they're focused on. This
can make using lenses in your code much more readable:

	>>> data = [1, 2, 3]
	>>> index_one_times_ten = lens[1] * 10
	>>> index_one_times_ten(data)
	[1, 20, 3]

The only operator that you can't use in this way is `&` (the _bitwise and_
operator, magic method `__and__`). Lenses reserve this for something else.
If you wish to `&` your focus, you can use the `bitwise_and` method instead.

Lenses work best when you have to manipulate highly nested data
structures that hold a great deal of state, such as when programming
games:

	>>> from collections import namedtuple
	>>>
	>>> GameState = namedtuple('GameState',
	...     'current_world current_level worlds')
	>>> World = namedtuple('World', 'theme levels')
	>>> Level = namedtuple('Level', 'map enemies')
	>>> Enemy = namedtuple('Enemy', 'x y')
	>>>
	>>> data = GameState(1, 2, {
	...     1: World('grassland', {}),
	...     2: World('desert', {
	...         1: Level({}, {
	...             'goomba1': Enemy(100, 45),
	...             'goomba2': Enemy(130, 45),
	...             'goomba3': Enemy(160, 45),
	...         }),
	...     }),
	... })
	>>>
	>>> new_data = (lens.worlds[2].levels[1].enemies['goomba3'].x + 1)(data)

With the structure above, that last line of code produces a new
`GameState` object where the third enemy on the first level of the
second world has been moved across by one pixel without any of the
objects in the original state being mutated. Without lenses this would
take a rather large amount of plumbing to achieve.
