
Lenses
======

Lenses is a python library that helps you to manipulate large
data-structures without mutating them. It is inspired by the lenses in
Haskell, although it's much less principled and the api is more suitable
for python.


Installation
------------

You can install the latest version from pypi using pip like so::

    pip install lenses

You can uninstall similarly::

    pip uninstall lenses


Documentation
-------------

The lenses library makes liberal use of docstrings, which you can access
as normal with the ``pydoc`` shell command, the ``help`` function in
the repl, or by reading the source yourself.

Most users will only need the docs from ``lenses.UnboundLens``. If you
want to add hooks to allow parts of the library to work with custom
objects then you should check out the ``lenses.hooks`` module. Most of
the fancy lens code is in the ``lenses.optics`` module for those who
are curious how everything works.

Some examples are given in the `examples`_ folder and the `documentation`_
is available on ReadTheDocs.

.. _examples: examples
.. _documentation: https://python-lenses.readthedocs.io/en/latest/


Example
-------

.. code:: pycon

    >>> from pprint import pprint
    >>> from lenses import lens
    >>>
    >>> data = [{'name': 'Jane', 'scores': ['a', 'a', 'b', 'a']},
    ...         {'name': 'Richard', 'scores': ['c', None, 'd', 'c']},
    ...         {'name': 'Zoe', 'scores': ['f', 'f', None, 'f']}]
    ... 
    >>> format_scores = lens.Each()['scores'].Each().Instance(str).call_upper()
    >>> cheat = lens[2]['scores'].Each().set('a')
    >>>
    >>> corrected = format_scores(data)
    >>> pprint(corrected)
    [{'name': 'Jane', 'scores': ['A', 'A', 'B', 'A']},
     {'name': 'Richard', 'scores': ['C', None, 'D', 'C']},
     {'name': 'Zoe', 'scores': ['F', 'F', None, 'F']}]
    >>>
    >>> cheated = format_scores(cheat(data))
    >>> pprint(cheated)
    [{'name': 'Jane', 'scores': ['A', 'A', 'B', 'A']},
     {'name': 'Richard', 'scores': ['C', None, 'D', 'C']},
     {'name': 'Zoe', 'scores': ['A', 'A', 'A', 'A']}]


The definition of ``format_scores`` means "for each item in the data take
the value with the key of ``'scores'`` and then for each item in that list
that is an instance of ``str``, call its ``upper`` method on it". That one
line is the equivalent of this code:

.. code:: python

    def format_scores(data):
        results = []
        for entry in data:
            result = {}
            for key, value in entry.items():
                if key == 'scores':
                    new_value = []
                    for letter in value:
                        if isinstance(letter, str):
                            new_value.append(letter.upper())
                        else:
                            new_value.append(letter)
                    result[key] = new_value
                else:
                    result[key] = value
            results.append(result)
        return results

Now, this code can be simplified using comprehensions. But comprehensions
only work with lists, dictionaries, and sets, whereas the lenses library
can work with arbitrary python objects.

Here's an example that shows off the full power of this library:

.. code:: pycon

    >>> from lenses import lens
    >>> state = (("foo", "bar"), "!", 2, ())
    >>> lens.Recur(str).Each().Filter(lambda c: c <= 'm').Parts().call_mut_reverse()(state)
    (('!oo', 'abr'), 'f', 2, ())

This is an example from the `Putting Lenses to Work`__ talk about the
haskell lenses library by John Wiegley. We extract all the strings inside
of ``state``, extract the characters, filter out any characters that
come after ``'m'`` in the alphabet, treat these characters as if they
were a list, reverse that list, before finally placing these characters
back into the state in their new positions.

.. _putting_lenses_to_work: https://www.youtube.com/watch?v=QZy4Yml3LTY&t=2250

__ putting_lenses_to_work_

This example is obviously very contrived, but I can't even begin to
imagine how you would do this in python code without lenses.


License
-------

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
