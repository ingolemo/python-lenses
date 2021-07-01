from .hook_funcs import (
    __doc__,
    contains_add,
    contains_remove,
    from_iter,
    setattr,
    setitem,
    to_iter,
)

supported_modules = ["pyrsistent"]

for _hook in supported_modules:
    try:
        __import__(_hook)
    except ImportError:
        pass
    else:
        _subname = "{}.{}".format(__name__, _hook)
        __import__(_subname)
