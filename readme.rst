
Lenses
======

.. image:: https://travis-ci.org/ingolemo/python-lenses.svg
    :target: https://travis-ci.org/ingolemo/python-lenses

.. image:: https://codecov.io/gh/ingolemo/python-lenses/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/ingolemo/python-lenses

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

Some examples are given in the `examples`_ folder and a tutorial is
available in the `tutorial`_ folder.

.. _examples: examples
.. _tutorial: tutorial/index.rst


Example
-------

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

::

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
