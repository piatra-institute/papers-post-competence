"""Exact checks of reference-answer corrections listed in key_corrections.json."""
from __future__ import annotations

import json
from fractions import Fraction
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def test_h09_sum_is_minus_2009():
    x = [Fraction(2009)]
    running = Fraction(2009)
    for n in range(1, 2010):
        xn = Fraction(-2009, n) * running
        x.append(xn)
        running += xn
    assert x[1] == -2009 ** 2
    assert all(x[n] == (-1) ** n * 2009 * comb(2009, n) for n in (0, 1, 2, 3, 1000, 2009))
    total = sum((2 ** n) * x[n] for n in range(2010))
    assert total == -2009
    corr = {c["item_id"]: c for c in json.loads((HERE / "key_corrections.json").read_text())["corrections"]}
    assert corr["h09"]["corrected_answer"] == total


def test_h07_reference_is_consistent():
    # 1/(x-1) + 1/(y-1) + 1/(z-1) = 1 gives xyz - 2(xy+yz+zx) + 3(x+y+z) - 4 = 0
    e1, e2 = 2010, 67
    assert 2 * e2 - 3 * e1 + 4 == -5892
