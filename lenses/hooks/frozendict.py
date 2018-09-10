from __future__ import absolute_import

import frozendict

from . import hook_funcs


@hook_funcs.setitem.register(frozendict.frozendict)
def _frozendict_setitem(self, key, value):
    if isinstance(key, str):
        return self.copy(**{key: value})
    else:
        mutable_dict = dict(self)
        mutable_dict[key] = value
        return frozendict.frozendict(mutable_dict)


@hook_funcs.to_iter.register(frozendict.frozendict)
def _frozendict_to_iter(self):
    return self.items()


@hook_funcs.from_iter.register(frozendict.frozendict)
def _frozendict_from_iter(self, iterable):
    return frozendict.frozendict(iterable)
