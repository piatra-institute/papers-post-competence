"""Estimators of reliability-versus-attempts curves from m attempts per item.

For budgets n <= m the estimators are exact U-statistics: the average outcome over all orderings (or
subsets) of the m observed attempts, which is unbiased for the expected outcome of n independent
attempts at that item, conditional on the realised check verdicts. For n > m they are plug-in values
from the item's observed frequencies.
"""
from __future__ import annotations

import itertools
import math
from collections import Counter
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Item:
    item_id: str
    answer: int
    attempts: list  # list of (parsed answer or None, stated confidence or None)
    verdicts: dict = field(default_factory=dict)  # check name -> {candidate answer: bool}

    @property
    def m(self) -> int:
        return len(self.attempts)

    def correct(self) -> list[bool]:
        return [a is not None and a == self.answer for a, _ in self.attempts]

    def p_hat(self) -> float:
        return sum(self.correct()) / self.m


def accept_vector(item: Item, check: str, tau: int = 90) -> list[bool]:
    """Per-attempt acceptance under a named check. Attempts without a parsed answer are rejected."""
    out = []
    for (ans, conf), ok in zip(item.attempts, item.correct()):
        if ans is None:
            out.append(False)
        elif check == "none":
            out.append(True)
        elif check == "oracle":
            out.append(ok)
        elif check == "confidence":
            out.append(conf is not None and conf >= tau)
        else:
            out.append(bool(item.verdicts[check].get(ans, False)))
    return out


def check_counts(item: Item, check: str, tau: int = 90) -> tuple[int, int, int, int]:
    """(correct & accepted, wrong & accepted, rejected, correct & rejected)."""
    acc = accept_vector(item, check, tau)
    cor = item.correct()
    A = sum(a and c for a, c in zip(acc, cor))
    B = sum(a and not c for a, c in zip(acc, cor))
    J = item.m - A - B
    Jc = sum((not a) and c for a, c in zip(acc, cor))
    return A, B, J, Jc


def _comb_ratio(J: int, m: int, n: int) -> float:
    """Probability that the first n of a random ordering of m attempts are all among J rejected ones."""
    return math.comb(J, n) / math.comb(m, n) if n <= J else 0.0


def reliability_check_item(item: Item, check: str, n: int, fallback: bool, tau: int = 90) -> float:
    A, B, J, Jc = check_counts(item, check, tau)
    m = item.m
    pi = A / (A + B) if A + B > 0 else 0.0
    if n <= m:
        none_acc = _comb_ratio(J, m, n)
    else:
        none_acc = (J / m) ** n
    out = pi * (1.0 - none_acc)
    if fallback and J > 0:
        out += none_acc * Jc / J
    return out


def ceiling_item(item: Item, check: str, fallback: bool, tau: int = 90) -> float:
    A, B, J, Jc = check_counts(item, check, tau)
    if A + B > 0:
        return A / (A + B)
    return (Jc / J if J else 0.0) if fallback else 0.0


def agreement_components(item: Item) -> tuple[float, float]:
    """Unbiased estimates of P(correct and confirmed) and P(wrong and confirmed) for the agreement check.

    A candidate is confirmed when one further independent attempt gives the same parsed answer;
    the estimates use pairs of distinct observed attempts.
    """
    m = item.m
    counts = Counter(a for a, _ in item.attempts if a is not None)
    pairs = m * (m - 1)
    tp = counts.get(item.answer, 0) * (counts.get(item.answer, 0) - 1) / pairs
    fp = sum(c * (c - 1) for y, c in counts.items() if y != item.answer) / pairs
    return tp, fp


def reliability_agreement_item(item: Item, n: int, fallback: bool) -> float:
    """n candidate-confirmation pairs (2n generations); plug-in in the acceptance components."""
    tp, fp = agreement_components(item)
    a = tp + fp
    p = item.p_hat()
    if a <= 0:
        return p if fallback else 0.0
    r = 1.0 - a
    out = tp / a * (1.0 - r ** n)
    if fallback and r > 0:
        out += r ** n * (p - tp) / r
    return out


def _vote_outcome(answers, correct_answer) -> float:
    """Expected correctness of a plurality vote with uniform tie-breaking; unparsed answers abstain."""
    c = Counter(a for a in answers if a is not None)
    if not c:
        return 0.0
    top = max(c.values())
    winners = [y for y, v in c.items() if v == top]
    return (1.0 / len(winners)) if correct_answer in winners else 0.0


