"""Checks of the closed forms against direct simulation and enumeration (seeded)."""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pc import estimators as est  # noqa: E402
from pc import theory as th  # noqa: E402


def simulate_check(p, s, f, n, reps, rng, fallback=False):
    wins = 0
    for _ in range(reps):
        first = None
        out = None
        for k in range(n):
            ok = rng.random() < p
            acc = rng.random() < (s if ok else f)
            if k == 0:
                first = ok
            if acc:
                out = ok
                break
        if out is None:
            out = first if fallback else False
        wins += out
    return wins / reps


def test_check_reliability_matches_simulation():
    rng = np.random.default_rng(1)
    for p, s, f, n in [(0.3, 0.9, 0.2, 5), (0.7, 0.8, 0.4, 3), (0.1, 0.95, 0.05, 20)]:
        for fb in (False, True):
            sim = simulate_check(p, s, f, n, 60000, rng, fb)
            assert abs(sim - th.reliability_check(p, s, f, n, fb)) < 0.01


def test_ceiling_is_limit_and_bayes_odds():
    p, s, f = 0.4, 0.85, 0.15
    assert abs(th.reliability_check(p, s, f, 10_000) - th.ceiling(p, s, f)) < 1e-12
    odds = th.ceiling(p, s, f) / (1 - th.ceiling(p, s, f))
    assert abs(odds - (s / f) * p / (1 - p)) < 1e-12
    # accept-everything check reduces to single-attempt accuracy; oracle reaches one
    assert abs(th.ceiling(p, 1.0, 1.0) - p) < 1e-12
    assert th.ceiling(p, 0.7, 0.0) == 1.0


def test_n_star_is_minimal_and_infinite_at_ceiling():
    p, s, f = 0.3, 0.9, 0.1
    pi = th.ceiling(p, s, f)
    for rho in (0.5, 0.7, 0.75):
        n = int(th.n_star(rho, p, s, f))
        assert th.reliability_check(p, s, f, n) >= rho
        if n > 1:
            assert th.reliability_check(p, s, f, n - 1) < rho
    assert math.isinf(th.n_star(pi, p, s, f))
    assert math.isinf(th.n_star(pi + 0.01, p, s, f))
    lr = th.required_likelihood_ratio(pi, p)
    assert abs(lr - s / f) < 1e-9


def test_population_bounds_and_icc_limits():
    pbar, s, f = 0.6, 0.9, 0.2
    vals = [th.beta_population_ceiling(pbar, icc, s, f) for icc in (0.0, 0.1, 0.4, 0.8, 0.99, 1.0)]
    assert abs(vals[0] - th.ceiling(pbar, s, f)) < 1e-12
    assert abs(vals[-1] - pbar) < 1e-12
    assert all(a >= b - 1e-9 for a, b in zip(vals, vals[1:]))  # decreasing in icc
    assert all(pbar - 1e-9 <= v <= th.ceiling(pbar, s, f) + 1e-9 for v in vals)
    # quadrature against Monte Carlo for one interior case
    rng = np.random.default_rng(2)
    k = 1 / 0.4 - 1
    ps = rng.beta(pbar * k, (1 - pbar) * k, 400000)
    mc = np.mean(s * ps / (s * ps + f * (1 - ps)))
    assert abs(mc - th.beta_population_ceiling(pbar, 0.4, s, f)) < 2e-3


def test_covariance_identity():
    rng = np.random.default_rng(3)
    p = rng.uniform(0.05, 0.95, 200)
    s = rng.uniform(0.6, 1.0, 200)
    f = rng.uniform(0.0, 0.5, 200)
    a = s * p + f * (1 - p)
    pi = s * p / a
    pooled = np.mean(a * pi) / np.mean(a)
    gap = pooled - np.mean(pi)
    assert abs(gap - np.cov(a, pi, bias=True)[0, 1] / np.mean(a)) < 1e-12


