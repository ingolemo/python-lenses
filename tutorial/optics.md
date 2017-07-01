# Optics

Lenses are just one in a whole family of related objects called
_optics_. Optics generalise the notion of accessing data.

The heirarchy of optics looks like this:

![Optics family](optics_family.png)

An arrow pointing from A to B here means that all B are also A. For
example, all Lenses are also Getters, and all Getters are also Folds.

When we compose two optics together, the result is the most-recent
common ancestor of the two. For example, if we compose a Getter and a
Traversal then the optic we get back would be a Fold because Getters and
Traversals are both kinds of Fold. We cannot compose two optics that do
not share a common ancestor; e.g. we cannot compose a Fold with a Setter.

You can find out the kind of a lens using the `kind` method:

	>>> from lenses import lens
	>>> my_lens = lens[0]
	>>> my_lens.kind()
	'Lens'
	>>> my_prism = lens.instance_(str)
	>>> my_prism.kind()
	'Prism'
	>>> my_traversal = my_lens & my_prism
	>>> my_traversal.kind()
	'Traversal'


## Traversals

All the optics that we have seen so far have been lenses, so they always
focused a single object inside a state. But it is possible for an optic
to have more than one focus. One such optic is the traversal. A simple
traversal can be made with the `_both` method. `lens.both_()` focuses
the two objects at indices `0` and `1` within the state. It is intended
to be used with tuples of length 2, but will work on any indexable object.

One issue with multi-focus optics is that the `get` method only ever
returns a single focus. It will return the _first_ item focused by the
optic. If we want to get all the items focused by that optic then we
can use the `collect` method which will return those objects in a list:

	>>> data = [0, 1, 2, 3]
	>>> both = lens.both_()
	>>> both.get()(data)
	0
	>>> both.collect()(data)
	[0, 1]

Setting works with a traversal, though all foci will be set to the same
object.

	>>> both.set(4)(data)
	[4, 4, 2, 3]

Modifying is the most useful operation we can perform. The modification
will be applied to all the foci independently. All the foci must be of
the same type (or at least be of a type that supports the modification
that we want to make).

	>>> both.modify(lambda a: a + 10)(data)
	[10, 11, 2, 3]
	>>> both.modify(str)([0, 1.0, 2, 3])
	['0', '1.0', 2, 3]

You can of course use the same shortcut for operators that single-focus
lenses allow:

	>>> (both + 10)(data)
	[10, 11, 2, 3]

Traversals can be composed with normal lenses. The result is a traversal
with the lens applied to each of its original foci:

	>>> data = [[0, 1], [2, 3]]
	>>> both_then_zero = lens.both_()[0]
	>>> both_then_zero.collect()(data)
	[0, 2]
	>>> (both_then_zero + 10)(data)
	[[10, 1], [12, 3]]

Traversals can also be composed with other traversals just fine. They
will simply increase the number of foci targeted. Note that `collect`
returns a flat list of foci; none of the structure of the state is
preserved.

	>>> both_twice = lens.both_().both_()
	>>> both_twice.collect()(data)
	[0, 1, 2, 3]
	>>> (both_twice + 10)(data)
	[[10, 11], [12, 13]]

A slightly more useful traversal method is `each_`. `each_` will focus
all of the items in a data-structure analogous to iterating over it
using python's `iter` and `next`. It supports most of the built-in
iterables out of the box, but if we want to use it on our own objects
then we will need to add a hook explicitly.

	>>> data = [1, 2, 3]
	>>> (lens.each_() + 10)(data)
	[11, 12, 13]

The `values_` method returns a traversal that focuses all of the values
in a dictionary. If we return to our `GameState` example from earlier,
we can use `values_` to move _every_ enemy in the same level 1 pixel
over to the right in one line of code:

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
	>>> level_enemies_right = (lens.worlds[2]
	...                            .levels[1]
	...                            .enemies.values_().x + 1)
	>>> new_data = level_enemies_right(data)

Or we could do the same thing to every enemy in the entire game
(assuming that there were other enemies on other levels in the
`GameState`):

	>>> all_enemies_right = (lens.worlds.values_()
	...                          .levels.values_()
	...                          .enemies.values_().x + 1)
	>>> new_data = all_enemies_right(data)


## Getter

A Getter is an optic that knows how to retrieve a single focus from a
state. You can think of a Getter as a Lens that does not have a setter
function. Because it does not have a setter function, we cannot use
a Getter to `set` values. You also cannot use `modify`, `call`, or
`call_mut` because these all make use of the setting machinery. The
only method we can meaningly perform on a Getter is `get`. We can call
`collect`, but it will always give us a list containing a single focus.

The simplest way to make a Getter is with the `f_` method. This method
takes a function and returns a Getter that just calls that function on
the state in order and whatever that function returns is the focus.

	>>> data = 1
	>>> def get_negative(state):
	...     return -state
	>>> neg_getter = lens.f_(get_negative)
	>>> neg_getter.get()(data)
	-1

If we try to call `set` or any other invalid method on a Getter then
we will get an exception:

	>>> neg_getter.set(2)(data)
	Traceback (most recent call last):
	  File "<stdin>", line 1, in ?
	TypeError: Must be an instance of Setter to .set()

You might notice that `lens.f_(some_function).get()` is exactly equivalent
to using `some_function` by itself. For this reason Getters on their
own are not particularly useful. The utility of Getters comes when we
compose them with other optics.

	>>> data = [1, 2, 3]
	>>> each_neg = lens.each_().f_(get_negative)
	>>> each_neg.collect()(data)
	[-1, -2, -3]

Getters allow you to _inject_ arbitrary behaviour into the middle of an
optic at the cost of not being able to set anything:

	>>> def log(focus):
	...     print('logged: {!r}'.format(focus))
	...     return focus
	>>> data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
	>>> lens.each_().f_(log).each_().collect()(data)
	logged: [1, 2, 3]
	logged: [4, 5, 6]
	logged: [7, 8, 9]
	[1, 2, 3, 4, 5, 6, 7, 8, 9]


## Folds

A Fold is to a Getter what a Traversal is to a Lens. That is, a Fold is
a Getter that can get multiple foci. Just like Getters, you cannot set
anything with a Fold. Just like Traversals, when using a Fold, you will
want to prefer the `collect` method over `get`.

A Fold can be constructed from any function that returns an iterator
using the `fold_` method. Generator functions are particularly useful
for making Folds.

	>>> def ends(state):
	...     yield state[0]
	...     yield state[-1]
	>>> data = [1, 2, 3]
	>>> lens.fold_(ends).collect()(data)
	[1, 3]

A useful Fold is `iter_`. This Fold just iterates over the state directly.
It's very similar to the `each_` Traversal, but while `each_` has the
ability set foci as well as get them, `iter_` does not need any special
support; it will work on any iterable python object. `lens.iter_()`
is equivalent to `lens.fold_(iter)`

Just as with Getters, Folds don't do much on their own; you will want
to compose them:

	>>> data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
	>>> lens.iter_().fold_(ends).f_(get_negative).collect()(data)
	[-1, -3, -4, -6, -7, -9]
