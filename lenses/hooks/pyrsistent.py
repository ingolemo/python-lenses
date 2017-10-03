from __future__ import absolute_import

import pyrsistent

from . import hook_funcs

pvector_type = type(pyrsistent.pvector())
pmap_type = type(pyrsistent.pmap())
pset_type = type(pyrsistent.pset())


@hook_funcs.setitem_immutable.register(pvector_type)
def _pvector_setitem_immutable(self, key, value):
    return self.set(key, value)


@hook_funcs.from_iter.register(pvector_type)
def _pvector_from_iter(self, iterable):
    return pyrsistent.pvector(iterable)


@hook_funcs.setitem_immutable.register(pmap_type)
def _pmap_setitem_immutable(self, key, value):
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


@hook_funcs.setattr_immutable.register(pyrsistent.PRecord)
def _precord_setattr_immutable(self, attr, value):
    return self.set(attr, value)


@hook_funcs.to_iter.register(pyrsistent.PRecord)
def _precord_to_iter(self):
    return self.items()


@hook_funcs.from_iter.register(pyrsistent.PRecord)
def _precord_from_iter(self, iterable):
    return type(self)(**dict(iterable))

@hook_funcs.setattr_immutable.register(pyrsistent.PClass)
def _pclass_setattr_immutable(self, attr, value):
    return self.set(attr, value)


