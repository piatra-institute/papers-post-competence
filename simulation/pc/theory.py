"""Closed forms for reliability under repeated sampling with an acceptance check.

Notation (one task item): p = probability that an attempt is correct; s = probability that the check
accepts a correct output (sensitivity); f = probability that it accepts an incorrect one (false
acceptance). a = s p + f (1 - p) is the acceptance probability of one attempt and r = 1 - a the
rejection probability. Attempts and verdicts are independent given the item.
"""
from __future__ import annotations

import math

import numpy as np


def acceptance(p: float, s: float, f: float) -> float:
    return s * p + f * (1.0 - p)


def ceiling(p: float, s: float, f: float) -> float:
    """Limit of accept-the-first-passing reliability: the check's precision at base rate p."""
    a = acceptance(p, s, f)
    return s * p / a if a > 0 else 0.0


def reliability_first(p: float, n: int = 1) -> float:
    return p


def reliability_oracle(p: float, n: int) -> float:
    return 1.0 - (1.0 - p) ** n


def reliability_check(p: float, s: float, f: float, n: int, fallback: bool = False) -> float:
    """Accept the first of n attempts that passes; abstain (or return the first attempt) if none passes."""
    a = acceptance(p, s, f)
    if a <= 0:
        return p if fallback else 0.0
    r = 1.0 - a
    out = ceiling(p, s, f) * (1.0 - r ** n)
    if fallback and r > 0:
        out += r ** n * (1.0 - s) * p / r
    return out


def n_star(rho: float, p: float, s: float, f: float) -> float:
    """Smallest n with reliability_check(p, s, f, n) >= rho (abstention); inf if rho >= ceiling."""
    pi = ceiling(p, s, f)
    if rho >= pi:
        return math.inf
    a = acceptance(p, s, f)
    if a >= 1.0:
        return 1.0
    return float(max(1, math.ceil(math.log(1.0 - rho / pi) / math.log(1.0 - a) - 1e-12)))


def reliability_check_fallback(p: float, s: float, f: float, n: int) -> float:
    """Closed form with fallback to the first attempt: pi - (pi - p) (1 - a)^(n - 1)."""
    a = acceptance(p, s, f)
    if a <= 0:
        return p
    pi = ceiling(p, s, f)
    return pi - (pi - p) * (1.0 - a) ** (n - 1)


def n_star_fallback(rho: float, p: float, s: float, f: float) -> float:
    """Smallest n with reliability_check_fallback >= rho; 1 if rho <= p; inf if rho >= ceiling."""
    if rho <= p:
        return 1.0
    pi = ceiling(p, s, f)
    if rho >= pi:
        return math.inf
    a = acceptance(p, s, f)
    if a >= 1.0:
        return 2.0
    return float(1 + math.ceil(math.log((pi - rho) / (pi - p)) / math.log(1.0 - a) - 1e-12))


def required_likelihood_ratio(rho: float, p: float) -> float:
    """s/f must exceed this for the ceiling to exceed rho: odds(rho) / odds(p)."""
    return (rho / (1.0 - rho)) / (p / (1.0 - p))


def jensen_second_order(pbar: float, var_p: float, s: float, f: float) -> float:
    """Second-order approximation of E[ceiling(p_i)] around pbar."""
    d = f + (s - f) * pbar
    second = -2.0 * s * f * (s - f) / d ** 3
    return ceiling(pbar, s, f) + 0.5 * second * var_p


def beta_population_ceiling(pbar: float, icc: float, s: float, f: float, nodes: int = 200) -> float:
    """E[ceiling(p_i)] for p_i ~ Beta with mean pbar and intraclass correlation icc = 1/(alpha+beta+1).

    Gauss-Jacobi quadrature integrates the Beta weight exactly, including its endpoint singularities.
    """
    if icc <= 0:
        return ceiling(pbar, s, f)
    if icc >= 1:
        return pbar * ceiling(1.0, s, f) + (1 - pbar) * ceiling(0.0, s, f)
    from scipy.special import roots_jacobi

    k = 1.0 / icc - 1.0
    al, be = pbar * k, (1 - pbar) * k
    x, w = roots_jacobi(nodes, be - 1.0, al - 1.0)
    pp = (1.0 + x) / 2.0
    vals = s * pp / (s * pp + f * (1.0 - pp))
    return float(np.sum(w * vals) / np.sum(w))


def repeated_check_ceiling(q: dict, correct: set, alpha: dict, k: int) -> float:
    """Ceiling when each candidate must pass k conditionally independent checks with acceptance alpha[y]."""
    num = sum(q[y] * alpha[y] ** k for y in q if y in correct)
    den = sum(q[y] * alpha[y] ** k for y in q)
    return num / den if den > 0 else 0.0
