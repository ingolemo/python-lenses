from __future__ import absolute_import

from typing import Type

import pyrsistent

from . import hook_funcs

pvector_type = type(pyrsistent.pvector())  # type: Type[pyrsistent.PVector]
pmap_type = type(pyrsistent.pmap())  # type: Type[pyrsistent.PMap]
pset_type = type(pyrsistent.pset())  # type: Type[pyrsistent.PSet]


@hook_funcs.setitem.register(pvector_type)
def _pvector_setitem(self, key, value):
    return self.set(key, value)


@hook_funcs.from_iter.register(pvector_type)
def _pvector_from_iter(self, iterable):
    return pyrsistent.pvector(iterable)


@hook_funcs.setitem.register(pmap_type)
def _pmap_setitem(self, key, value):
    return self.set(key, value)


@hook_funcs.to_iter.register(pmap_type)
def _pmap_to_iter(self):
    return self.items()


@hook_funcs.from_iter.register(pmap_type)
def _pmap_from_iter(self, iterable):
    return pyrsistent.pmap(iterable)


@hook_funcs.from_iter.register(pset_type)
def _pset_from_iter(self, iterable):
    return pyrsistent.pset(iterable)


@hook_funcs.setattr.register(pyrsistent.PRecord)
def _precord_setattr(self, attr, value):
    return self.set(attr, value)


@hook_funcs.to_iter.register(pyrsistent.PRecord)
def _precord_to_iter(self):
    return self.items()


@hook_funcs.from_iter.register(pyrsistent.PRecord)
def _precord_from_iter(self, iterable):
    return type(self)(**dict(iterable))


@hook_funcs.setattr.register(pyrsistent.PClass)
def _pclass_setattr(self, attr, value):
    return self.set(attr, value)
