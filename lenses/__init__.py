from .lens import Lens


def lens(obj=None):
    '''Returns a simple Lens bound to `obj`. If `obj is None` then the
    Lens object is unbound.'''
    return Lens(obj)
