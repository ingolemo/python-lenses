from lenses import lens, bind
import greenlet

def setter_traversal(setter):
    def folder(state):
        g = greenlet.greenlet(lambda _: setter(lambda a: ret.switch(a), state))
        while not g.dead:
            ret = greenlet.getcurrent()
            result = g.switch(None)
            if not g.dead:
                yield result
    def builder(state, values):
        iterator = iter(values)
        return setter(lambda _: next(iterator), state)
    return lens.Traversal(folder, builder)

import re
state = "First thou pullest the Holy Pin"
def foo(bar,x):
    print(bar("First"))
    print(bar("thou"))
    print(bar("pullest"))
#state &= setter_traversal(foo) + "!"
#(setter_traversal(lambda f,x: re.sub("\w+", lambda m: f(m.group(0)), x)) + "!").__radd__(state)
state &= setter_traversal(lambda f,x: re.sub("\w+", lambda m: f(m.group(0)), x)) + "!"
print(state)  # "First! thou! pullest! the! Holy! Pin!"

print(bind(2)&lens.Iso(str,int).set("4"))