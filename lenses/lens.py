from .identity import Identity
from .const import Const
from .typeclass import fmap, ap
from .setter import magic_set


def make_lens(getter, setter):
    '''turns a pair of getter and setter functions into a van Laarhoven
    lens. A getter function is one that takes a state and returns a
    value derived from that state. A setter function takes a new value and
    an old state and injects the new value into the old state, returning
    a new state.

    make_lens :: getter_func, setter_func -> Lens
    getter_func :: state -> value
    setter_func :: new_value, old_state -> new_state
    '''

    def new_func(func, state):
        old_value = getter(state)
        fa = func(old_value)
        return fmap(fa, lambda a: setter(a, state))

    return Lens(new_func)


class Lens:
    '''A Lens. Serves as the backbone of the lenses library. Acts as an
    object-oriented wrapper around a function that does all the hard
    work. This function is a van Laarhoven lens and has the following
    type (in ML-style notation):

    func :: (value -> functor value), state -> functor state
    '''
    __slots__ = ['func']

    def __init__(self, func):
        self.func = func

    @classmethod
    def trivial(cls):
        'Returns a trivial lens that magnifies to the whole state.'
        return Lens(lambda fn, state: fmap(
            fn(state),
            lambda newvalue: newvalue
        ))

    def get(self, state):
        'Returns the value this lens is magnified on.'
        return self.func(lambda a: Const(a), state).item

    def modify(self, state, fn):
        'Applies a function to the magnified value.'
        return self.func(lambda a: Identity(fn(a)), state).item

    def set(self, state, newitem):
        'Sets the magnified value in the passed state.'
        return self.func(lambda a: Identity(newitem), state).item

    def compose(self, other):
        '''Composes another lens with this one.

        The `other` lens is used to refine the `self` lens. The
        following two pieces of code should be equivalent:

            self.compose(other).get(state)

            other.get(self.get(state))
        '''

        def new_func(fn, state):
            return self.func((lambda state2: other.func(fn, state2)), state)

        return Lens(new_func)

    def both(self):
        def new_func(func, state):
            make_new = lambda a: (
                lambda b: magic_set(
                    magic_set(state, 'setitem', 0, a),
                    'setitem', 1, b))
            return ap(func(state[0]), fmap(func(state[1]), make_new))

        return self.compose(Lens(new_func))
