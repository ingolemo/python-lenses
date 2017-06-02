[![Build Status](https://travis-ci.org/ingolemo/python-lenses.svg?branch=master)](https://travis-ci.org/ingolemo/python-lenses)
[![codecov](https://codecov.io/gh/ingolemo/python-lenses/branch/master/graph/badge.svg)](https://codecov.io/gh/ingolemo/python-lenses)

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


## Documentation

The lenses library makes liberal use of docstrings, which you can access
as normal with the `pydoc` shell command, the `help` function in the
repl, or by reading the source yourself.

Most users will only need the docs from `lenses.UnboundLens`. If you want
to add hooks to allow parts of the library to work with custom objects
then you should check out the `lenses.hooks` module. Most of the fancy
lens code is in the `lenses.optics` module for those who are curious
how everything works.

Some examples are given in the [`examples`](examples) folder and a tutorial
is available in the [`tutorial`](tutorial/index.md) folder.

Here's a simple example:

```python
>>> from pprint import pprint
>>> from lenses import lens
>>> 
>>> data = [{'name': 'Jane', 'scores': ['a', 'a', 'b', 'a']},
...         {'name': 'Richard', 'scores': ['c', 'a', 'd', 'c']},
...         {'name': 'Zoe', 'scores': ['f', 'f', 'f']}]
... 
>>> format_scores = lens.each_()['scores'].each_().call_upper()
>>> cheat = lens[2]['scores'].each_().set('a')
>>>
>>> corrected = format_scores(data)
>>> pprint(corrected)
[{'name': 'Jane', 'scores': ['A', 'A', 'B', 'A']},
 {'name': 'Richard', 'scores': ['C', 'A', 'D', 'C']},
 {'name': 'Zoe', 'scores': ['F', 'F', 'F']}]
>>> 
>>> cheated = format_scores(cheat(data))
>>> pprint(cheated)
[{'name': 'Jane', 'scores': ['A', 'A', 'B', 'A']},
 {'name': 'Richard', 'scores': ['C', 'A', 'D', 'C']},
 {'name': 'Zoe', 'scores': ['A', 'A', 'A']}]
```


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
