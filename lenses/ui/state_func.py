from typing import Callable, Generic, TypeVar

Argument = TypeVar("Argument")
Result = TypeVar("Result")


class StateFunction(Callable[[Argument], Result]):
    """A wrapper around a function that takes a state and returns a
    transformed state. This wrapper can be called directly `self(state)`
    or you can use the bitwise and operator `state & self`. This syntax is common in haskell code. It also allows reassignments to be more pleasant; instead of
    `state = self(state)` you can write `state &= self`."""

    def __init__(self, func: Callable[[Argument], Result]):
        self.func = func

    def __call__(self, arg: Argument) -> Result:
        return self.func(arg)

    def __rand__(self, other: Argument) -> Result:
        return self.func(other)
