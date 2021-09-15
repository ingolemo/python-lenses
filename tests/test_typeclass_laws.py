import hypothesis
import hypothesis.strategies as strat

import lenses
import lenses.typeclass as tc


def objects():
    return strat.just(object())


def maybes(substrat):
    return substrat.flatmap(
        lambda a: strat.sampled_from(
            [
                lenses.maybe.Nothing(),
                lenses.maybe.Just(a),
            ]
        )
    )


# the free monoid should be good enough
monoids = strat.one_of(
    strat.integers(),
    strat.text(),
    strat.lists(strat.integers()),
    strat.tuples(strat.integers(), strat.text()),
    strat.dictionaries(strat.text(), strat.integers()),
)


def applicatives(substrat):
    return strat.one_of(
        strat.lists(substrat),
        strat.lists(substrat).map(tuple),
        substrat.map(lenses.identity.Identity),
        maybes(substrat),
    )


def functors(substrat):
    return applicatives(substrat)


@hypothesis.given(monoids)
def test_monoid_law_associativity(m1):
    # (a + b) + c = a + (b + c)
    add = tc.mappend
    assert add(add(m1, m1), m1) == add(m1, add(m1, m1))


@hypothesis.given(monoids)
def test_monoid_law_left_identity(m):
    # mempty + a = a
    assert tc.mappend(tc.mempty(m), m) == m


@hypothesis.given(monoids)
def test_monoid_law_right_identity(m):
    # a + mempty = a
    assert tc.mappend(m, tc.mempty(m)) == m


@hypothesis.given(functors(objects()))
def test_functor_law_identity(data):
    # fmap id = id
    def identity(a):
        return a

    assert tc.fmap(data, identity) == identity(data)


@hypothesis.given(functors(objects()))
def test_functor_law_distributive(functor):
    # fmap (g . f) = fmap g . fmap f
    def f1(a):
        return [a]

    f2 = str

    def composed(a):
        return f1(f2(a))

    assert tc.fmap(functor, composed) == tc.fmap(tc.fmap(functor, f2), f1)


@hypothesis.given(applicatives(objects()))
def test_applicative_law_identity(data):
    # pure id <*> v = v
    def identity(a):
        return a

    assert tc.apply(data, tc.pure(data, identity)) == data


@hypothesis.given(applicatives(objects()))
def test_applicative_law_homomorphism(appl):
    # pure f <*> pure x = pure (f x)
    x = object()
    f = id

    left = tc.apply(tc.pure(appl, x), tc.pure(appl, f))
    right = tc.pure(appl, f(x))
    assert left == right


@hypothesis.given(applicatives(objects()))
def test_applicative_law_interchange(appl):
    # u <*> pure y = pure ($ y) <*> u
    y = object()
    u = tc.pure(appl, str)

    left = tc.apply(tc.pure(appl, y), u)
    right = tc.apply(u, tc.pure(appl, lambda a: a(y)))
    assert left == right


@hypothesis.given(applicatives(objects()))
def test_applicative_law_composition(appl):
    # pure (.) <*> u <*> v <*> w = u <*> (v <*> w)
    u = tc.pure(appl, lambda a: [a])
    v = tc.pure(appl, str)
    w = appl

    def compose(f1):
        return lambda f2: lambda a: f1(f2(a))

    left = tc.apply(w, tc.apply(v, tc.apply(u, tc.pure(appl, compose))))
    right = tc.apply(tc.apply(w, v), u)
    assert left == right
