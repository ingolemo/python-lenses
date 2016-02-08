import hypothesis
import hypothesis.strategies as strat

import lenses
import lenses.typeclass as tc

monoids = [
    strat.lists(strat.integers()),
    strat.lists(strat.integers()).map(tuple),
    strat.text(),
]


def many_of(*strategies):
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
    return strat.one_of(
        strat.tuples(wrapper(strat.integers()),
                     strat.just(lambda a: a * 2),
                     strat.just(lambda a: a + 1)),
    )


@hypothesis.given(many_of(*monoids))
def test_monoid_law_associativity(monoids):
    m1, m2, m3 = monoids[0], monoids[1], monoids[2]
    add = tc.mappend
    assert add(add(m1, m2), m3) == add(m1, add(m2, m3))


@hypothesis.given(strat.one_of(*monoids))
def test_monoid_law_left_identity(monoid):
    assert tc.mappend(tc.mempty(monoid), monoid) == monoid


@hypothesis.given(strat.one_of(*monoids))
def test_monoid_law_right_identity(monoid):
    assert tc.mappend(monoid, tc.mempty(monoid)) == monoid


@hypothesis.given(functors(strat.just(object())))
def test_functor_law_identity(data):
    def identity(a):
        return a

    assert tc.fmap(data, identity) == identity(data)


@hypothesis.given(data_funcs(functors))
def test_functor_law_distributive(f):
    data, f1, f2 = f

    def composed(a):
        return f1(f2(a))

    assert tc.fmap(data, composed) == tc.fmap(tc.fmap(data, f2), f1)


@hypothesis.given(applicatives(strat.integers()))
def test_applicative_law_identity(data):
    # pure id <*> v = v
    def identity(a):
        return a

    assert tc.ap(data, tc.pure(data, identity)) == data


@hypothesis.given(applicatives(strat.integers()), data_funcs(lambda a: a))
def test_applicative_law_homomorphism(appl, datas):
    # pure f <*> pure x = pure (f x)
    data, f1, f2 = datas

    left = tc.ap(tc.pure(appl, data), tc.pure(appl, f1))
    right = tc.pure(appl, f1(data))
    assert left == right


# @hypothesis.given()
# def test_applicative_law_interchange():
#     # u <*> pure y = pure ($ y) <*> u
#     assert True


# @hypothesis.given()
# def test_applicative_law_composition():
#     # pure (.) <*> u <*> v <*> w = u <*> (v <*> w)
#     def compose(f1):
#         return lambda f2: lambda a: f1(f2(a))
#     assert True