def reliability_vote_item(item: Item, n: int, seed: int = 0, reps: int = 20000) -> float:
    """Exact U-statistic for n <= m; seeded Monte Carlo on the observed answer frequencies for n > m."""
    answers = [a for a, _ in item.attempts]
    m = item.m
    if n <= m:
        vals = [_vote_outcome([answers[i] for i in sub], item.answer) for sub in itertools.combinations(range(m), n)]
        return float(np.mean(vals))
    counts = Counter(answers)
    q = {y: c / m for y, c in counts.items()}
    return vote_plugin_mc(q, item.answer, n, seed, reps)


def vote_plugin_mc(q: dict, correct, n: int, seed: int, reps: int = 20000) -> float:
    """Plurality-vote accuracy for n draws from categorical q by seeded simulation (None abstains)."""
    keys = list(q)
    probs = np.array([q[k] for k in keys], float)
    if correct not in q:
        return 0.0
    if len([k for k in keys if k is not None]) == 1:
        return 1.0
    rng = np.random.default_rng([seed, n])
    counts = rng.multinomial(n, probs / probs.sum(), size=reps)
    voting = np.array([k is not None for k in keys])
    vc = np.where(voting, counts, -1)
    top = vc.max(axis=1, keepdims=True)
    is_top = (vc == top) & (top > 0)
    ci = keys.index(correct)
    wins = np.where(is_top[:, ci], 1.0 / is_top.sum(axis=1), 0.0)
    return float(wins.mean())


def vote_plugin(q: dict, correct, n: int) -> float:
    """Exact plurality-vote accuracy for n draws from categorical q (key None abstains; ties uniform)."""
    pc = q.get(correct, 0.0)
    others = [v for y, v in q.items() if y != correct and y is not None and v > 0]
    pnone = q.get(None, 0.0)
    if pc <= 0:
        return 0.0
    total = 0.0
    for c in range(1, n + 1):
        rest = n - c
        # P(N_correct = c) and conditional distribution of the remaining draws over others and None
        log_pc = math.lgamma(n + 1) - math.lgamma(c + 1) - math.lgamma(rest + 1) + c * math.log(pc)
        denom = 1.0 - pc
        if rest > 0 and denom <= 0:
            continue
        log_pc += rest * math.log(denom) if rest > 0 else 0.0
        if rest == 0:
            total += math.exp(log_pc)
            continue
        probs = [v / denom for v in others]
        pn = pnone / denom
        # dp[k][t]: sum over assignments of k draws to processed categories (each <= c), t ties at c,
        # of prod (prob^cnt / cnt!)
        dp = np.zeros((rest + 1, len(probs) + 1))
        dp[0, 0] = 1.0
        for pr in probs:
            new = np.zeros_like(dp)
            for k in range(rest + 1):
                for t in range(len(probs) + 1):
                    if dp[k, t] == 0.0:
                        continue
                    for cnt in range(0, min(c, rest - k) + 1):
                        w = dp[k, t] * (pr ** cnt) / math.factorial(cnt)
                        if cnt == c:
                            new[k + cnt, t + 1] += w
                        else:
                            new[k + cnt, t] += w
            dp = new
        cond = 0.0
        for k in range(rest + 1):
            none_cnt = rest - k
            wn = (pn ** none_cnt) / math.factorial(none_cnt) if (pn > 0 or none_cnt == 0) else 0.0
            for t in range(len(probs) + 1):
                cond += dp[k, t] * wn / (1 + t)
        cond *= math.factorial(rest)
        total += math.exp(log_pc) * cond
    return float(total)


def reliability_oracle_item(item: Item, n: int) -> float:
    m, c = item.m, sum(item.correct())
    if n <= m:
        return 1.0 - (math.comb(m - c, n) / math.comb(m, n) if n <= m - c else 0.0)
    return 1.0 - (1.0 - c / m) ** n


def icc_anova(phat: np.ndarray, m: int) -> float:
    """ANOVA estimator of the intraclass correlation of binary outcomes with equal cluster size m."""
    N = len(phat)
    pbar = phat.mean()
    msb = m * np.sum((phat - pbar) ** 2) / (N - 1)
    msw = np.sum(m * phat * (1 - phat)) / (N * (m - 1))
    return float((msb - msw) / (msb + (m - 1) * msw))


def sens_far(items: list[Item], check: str, tau: int = 90) -> tuple[float, float]:
    """Attempt-level sensitivity and false-acceptance rate pooled over items."""
    tp = fn = fp = tn = 0
    for it in items:
        for acc, ok, (ans, _) in zip(accept_vector(it, check, tau), it.correct(), it.attempts):
            if ok:
                tp += acc
                fn += not acc
            else:
                fp += acc
                tn += not acc
    s = tp / (tp + fn) if tp + fn else float("nan")
    f = fp / (fp + tn) if fp + tn else float("nan")
    return s, f
