import hypothesis
import hypothesis.strategies as strat

import lenses
import lenses.typeclass as tc


class MonoidAdd:
    def __init__(self, n):
        self.n = n

    def mempty(self):
        return MonoidAdd(0)

    def mappend(self, other):
        return MonoidAdd(self.n + other.n)

    def __eq__(self, other):
        return self.n == other.n

monoids = [
    strat.lists(strat.integers()),
    strat.lists(strat.integers()).map(tuple),
    strat.text(),
    strat.integers().map(MonoidAdd),
    strat.dictionaries(strat.integers(), strat.integers()),
]


def many_one_of(*strategies):
    return strat.one_of(*(strat.streaming(s) for s in strategies))


def applicatives(substrat):
    return strat.one_of(
        strat.lists(substrat),
        strat.lists(substrat).map(tuple),
        substrat.map(lenses.identity.Identity),
    )


def functors(substrat):
    return strat.one_of(
        applicatives(substrat),
    )


def data_funcs(wrapper):
    intfuncs = strat.streaming(strat.one_of(
        strat.just(lambda a: a * 2),
        strat.just(lambda a: a + 1),
    ))
    floatfuncs = strat.streaming(strat.one_of(
        strat.just(lambda a: a / 2),
        strat.just(lambda a: a + 1.5),
    ))
    stringfuncs = strat.streaming(strat.one_of(
        strat.just(lambda a: a + '!'),
        strat.just(lambda a: (a+'#')[0]),
    ))
    return strat.one_of(
        strat.tuples(strat.integers(),
                     wrapper(strat.integers()),
                     intfuncs),
        strat.tuples(strat.floats(allow_nan=False),
                     wrapper(strat.floats(allow_nan=False)),
                     floatfuncs),
        strat.tuples(strat.text(),
                     wrapper(strat.text()),
                     stringfuncs),
    )


@hypothesis.given(many_one_of(*monoids))
def test_monoid_law_associativity(monoids):
    # (a + b) + c = a + (b + c)
    m1, m2, m3 = monoids[0], monoids[1], monoids[2]
    add = tc.mappend
    assert add(add(m1, m2), m3) == add(m1, add(m2, m3))


@hypothesis.given(strat.one_of(*monoids))
def test_monoid_law_left_identity(monoid):
    # mempty + a = a
    assert tc.mappend(tc.mempty(monoid), monoid) == monoid


@hypothesis.given(strat.one_of(*monoids))
def test_monoid_law_right_identity(monoid):
    # a + mempty = a
    assert tc.mappend(monoid, tc.mempty(monoid)) == monoid


@hypothesis.given(functors(strat.just(object())))
def test_functor_law_identity(data):
    # fmap id = id
    def identity(a):
        return a

    assert tc.fmap(data, identity) == identity(data)


@hypothesis.given(data_funcs(functors))
def test_functor_law_distributive(f):
    # fmap (g . f) = fmap g . fmap f
    _, functor, funcs = f
    f1 = funcs[0]
    f2 = funcs[1]

    def composed(a):
        return f1(f2(a))

    assert tc.fmap(functor, composed) == tc.fmap(tc.fmap(functor, f2), f1)


@hypothesis.given(applicatives(strat.integers()))
def test_applicative_law_identity(data):
    # pure id <*> v = v
    def identity(a):
        return a

    assert tc.ap(data, tc.pure(data, identity)) == data


@hypothesis.given(data_funcs(applicatives))
def test_applicative_law_homomorphism(datas):
    # pure f <*> pure x = pure (f x)
    x, appl, funcs = datas
    f = funcs[0]

    left = tc.ap(tc.pure(appl, x), tc.pure(appl, f))
    right = tc.pure(appl, f(x))
    assert left == right


@hypothesis.given(data_funcs(applicatives))
def test_applicative_law_interchange(datas):
    # u <*> pure y = pure ($ y) <*> u
    y, appl, funcs = datas
    u = tc.pure(appl, funcs[0])

    left = tc.ap(tc.pure(appl, y), u)
    right = tc.ap(u, tc.pure(appl, lambda a: a(y)))
    assert left == right


@hypothesis.given(data_funcs(applicatives))
def test_applicative_law_composition(datas):
    # pure (.) <*> u <*> v <*> w = u <*> (v <*> w)
    _, appl, funcs = datas
    u = tc.pure(appl, funcs[0])
    v = tc.pure(appl, funcs[1])
    w = appl

    def compose(f1):
        return lambda f2: lambda a: f1(f2(a))

    left = tc.ap(w, tc.ap(v, tc.ap(u, tc.pure(appl, compose))))
    right = tc.ap(tc.ap(w, v), u)
    assert left == right
