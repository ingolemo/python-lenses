# Lens methods

So far we've seen lenses that extract data out of data-structures, but
lenses are more powerful than that. Lenses can actually perform
arbitrary computation on the data passing through them as long as that
computation can be reversed.

A simple example is that of the `item_` method which returns a lens that
focuses on a single key of a dictionary but returns both the key and the
value:

	>>> from lenses import lens

	>>> item_one = lens.item_('one')
	>>> item_one.get()({'one': 1})
	('one', 1)
	>>> item_one.set(('three', 3))({'one': 1})
	{'three': 3}

For a good example of a more complex lens, check out the `json_` method
which gives you a lens that can focus a string as though it were a parsed
json object.

	>>> data = '{"numbers":[1, 2, 3]}'
	>>> json_lens = lens.json_()
	>>> json_lens.get()(data)                               # doctest: +SKIP
	{'numbers': [1, 2, 3]}
	>>> json_lens['numbers'][1].set(4)(data)
	'{"numbers": [1, 4, 3]}'

At their heart, lenses are really just souped-up getters and setters. If
you have a getter and a setter for some data then you can turn those
into a lens using the `lens_` method. Here is how you could
recreate the `item_('one')` lens defined above in terms of
`lens_`:

	>>> def getter(current_state):
	...     return 'one', current_state['one']
	...
	>>> def setter(old_state, new_focus):
	...     key, value = new_focus
	...     new_state = old_state.copy()
	...     del new_state['one']
	...     new_state[key] = value
	...     return new_state
	...
	>>> item_one = lens.lens_(getter, setter)
	>>> item_one.get()({'one': 1})
	('one', 1)
	>>> item_one.set(('three', 3))({'one': 1})
	{'three': 3}

Recreating existing behaviour isn't very useful, but hopefully you can
see how useful it is to be able to make your own lenses just by writing
a pair of functions.

If you use custom lenses frequently then you may want to look into the
`iso_` method which is a less powerful but often more convenient version
of `lens_`.

There are a number of such more complicated lenses defined on `Lens`. To
help avoid collision with accessing attributes on the state, their names
all end with a single underscore. See `help(lenses.UnboundLens)` in
the repl for more. If you need to access an attribute on the state
that has been shadowed by one of lens' methods then you can use
`my_lens.getattr_(attribute)`.
