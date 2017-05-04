import hypothesis
import hypothesis.strategies as strat
from hypothesis.strategies import just, one_of, sampled_from, streaming

import lenses
import lenses.typeclass as tc


class MonoidProduct(object):

    def __init__(self, n):
        self.n = n

    def __add__(self, other):
        return MonoidProduct(self.n * other.n)

    def __eq__(self, other):
        return self.n == other.n

    def mempty(self):
        return MonoidProduct(1)


def many_one_of(*strategies):
    return one_of(*(streaming(s) for s in strategies))


def apply_strat(funcstrat, substrat):
    return substrat.flatmap(lambda a: funcstrat.map(lambda f: f(a)))


def stream_apply_strat(funcstrat, substrat):
    return funcstrat.flatmap(lambda fn: substrat.map(lambda s: s.map(fn)))


def maybes():
    return strat.sampled_from([
        lambda a: lenses.maybe.Nothing(),
        lenses.maybe.Just,
    ])


def monoids():
    base = many_one_of(
        strat.integers(),
        strat.lists(strat.integers()),
        strat.lists(strat.integers()).map(tuple),
        strat.text(),
        strat.integers().map(MonoidProduct),
        strat.dictionaries(strat.integers(), strat.integers()),
    )

    def recurse(substrat):
        return stream_apply_strat(maybes(), substrat)

    return strat.recursive(base, recurse)


def applicatives(substrat):
    return one_of(
        strat.lists(substrat),
        strat.lists(substrat).map(tuple),
        substrat.map(lenses.identity.Identity),
        apply_strat(maybes(), substrat),
    )


def functors(substrat):
    return one_of(applicatives(substrat), )


def data_funcs(wrapper):
    intfuncs = streaming(sampled_from([lambda a: a * 2, lambda a: a + 1, ]))
    floatfuncs = streaming(sampled_from([
        lambda a: a / 2,
        lambda a: a + 1.5,
    ]))
    stringfuncs = streaming(sampled_from([
        lambda a: a + '!',
        lambda a: (a + '#')[0],
    ]))
    unistringfuncs = streaming(sampled_from([
        lambda a: a + u'!',
        lambda a: (a + u'#')[0],
    ]))
    def make_option(strategy, funcs):
        return strat.tuples(strategy, wrapper(strategy), funcs)
    return one_of(
        make_option(strat.integers(), intfuncs),
        make_option(strat.floats(allow_nan=False), floatfuncs),
        make_option(strat.text(), stringfuncs),
        make_option(strat.characters(), unistringfuncs),
    )


@hypothesis.given(monoids())
def test_monoid_law_associativity(monoids):
    # (a + b) + c = a + (b + c)
    m1, m2, m3 = monoids[0], monoids[1], monoids[2]
    add = tc.mappend
    assert add(add(m1, m2), m3) == add(m1, add(m2, m3))


@hypothesis.given(monoids())
def test_monoid_law_left_identity(monoids):
    # mempty + a = a
    monoid = monoids[0]
    assert tc.mappend(tc.mempty(monoid), monoid) == monoid


@hypothesis.given(monoids())
def test_monoid_law_right_identity(monoids):
    # a + mempty = a
    monoid = monoids[0]
    assert tc.mappend(monoid, tc.mempty(monoid)) == monoid


@hypothesis.given(functors(just(object())))
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

    assert tc.apply(data, tc.pure(data, identity)) == data


@hypothesis.given(data_funcs(applicatives))
def test_applicative_law_homomorphism(datas):
    # pure f <*> pure x = pure (f x)
    x, appl, funcs = datas
    f = funcs[0]

    left = tc.apply(tc.pure(appl, x), tc.pure(appl, f))
    right = tc.pure(appl, f(x))
    assert left == right


@hypothesis.given(data_funcs(applicatives))
def test_applicative_law_interchange(datas):
    # u <*> pure y = pure ($ y) <*> u
    y, appl, funcs = datas
    u = tc.pure(appl, funcs[0])

    left = tc.apply(tc.pure(appl, y), u)
    right = tc.apply(u, tc.pure(appl, lambda a: a(y)))
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

    left = tc.apply(w, tc.apply(v, tc.apply(u, tc.pure(appl, compose))))
    right = tc.apply(tc.apply(w, v), u)
    assert left == right