def test_repeated_checks_converge_to_most_accepted():
    q = {"right": 0.5, "w1": 0.3, "w2": 0.2}
    alpha = {"right": 0.8, "w1": 0.9, "w2": 0.1}
    c1 = th.repeated_check_ceiling(q, {"right"}, alpha, 1)
    c50 = th.repeated_check_ceiling(q, {"right"}, alpha, 50)
    assert c50 < c1 and c50 < 0.05
    det = {"right": 1.0, "w1": 1.0, "w2": 0.0}
    assert th.repeated_check_ceiling(q, {"right"}, det, 1) == th.repeated_check_ceiling(q, {"right"}, det, 9)


def make_item(answers, correct=7, confs=None, verdicts=None):
    confs = confs or [95] * len(answers)
    return est.Item("x", correct, list(zip(answers, confs)), verdicts or {})


def brute_check(item, check, n, fallback):
    """Average outcome over all orderings of the m attempts, using the first n."""
    acc = est.accept_vector(item, check)
    cor = item.correct()
    vals = []
    for perm in itertools.permutations(range(item.m)):
        out = None
        for i in perm[:n]:
            if acc[i]:
                out = cor[i]
                break
        if out is None:
            out = cor[perm[0]] if fallback else False
        vals.append(out)
    return float(np.mean(vals))


def test_check_u_statistic_equals_enumeration():
    it = make_item([7, 3, 7, None, 5, 7], verdicts={"self": {7: True, 3: True, 5: False}})
    for n in range(1, 7):
        for fb in (False, True):
            assert abs(est.reliability_check_item(it, "self", n, fb) - brute_check(it, "self", n, fb)) < 1e-12


def test_vote_plugin_matches_simulation_and_enumeration():
    q = {7: 0.45, 3: 0.35, 5: 0.15, None: 0.05}
    rng = np.random.default_rng(4)
    keys = list(q)
    for n in (1, 2, 5, 9):
        draws = rng.choice(len(keys), size=(40000, n), p=[q[k] for k in keys])
        sim = np.mean([est._vote_outcome([keys[j] for j in row], 7) for row in draws])
        assert abs(sim - est.vote_plugin(q, 7, n)) < 0.01
    it = make_item([7, 3, 7, 5, 3, 7])
    assert abs(est.reliability_vote_item(it, 1) - 0.5) < 1e-12
    for n in (7, 9, 15):
        assert abs(est.vote_plugin_mc(q, 7, n, seed=1, reps=200000) - est.vote_plugin(q, 7, n)) < 0.005


def test_oracle_and_agreement():
    it = make_item([7, 3, 7, 5, 3, 7])
    assert abs(est.reliability_oracle_item(it, 1) - 0.5) < 1e-12
    assert abs(est.reliability_oracle_item(it, 4) - 1.0) < 1e-12
    tp, fp = est.agreement_components(it)
    assert abs(tp - 3 * 2 / 30) < 1e-12 and abs(fp - 2 * 1 / 30) < 1e-12


def test_icc_anova_extremes():
    assert abs(est.icc_anova(np.array([1.0, 0.0, 1.0, 0.0]), 6) - 1.0) < 1e-12
    rng = np.random.default_rng(5)
    ph = rng.binomial(6, 0.5, 20000) / 6
    assert abs(est.icc_anova(ph, 6)) < 0.02


def test_fallback_closed_form_and_threshold():
    for p, s, f in [(0.4, 0.9, 0.15), (0.2, 0.7, 0.3), (0.8, 1.0, 0.4)]:
        for n in (1, 2, 5, 30):
            assert abs(th.reliability_check_fallback(p, s, f, n) - th.reliability_check(p, s, f, n, fallback=True)) < 1e-12
        assert abs(th.reliability_check_fallback(p, s, f, 1) - p) < 1e-12
        pi = th.ceiling(p, s, f)
        for rho in (p + 0.3 * (pi - p), p + 0.9 * (pi - p)):
            n = int(th.n_star_fallback(rho, p, s, f))
            assert th.reliability_check_fallback(p, s, f, n) >= rho - 1e-12
            assert n == 1 or th.reliability_check_fallback(p, s, f, n - 1) < rho
        assert math.isinf(th.n_star_fallback(pi, p, s, f))
