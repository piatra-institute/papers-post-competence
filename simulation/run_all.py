"""Recorded analysis: theory illustrations and the reliability study on frozen model outputs.

Reads only frozen inputs (data/items.json and data/llm/*.jsonl with their manifests), recomputes
every reported quantity, writes output/results.json and the two figures, and runs no model.

Usage: uv run python run_all.py
"""
from __future__ import annotations

import hashlib
import itertools
import json
import re
import math
import platform
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from pc import estimators as est  # noqa: E402
from pc import theory as th  # noqa: E402
from pc.grading import parse_answer, parse_confidence, parse_verdict  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "output"
FIG = HERE.parent / "paper" / "figures"

N_ITEMS = 40
ATTEMPTS = 6
TAU = 90  # confidence threshold, fixed before analysis
TARGETS = (0.80, 0.90, 0.95)
AVAILABILITY_PROBES = 2  # two one-word calls that checked a model identifier was available; not stored
N_MAX = 1024
BOOT = 2000
SEED = 20261121
GEN_TAG = "gen__claude-haiku-5-5__low"
CHECKS = {"self": f"check__claude-haiku-5-5__low__on__{GEN_TAG}",
          "strong": f"check__claude-sonnet-5-5__low__on__{GEN_TAG}"}
PROTOCOLS = ("first", "vote", "confidence", "agreement", "self", "strong", "oracle")
# revision round 1: per-attempt verdicts on repeated wrong attempts, robustness set, recall cues
CHECKWRONG = {"self": f"checkwrong__claude-haiku-5-5__low__on__{GEN_TAG}",
              "strong": f"checkwrong__claude-sonnet-5-5__low__on__{GEN_TAG}"}
ROBUST_GEN = "gen__claude-haiku-5-5__low__robust"
ROBUST_CHECKS = {"self": f"check__claude-haiku-5-5__low__on__{ROBUST_GEN}",
                 "strong": f"check__claude-sonnet-5-5__low__on__{ROBUST_GEN}"}
N_ROBUST = 25
CUE = re.compile(r"\b(recall|recalled|remember|remembered|recollection|known answer|well[- ]known|official answer|"
                 r"official solution|answer key|HMMT|OEIS|memori[sz]ed|IMO|Putnam|shortlist)\b", re.IGNORECASE)
LABELS = {"first": "Accept first output", "vote": "Plurality vote", "confidence": "Stated confidence $\\geq$ 90",
          "agreement": "Agreement of two samples", "self": "Self-check (same model)",
          "strong": "Stronger-model check", "oracle": "Oracle check"}
SHORT = {"first": "Accept first", "vote": "Plurality vote", "confidence": "Confidence $\\geq$ 90",
         "agreement": "Agreement", "self": "Self-check", "strong": "Stronger model", "oracle": "Oracle"}
COLORS = {"first": "#7f7f7f", "vote": "#9467bd", "confidence": "#e6a100", "agreement": "#8c564b",
          "self": "#d62728", "strong": "#1f77b4", "oracle": "#2ca02c"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def result_of(rec: dict) -> dict:
    return json.loads(rec["stdout"])


def usage_of(rec: dict) -> dict:
    o = result_of(rec)
    mu = next(iter(o.get("modelUsage", {}).values()))
    return {"output_tokens": mu.get("outputTokens", 0), "thinking_tokens": mu.get("thinkingTokens", 0),
            "cost_usd": o.get("total_cost_usd", 0.0), "model": next(iter(o.get("modelUsage", {})))}


def load():
    meta_items = json.loads((DATA / "items.json").read_text())
    items_raw = [dict(it) for it in meta_items["items"][:N_ITEMS]]
    corrections = {c["item_id"]: c for c in json.loads((HERE / "key_corrections.json").read_text())["corrections"]}
    for it in items_raw:
        it["original_answer"] = it["answer"]
        if it["item_id"] in corrections:
            it["answer"] = corrections[it["item_id"]]["corrected_answer"]
    gens = read_jsonl(DATA / "llm" / f"{GEN_TAG}.jsonl")
    gen_manifest = json.loads((DATA / "llm" / f"{GEN_TAG}.manifest.json").read_text())
    checks = {k: read_jsonl(DATA / "llm" / f"{v}.jsonl") for k, v in CHECKS.items()}
    check_manifests = {k: json.loads((DATA / "llm" / f"{v}.manifest.json").read_text()) for k, v in CHECKS.items()}
    by_item = {it["item_id"]: [] for it in items_raw}
    usage = {"gen": [], "self": [], "strong": []}
    models = Counter()
    for r in sorted(gens, key=lambda r: (r["item_id"], r["attempt_index"])):
        text = result_of(r).get("result", "")
        by_item[r["item_id"]].append((parse_answer(text), parse_confidence(text)))
        u = usage_of(r)
        usage["gen"].append(u)
        models[u["model"]] += 1
    verdicts = {k: {} for k in CHECKS}
    unparsed_verdicts = Counter()
    for k, recs in checks.items():
        for r in recs:
            v = parse_verdict(result_of(r).get("result", ""))
            if v is None:
                unparsed_verdicts[k] += 1
            verdicts[k].setdefault(r["item_id"], {})[r["candidate_answer"]] = bool(v)
            u = usage_of(r)
            usage[k].append(u)
            models[u["model"]] += 1
    items = [est.Item(it["item_id"], it["answer"], by_item[it["item_id"]],
                      {k: verdicts[k].get(it["item_id"], {}) for k in CHECKS}) for it in items_raw]
    assert all(it.m == ATTEMPTS for it in items)
    return items, items_raw, meta_items["meta"], gen_manifest, check_manifests, usage, models, unparsed_verdicts


# ---------------------------------------------------------------- per-item curves

def item_curve(it: est.Item, proto: str, ns) -> np.ndarray:
    if proto == "first":
        return np.full(len(ns), it.p_hat())
    if proto == "oracle":
        return np.array([est.reliability_oracle_item(it, n) for n in ns])
    if proto == "vote":
        seed = SEED + int(it.item_id[1:])
        return np.array([est.reliability_vote_item(it, n, seed=seed) for n in ns])
    if proto == "agreement":
        return np.array([est.reliability_agreement_generations(it, n) for n in ns])
    return np.array([est.reliability_check_item(it, proto, n, fallback=True, tau=TAU) for n in ns])


def item_limit(it: est.Item, proto: str) -> float:
    if proto == "first":
        return it.p_hat()
    if proto == "oracle":
        return 1.0 if sum(it.correct()) > 0 else 0.0
    if proto == "vote":
        c = Counter(a for a, _ in it.attempts if a is not None)
        if not c or it.answer not in c:
            return 0.0
        top = max(c.values())
        winners = [y for y, v in c.items() if v == top]
        return 1.0 / len(winners) if it.answer in winners else 0.0
    if proto == "agreement":
        tp, fp = est.agreement_components(it)
        return tp / (tp + fp) if tp + fp > 0 else it.p_hat()
    return est.ceiling_item(it, proto, fallback=True, tau=TAU)


def pooled_precision(items, proto):
    if proto == "agreement":
        tp = sum(est.agreement_components(it)[0] for it in items)
        fp = sum(est.agreement_components(it)[1] for it in items)
        return tp / (tp + fp)
    A = sum(est.check_counts(it, proto, TAU)[0] for it in items)
    B = sum(est.check_counts(it, proto, TAU)[1] for it in items)
    return A / (A + B)


def sens_far(items, proto):
    if proto == "agreement":
        num_s = sum(est.agreement_components(it)[0] for it in items)
        den_s = sum(it.p_hat() for it in items)
        num_f = sum(est.agreement_components(it)[1] for it in items)
        den_f = sum(1 - it.p_hat() for it in items)
        return num_s / den_s, (num_f / den_f if den_f else float("nan"))
    return est.sens_far(items, proto, TAU)


def accept_rate_and_precision(it, proto):
    """Per-item acceptance rate a_i and precision pi_i (0 when nothing is accepted)."""
    if proto == "agreement":
        tp, fp = est.agreement_components(it)
        a = tp + fp
        return a, (tp / a if a > 0 else 0.0)
    A, B, J, _ = est.check_counts(it, proto, TAU)
    a = (A + B) / it.m
    return a, (A / (A + B) if A + B > 0 else 0.0)


def summarise(items, ns):
    curves = {p: np.mean([item_curve(it, p, ns) for it in items], axis=0) for p in PROTOCOLS}
    limits = {p: float(np.mean([item_limit(it, p) for it in items])) for p in PROTOCOLS}
    return curves, limits


def n_star_from_curve(curve, ns, rho):
    for n, v in zip(ns, curve):
        if v >= rho - 1e-12:
            return int(n)
    return None


def text_of(rec: dict) -> str:
    return result_of(rec).get("result", "") or ""


def has_cue(text: str) -> bool:
    return bool(CUE.search(text))


def load_set(items_file, n_items, gen_tag, check_tags):
    """Load a generation set and its candidate-level checks (used for the robustness set)."""
    raw_items = json.loads((DATA / items_file).read_text())
    items_raw = raw_items["items"][:n_items]
    gens = read_jsonl(DATA / "llm" / f"{gen_tag}.jsonl")
    by_item = {it["item_id"]: [] for it in items_raw}
    usage = {"gen": [usage_of(r) for r in gens]}
    for r in sorted(gens, key=lambda r: (r["item_id"], r["attempt_index"])):
        t = text_of(r)
        by_item[r["item_id"]].append((parse_answer(t), parse_confidence(t)))
    verdicts = {k: {} for k in check_tags}
    checks = {}
    for k, tag in check_tags.items():
        checks[k] = read_jsonl(DATA / "llm" / f"{tag}.jsonl")
        usage[k] = [usage_of(r) for r in checks[k]]
        for r in checks[k]:
            verdicts[k].setdefault(r["item_id"], {})[r["candidate_answer"]] = bool(parse_verdict(text_of(r)))
    items = [est.Item(it["item_id"], it["answer"], by_item[it["item_id"]],
                      {k: verdicts[k].get(it["item_id"], {}) for k in check_tags}) for it in items_raw]
    return items, raw_items["meta"], gens, checks, usage


def cue_summary(gens, checks, items):
    """Counts of explicit recall cues (CUE pattern) in generations and verdicts, and stronger-check outcomes
    on wrong candidates split by whether the verdict text contains a cue."""
    keyed = {it.item_id: it.answer for it in items}
    out = {"pattern": CUE.pattern, "gen_calls": len(gens), "gen_with_cue": sum(has_cue(text_of(r)) for r in gens)}
    for k, recs in checks.items():
        out[f"{k}_calls"] = len(recs)
        out[f"{k}_with_cue"] = sum(has_cue(text_of(r)) for r in recs)
        wrong = [r for r in recs if r["candidate_answer"] != keyed[r["item_id"]]]
        wc = [r for r in wrong if has_cue(text_of(r))]
        wn = [r for r in wrong if not has_cue(text_of(r))]
        out[f"{k}_wrong_candidates"] = len(wrong)
        out[f"{k}_wrong_with_cue"] = len(wc)
        out[f"{k}_wrong_with_cue_accepted"] = sum(bool(parse_verdict(text_of(r))) for r in wc)
        out[f"{k}_wrong_without_cue"] = len(wn)
        out[f"{k}_wrong_without_cue_accepted"] = sum(bool(parse_verdict(text_of(r))) for r in wn)
        right = [r for r in recs if r["candidate_answer"] == keyed[r["item_id"]]]
        out[f"{k}_correct_with_cue"] = sum(has_cue(text_of(r)) for r in right)
    out["gen_share_with_cue"] = out["gen_with_cue"] / max(1, out["gen_calls"])
    for k in checks:
        out[f"{k}_share_with_cue"] = out[f"{k}_with_cue"] / max(1, out[f"{k}_calls"])
    return out


def recall_label_summary(set_name, checks, items, labels):
    """Summaries of the hand classification (recall_labels.json) of verdicts matching the CUE pattern."""
    keyed = {it.item_id: it.answer for it in items}
    out = {}
    for k, recs in checks.items():
        rows = []
        for r in recs:
            key = f"{set_name}|{k}|{r['item_id']}|{r['candidate_answer']}"
            t = text_of(r)
            hit = has_cue(t)
            lab = labels.get(key, {}).get("label") if hit else None
            if hit and lab is None:
                raise SystemExit(f"unlabelled cue hit {key}")
            rows.append({"hit": hit, "label": lab, "correct": r["candidate_answer"] == keyed[r["item_id"]],
                         "accepted": bool(parse_verdict(t))})
        rem = [x for x in rows if x["label"] == "remembered_answer"]
        wrong = [x for x in rows if not x["correct"]]
        out[k] = {"calls": len(rows), "pattern_hits": sum(x["hit"] for x in rows),
                  "remembered_answer": len(rem), "related": sum(x["label"] == "related" for x in rows),
                  "no_recall": sum(x["label"] == "no_recall" for x in rows),
                  "remembered_share": len(rem) / len(rows),
                  "wrong_candidates": len(wrong),
                  "wrong_remembered": sum(x["label"] == "remembered_answer" for x in wrong),
                  "wrong_remembered_accepted": sum(x["label"] == "remembered_answer" and x["accepted"] for x in wrong),
                  "wrong_other": sum(x["label"] != "remembered_answer" for x in wrong),
                  "wrong_other_accepted": sum(x["label"] != "remembered_answer" and x["accepted"] for x in wrong),
                  "remembered_verdicts_against_key": sum(x["accepted"] != x["correct"] for x in rem)}
    return out


def per_attempt_check(items, gens, checks, checkwrong):
    """False acceptance and limits when every wrong attempt is judged with its own solution text.

    Wrong attempts that were the first with their answer were judged in the main check; the others were
    judged in the revision collection (checkwrong). Correct attempts keep the cached candidate verdict."""
    out = {}
    for k in checks:
        first_seen = {}
        for r in sorted(gens, key=lambda r: (r["item_id"], r["attempt_index"])):
            a = parse_answer(text_of(r))
            if a is not None and (r["item_id"], a) not in first_seen:
                first_seen[(r["item_id"], a)] = r["attempt_index"]
        own = {}
        for r in checks[k]:
            own[(r["item_id"], first_seen[(r["item_id"], r["candidate_answer"])])] = bool(parse_verdict(text_of(r)))
        extra = {(r["item_id"], r["attempt_index"]): bool(parse_verdict(text_of(r))) for r in checkwrong[k]}
        n_wrong = acc_wrong = n_repeat = repeat_agree = 0
        lim = []
        for it in items:
            A = B = J = Jc = 0
            for j, ((a, _), ok) in enumerate(zip(it.attempts, it.correct())):
                cached = bool(it.verdicts[k].get(a, False)) if a is not None else False
                if ok:
                    v = cached
                else:
                    if (it.item_id, j) in extra:
                        v = extra[(it.item_id, j)]
                        n_repeat += 1
                        repeat_agree += v == cached
                    else:
                        v = own.get((it.item_id, j), cached)
                    n_wrong += 1
                    acc_wrong += v
                A += v and ok
                B += v and not ok
                J += not v
                Jc += (not v) and ok
            lim.append(A / (A + B) if A + B else (Jc / J if J else 0.0))
        out[k] = {"wrong_attempts": n_wrong, "wrong_accepted": acc_wrong, "false_acceptance": acc_wrong / n_wrong,
                  "repeated_wrong_attempts_rejudged": n_repeat, "rejudged_agree_with_cached": repeat_agree,
                  "limit_fallback": float(np.mean(lim))}
    return out


def analyse_set(items, ns, rng, boot):
    """Compact analysis of an item set with the same protocols (used for the robustness set)."""
    N = len(items)
    phat = np.array([it.p_hat() for it in items])
    pic = {p: np.array([item_curve(it, p, ns) for it in items]) for p in PROTOCOLS}
    pil = {p: np.array([item_limit(it, p) for it in items]) for p in PROTOCOLS}
    curves = {p: pic[p].mean(axis=0) for p in PROTOCOLS}
    res = {"n_items": N, "mean_p": float(phat.mean()), "icc": est.icc_anova(phat, ATTEMPTS),
           "items_by_correct_count": {str(k): int(np.sum(np.round(phat * ATTEMPTS) == k)) for k in range(ATTEMPTS + 1)},
           "n_never": int(np.sum(phat == 0)), "n_always": int(np.sum(phat == 1)),
           "n_wrong_attempts": int(round(sum((1 - phat) * ATTEMPTS)))}
    res["share_wrong_on_never"] = (res["n_never"] * ATTEMPTS) / res["n_wrong_attempts"] if res["n_wrong_attempts"] else None
    checks = {}
    for c in ("confidence", "agreement", "self", "strong"):
        s_, f_ = sens_far(items, c)
        a_pi = [accept_rate_and_precision(it, c) for it in items]
        checks[c] = {"sensitivity": s_, "false_acceptance": f_, "likelihood_ratio": (s_ / f_) if f_ else None,
                     "pooled_precision": pooled_precision(items, c),
                     "ceiling_abstain": float(np.mean([x[1] for x in a_pi]))}
    prot = {}
    for p in PROTOCOLS:
        prot[p] = {"limit": float(pil[p].mean()), "reliability_6": float(curves[p][int(np.where(ns == 6)[0][0])]),
                   "n_star": {f"{rho:.2f}": n_star_from_curve(curves[p], ns, rho) for rho in TARGETS}}
    bs = {"mean_p": [], "icc": []}
    bl = {p: [] for p in PROTOCOLS}
    bc = {c: {"s": [], "f": []} for c in ("self", "strong")}
    for _ in range(boot):
        idx = rng.integers(0, N, N)
        sub = [items[i] for i in idx]
        bs["mean_p"].append(phat[idx].mean())
        bs["icc"].append(est.icc_anova(phat[idx], ATTEMPTS) if phat[idx].std() > 0 else float("nan"))
        for p in PROTOCOLS:
            bl[p].append(pil[p][idx].mean())
        for c in bc:
            s_, f_ = sens_far(sub, c)
            bc[c]["s"].append(s_)
            bc[c]["f"].append(f_)

    def ci(x):
        x = np.asarray(x, float)
        x = x[~np.isnan(x)]
        return [float(np.quantile(x, 0.025)), float(np.quantile(x, 0.975))]

    res["mean_p_ci95"] = ci(bs["mean_p"])
    res["icc_ci95"] = ci(bs["icc"])
    for p in PROTOCOLS:
        prot[p]["limit_ci95"] = ci(bl[p])
    for c in bc:
        checks[c]["sensitivity_ci95"] = ci(bc[c]["s"])
        checks[c]["false_acceptance_ci95"] = ci(bc[c]["f"])
    paired = {}
    for a_, b_ in (("oracle", "self"), ("oracle", "strong"), ("self", "first"), ("strong", "self"), ("oracle", "first"),
                   ("oracle", "vote")):
        d = pil[a_] - pil[b_]
        paired[f"{a_}_minus_{b_}"] = {"diff": float(d.mean()), "ci95": ci([d[rng.integers(0, N, N)].mean() for _ in range(boot)]),
                                      "items_differing": int(np.sum(np.abs(d) > 1e-12))}
    res["checks"] = checks
    res["protocols"] = prot
    res["paired_limit_differences"] = paired
    res["share_of_oracle_gain_recovered"] = {p: ((prot[p]["limit"] - prot["first"]["limit"]) / (prot["oracle"]["limit"] - prot["first"]["limit"])
                                                 if prot["oracle"]["limit"] > prot["first"]["limit"] else None) for p in PROTOCOLS}
    # never-solved items on which the stronger check accepted some model answer (key or checker in question)
    res["never_items_with_strong_acceptance"] = int(sum(1 for it in items if it.p_hat() == 0 and any(it.verdicts["strong"].values())))
    res["never_items_with_self_acceptance"] = int(sum(1 for it in items if it.p_hat() == 0 and any(it.verdicts["self"].values())))
    res["n_candidates"] = int(sum(len(it.verdicts["self"]) for it in items))
    return res, curves


def main() -> None:
    OUT.mkdir(exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    items, items_raw, items_meta, gen_manifest, check_manifests, usage, models, unparsed_verdicts = load()
    rng = np.random.default_rng(SEED)
    N = len(items)
    ns = np.unique(np.concatenate([np.arange(1, 33), 2 ** np.arange(5, 11), np.round(np.logspace(np.log10(33), np.log10(N_MAX), 40))]).astype(int))

    # ----------------------------------------------------------- population of items
    phat = np.array([it.p_hat() for it in items])
    k_correct = Counter(int(round(p * ATTEMPTS)) for p in phat)
    unparsed = sum(a is None for it in items for a, _ in it.attempts)
    no_conf = sum(c is None for it in items for _, c in it.attempts)
    wrong_attempts = [(it, a) for it in items for (a, _), ok in zip(it.attempts, it.correct()) if not ok]
    n_wrong = len(wrong_attempts)
    distinct_wrong = len({(it.item_id, a) for it, a in wrong_attempts})
    icc = est.icc_anova(phat, ATTEMPTS)
    mixed = [it for it in items if 0 < it.p_hat() < 1]
    never = [it for it in items if it.p_hat() == 0]
    always = [it for it in items if it.p_hat() == 1]
    # wrong answers on items never solved: how concentrated
    never_modal_share = []
    for it in never:
        c = Counter(a for a, _ in it.attempts)
        never_modal_share.append(max(c.values()) / it.m)
    never_detail = []
    for it in never:
        c = Counter(a for a, _ in it.attempts)
        confs = [cf for _, cf in it.attempts if cf is not None]
        never_detail.append({"item_id": it.item_id, "distinct_answers": len(c), "modal_share": max(c.values()) / it.m,
                             "min_confidence": min(confs), "max_confidence": max(confs),
                             "self_accepts_modal": bool(it.verdicts["self"].get(c.most_common(1)[0][0], False)),
                             "strong_accepts_modal": bool(it.verdicts["strong"].get(c.most_common(1)[0][0], False))})
    pop = {"n_items": N, "attempts_per_item": ATTEMPTS, "n_attempts": N * ATTEMPTS,
           "mean_p": float(phat.mean()), "icc": icc,
           "items_by_correct_count": {str(k): k_correct.get(k, 0) for k in range(ATTEMPTS + 1)},
           "n_always": len(always), "n_never": len(never), "n_mixed": len(mixed),
           "share_always": len(always) / N, "share_never": len(never) / N, "share_mixed": len(mixed) / N,
           "n_wrong_attempts": n_wrong, "n_distinct_wrong_candidates": distinct_wrong,
           "unparsed_answers": unparsed, "missing_confidence": no_conf,
           "never_items_modal_wrong_share_mean": float(np.mean(never_modal_share)) if never_modal_share else None,
           "error_share_on_never_items": (sum(1 - it.p_hat() for it in never) * ATTEMPTS) / n_wrong if n_wrong else None}

    # ----------------------------------------------------------- checks
    checks = {}
    for proto in ("confidence", "agreement", "self", "strong"):
        s, f = sens_far(items, proto)
        a_pi = [accept_rate_and_precision(it, proto) for it in items]
        a = np.array([x[0] for x in a_pi])
        pi = np.array([x[1] for x in a_pi])
        pooled = pooled_precision(items, proto)
        cov_gap = float(np.mean((a - a.mean()) * (pi - pi.mean())) / a.mean())
        abstain_ceiling = float(pi.mean())
        checks[proto] = {"sensitivity": s, "false_acceptance": f, "likelihood_ratio": (s / f) if f > 0 else None,
                         "pooled_precision": pooled, "ceiling_abstain": abstain_ceiling,
                         "ceiling_fallback": float(np.mean([item_limit(it, proto) for it in items])),
                         "pooled_minus_ceiling_abstain": pooled - abstain_ceiling,
                         "covariance_identity_value": cov_gap,
                         "items_with_no_accepted_attempt": int(np.sum(a == 0)),
                         "single_attempt_precision_formula": th.ceiling(float(phat.mean()), s, f)}
    # distinct-candidate counts for model checks, and modal-vs-nonmodal false acceptance
    cand = {}
    for proto in ("self", "strong"):
        fa_modal, fa_other, n_modal, n_other = 0, 0, 0, 0
        for it in items:
            c = Counter(a for a, _ in it.attempts if a is not None and a != it.answer)
            if not c:
                continue
            top = max(c.values())
            for y, cnt in c.items():
                v = it.verdicts[proto].get(y, False)
                if cnt == top and cnt >= 2:
                    fa_modal += v
                    n_modal += 1
                else:
                    fa_other += v
                    n_other += 1
        n_cands = sum(len(it.verdicts[proto]) for it in items)
        n_wrong_cands = sum(1 for it in items for y in it.verdicts[proto] if y != it.answer)
        acc_wrong = sum(1 for it in items for y, v in it.verdicts[proto].items() if y != it.answer and v)
        n_right_cands = n_cands - n_wrong_cands
        acc_right = sum(1 for it in items for y, v in it.verdicts[proto].items() if y == it.answer and v)
        cand[proto] = {"n_candidates": n_cands, "n_wrong_candidates": n_wrong_cands,
                       "wrong_candidates_accepted": acc_wrong, "n_correct_candidates": n_right_cands,
                       "correct_candidates_accepted": acc_right,
                       "repeated_modal_wrong_candidates": n_modal, "repeated_modal_wrong_accepted": fa_modal,
                       "other_wrong_candidates": n_other, "other_wrong_accepted": fa_other}
    from scipy.stats import fisher_exact
    for proto in ("self", "strong"):
        cc = cand[proto]
        table = [[cc["repeated_modal_wrong_accepted"], cc["repeated_modal_wrong_candidates"] - cc["repeated_modal_wrong_accepted"]],
                 [cc["other_wrong_accepted"], cc["other_wrong_candidates"] - cc["other_wrong_accepted"]]]
        cc["fisher_one_sided_p_modal_more_accepted"] = float(fisher_exact(table, alternative="greater")[1])
        cc["candidate_level_false_acceptance"] = cc["wrong_candidates_accepted"] / cc["n_wrong_candidates"]
    # paired comparison of the two model checks on wrong candidates
    both = [(it.verdicts["self"].get(y, False), it.verdicts["strong"].get(y, False))
            for it in items for y in it.verdicts["self"] if y != it.answer]
    paired = {"wrong_candidates": len(both),
              "accepted_by_both": sum(a and b for a, b in both),
              "accepted_by_self_only": sum(a and not b for a, b in both),
              "accepted_by_strong_only": sum(b and not a for a, b in both),
              "rejected_by_both": sum((not a) and (not b) for a, b in both)}
    # confidence as a continuous score: ROC points and AUROC
    confs = [(c if c is not None else -1, ok) for it in items for (a, c), ok in zip(it.attempts, it.correct())]
    pos = np.array([c for c, ok in confs if ok], float)
    neg = np.array([c for c, ok in confs if not ok], float)
    auroc = float(np.mean([(1.0 if x > y else 0.5 if x == y else 0.0) for x in pos for y in neg])) if len(neg) else None
    thresholds = sorted({c for c, _ in confs})
    roc = [{"tau": t, "s": float(np.mean(pos >= t)), "f": float(np.mean(neg >= t)) if len(neg) else None} for t in thresholds]

    # ----------------------------------------------------------- curves, limits, bootstrap
    curves, limits = summarise(items, ns)
    boot_curves = {p: [] for p in PROTOCOLS}
    boot_limits = {p: [] for p in PROTOCOLS}
    boot_scalar = {"mean_p": [], "icc": []}
    boot_checks = {c: {"s": [], "f": [], "pooled": [], "ceiling_abstain": []} for c in checks}
    per_item_curves = {p: np.array([item_curve(it, p, ns) for it in items]) for p in PROTOCOLS}
    per_item_limits = {p: np.array([item_limit(it, p) for it in items]) for p in PROTOCOLS}
    for _ in range(BOOT):
        idx = rng.integers(0, N, N)
        sub = [items[i] for i in idx]
        for p in PROTOCOLS:
            boot_curves[p].append(per_item_curves[p][idx].mean(axis=0))
            boot_limits[p].append(per_item_limits[p][idx].mean())
        ph = phat[idx]
        boot_scalar["mean_p"].append(ph.mean())
        boot_scalar["icc"].append(est.icc_anova(ph, ATTEMPTS) if ph.std() > 0 else float("nan"))
        for c in checks:
            s, f = sens_far(sub, c)
            boot_checks[c]["s"].append(s)
            boot_checks[c]["f"].append(f)
            boot_checks[c]["pooled"].append(pooled_precision(sub, c))
            boot_checks[c]["ceiling_abstain"].append(np.mean([accept_rate_and_precision(it, c)[1] for it in sub]))

    def ci(x):
        x = np.asarray(x, float)
        x = x[~np.isnan(x)]
        return [float(np.quantile(x, 0.025)), float(np.quantile(x, 0.975))]

    pop["mean_p_ci95"] = ci(boot_scalar["mean_p"])
    pop["icc_ci95"] = ci(boot_scalar["icc"])
    for c in checks:
        checks[c]["sensitivity_ci95"] = ci(boot_checks[c]["s"])
        checks[c]["false_acceptance_ci95"] = ci(boot_checks[c]["f"])
        checks[c]["pooled_precision_ci95"] = ci(boot_checks[c]["pooled"])
        checks[c]["ceiling_abstain_ci95"] = ci(boot_checks[c]["ceiling_abstain"])
        gaps = np.array(boot_checks[c]["pooled"]) - np.array(boot_checks[c]["ceiling_abstain"])
        checks[c]["pooled_minus_ceiling_abstain_ci95"] = ci(gaps)

    def at(n):
        return int(np.where(ns == n)[0][0])

    protocols = {}
    for p in PROTOCOLS:
        bc = np.array(boot_curves[p])
        protocols[p] = {
            "reliability": {str(n): float(curves[p][at(n)]) for n in (1, 2, 3, 6, 16, 64, 256, 1024)},
            "reliability_ci95": {str(n): ci(bc[:, at(n)]) for n in (1, 6, 64, 1024)},
            "limit": limits[p], "limit_ci95": ci(boot_limits[p]),
            "n_star": {f"{rho:.2f}": n_star_from_curve(curves[p], ns, rho) for rho in TARGETS},
            "items_limit_at_least": {f"{rho:.2f}": int(np.sum(per_item_limits[p] >= rho - 1e-12)) for rho in TARGETS},
        }
    gap_oracle_minus = {p: limits["oracle"] - limits[p] for p in PROTOCOLS}
    pairs = [("oracle", "self"), ("oracle", "strong"), ("oracle", "vote"), ("oracle", "agreement"), ("oracle", "confidence"),
             ("strong", "self"), ("self", "first"), ("vote", "self"), ("oracle", "first")]
    paired_limits = {}
    for a_, b_ in pairs:
        d = per_item_limits[a_] - per_item_limits[b_]
        bs = [d[rng.integers(0, N, N)].mean() for _ in range(BOOT)]
        paired_limits[f"{a_}_minus_{b_}"] = {"diff": float(d.mean()), "ci95": ci(bs),
                                            "items_differing": int(np.sum(np.abs(d) > 1e-12))}
    recovered = {p: (limits[p] - limits["first"]) / (limits["oracle"] - limits["first"]) for p in PROTOCOLS}
    # sensitivity: the same analysis with the original (uncorrected) reference answers
    orig_items = [est.Item(it.item_id, raw["original_answer"], it.attempts, it.verdicts) for it, raw in zip(items, items_raw)]
    orig_curves, orig_limits = summarise(orig_items, ns)
    original_key = {"n_corrected": sum(raw["original_answer"] != raw["answer"] for raw in items_raw),
                    "limit_drop": {p: limits[p] - orig_limits[p] for p in PROTOCOLS},
                    "mean_p": float(np.mean([it.p_hat() for it in orig_items])),
                    "n_never": sum(it.p_hat() == 0 for it in orig_items), "limits": orig_limits,
                    "checks": {c: dict(zip(("sensitivity", "false_acceptance"), sens_far(orig_items, c))) for c in checks}}

    # ----------------------------------------------------------- compute
    def mean_of(xs, key):
        return float(np.mean([x[key] for x in xs])) if xs else None

    compute = {k: {"calls": len(v), "mean_output_tokens": mean_of(v, "output_tokens"),
                   "mean_thinking_tokens": mean_of(v, "thinking_tokens"), "mean_cost_usd": mean_of(v, "cost_usd"),
                   "total_cost_usd": float(sum(x["cost_usd"] for x in v))} for k, v in usage.items()}
    pilot_calls = 0
    for mf in (DATA / "pilot").glob("*.manifest.json"):
        pilot_calls += json.loads(mf.read_text())["n_prompts"]
    compute["pilot_calls"] = pilot_calls
    compute["availability_probes"] = AVAILABILITY_PROBES
    compute["analysed_calls"] = sum(len(v) for v in usage.values())
    compute["total_calls_including_pilot_and_probes"] = compute["analysed_calls"] + pilot_calls + AVAILABILITY_PROBES
    compute["total_cost_usd_analysed"] = float(sum(x["cost_usd"] for v in usage.values() for x in v))
    compute["strong_check_to_attempt_cost_ratio"] = compute["strong"]["mean_cost_usd"] / compute["gen"]["mean_cost_usd"]
    compute["self_check_to_attempt_cost_ratio"] = compute["self"]["mean_cost_usd"] / compute["gen"]["mean_cost_usd"]
    # pilot outcomes (not analysed elsewhere)
    pilot = {}
    keys = {"math500": {it["item_id"]: it["answer"] for it in json.loads((DATA / "pilot" / "math500_items.json").read_text())["items"]},
            "omni": {it["item_id"]: it["answer"] for it in json.loads((DATA / "items.json").read_text())["items"]}}
    for jf in sorted((DATA / "pilot").glob("*__gen__*.jsonl")):
        bench = jf.name.split("__")[0]
        recs = read_jsonl(jf)
        ok = sum(parse_answer(result_of(r).get("result", "")) == keys[bench][r["item_id"]] for r in recs)
        pilot[jf.stem] = {"attempts": len(recs), "correct": int(ok), "model": recs[0]["model"]}
    pilot_math500 = {"attempts": sum(v["attempts"] for k, v in pilot.items() if k.startswith("math500")),
                     "correct": sum(v["correct"] for k, v in pilot.items() if k.startswith("math500"))}

    # ----------------------------------------------------------- theory illustrations
    ex = {"p": 0.4, "s": 0.9, "f": 0.15}
    ex_pi = th.ceiling(ex["p"], ex["s"], ex["f"])
    theory = {"example": {**ex, "ceiling": ex_pi, "likelihood_ratio": ex["s"] / ex["f"],
                          "n_star_0.75": th.n_star_fallback(0.75, **ex), "n_star_0.79": th.n_star_fallback(0.79, **ex),
                          "acceptance": th.acceptance(ex["p"], ex["s"], ex["f"]),
                          "oracle_n_star_0.99": math.ceil(math.log(0.01) / math.log(1 - ex["p"])),
                          "required_lr_0.99": th.required_likelihood_ratio(0.99, ex["p"]),
                          "required_lr_0.9": th.required_likelihood_ratio(0.9, ex["p"])},
              "icc_example": {"pbar": 0.6, "s": 0.9, "f": 0.2,
                              "ceiling_icc0": th.beta_population_ceiling(0.6, 0.0, 0.9, 0.2),
                              "ceiling_icc0.3": th.beta_population_ceiling(0.6, 0.3, 0.9, 0.2),
                              "ceiling_icc0.7": th.beta_population_ceiling(0.6, 0.7, 0.9, 0.2),
                              "ceiling_icc1": th.beta_population_ceiling(0.6, 1.0, 0.9, 0.2),
                              "second_order_icc0.3": th.jensen_second_order(0.6, 0.3 * 0.6 * 0.4, 0.9, 0.2)}}
    # measured checks plugged into the single-item formula at the measured mean p (what a pooled analysis predicts)
    # versus the plug-in Beta population with the measured ICC
    pbar, icc_hat = float(phat.mean()), max(0.0, min(0.999, icc))
    for c in ("self", "strong", "confidence", "agreement"):
        s, f = checks[c]["sensitivity"], checks[c]["false_acceptance"]
        checks[c]["beta_model_ceiling_at_measured_icc"] = th.beta_population_ceiling(pbar, icc_hat, s, f) if f > 0 else 1.0

    # ----------------------------------------------------------- revision round 1
    gens_main = read_jsonl(DATA / "llm" / f"{GEN_TAG}.jsonl")
    checks_main = {k: read_jsonl(DATA / "llm" / f"{v}.jsonl") for k, v in CHECKS.items()}
    checkwrong = {k: read_jsonl(DATA / "llm" / f"{v}.jsonl") for k, v in CHECKWRONG.items()}
    per_attempt = per_attempt_check(items, gens_main, checks_main, checkwrong)
    cues = cue_summary(gens_main, checks_main, items)
    cues["checkwrong_with_cue"] = {k: sum(has_cue(text_of(r)) for r in v) for k, v in checkwrong.items()}
    items_r, meta_r, gens_r, checks_r, usage_r = load_set("items_robust.json", N_ROBUST, ROBUST_GEN, ROBUST_CHECKS)
    robust, curves_r = analyse_set(items_r, ns, np.random.default_rng(SEED + 1), BOOT)
    robust["items_meta"] = meta_r
    robust["recall_cues"] = cue_summary(gens_r, checks_r, items_r)
    robust["compute"] = {k: {"calls": len(v), "mean_output_tokens": float(np.mean([x["output_tokens"] for x in v])),
                             "mean_cost_usd": float(np.mean([x["cost_usd"] for x in v]))} for k, v in usage_r.items()}
    labels = json.loads((HERE / "recall_labels.json").read_text())["labels"]
    recall_labels = {"main": recall_label_summary("main", checks_main, items, labels),
                     "robust": recall_label_summary("robust", checks_r, items_r, labels),
                     "n_labels": len(labels)}
    below = 0
    for it in items_r:
        A_, B_, J_, Jc_ = est.check_counts(it, "self", TAU)
        if A_ + B_ > 0 and A_ / (A_ + B_) < it.p_hat():
            below += 1
    robust["items_self_precision_below_p"] = below
    robust["sources"] = dict(Counter(json.loads((DATA / "items_robust.json").read_text())["items"][i]["source"] for i in range(N_ROBUST)))
    revision_calls = {"checkwrong": sum(len(v) for v in checkwrong.values()),
                      "robust": sum(len(v) for v in usage_r.values())}
    compute["revision_calls"] = revision_calls
    compute["total_calls_all_rounds"] = compute["total_calls_including_pilot_and_probes"] + sum(revision_calls.values())
    compute["agreement_generations_note"] = "agreement curves are indexed by generations: n generations allow floor(n/2) pairs"
    # F1: two task mixtures with the same mean show the ceiling is not a function of the ICC alone
    s_c, f_c = 0.9, 0.2
    mixA = [(0.0, 0.2), (0.625, 0.8)]
    mixB = [(0.2, 0.5), (0.8, 0.5)]

    def mix_stats(mix):
        m = sum(pp * w for pp, w in mix)
        var = sum(w * (pp - m) ** 2 for pp, w in mix)
        return {"mean": m, "icc": var / (m * (1 - m)), "ceiling": sum(w * th.ceiling(pp, s_c, f_c) for pp, w in mix)}
    theory_icc_counter = {"s": s_c, "f": f_c, "mixture_a": mix_stats(mixA), "mixture_b": mix_stats(mixB)}

    results = {"schema": "post-competence-results-1", "config": {
        "n_items": N_ITEMS, "attempts": ATTEMPTS, "tau": TAU, "targets": TARGETS, "n_max": N_MAX,
        "bootstrap": BOOT, "seed": SEED, "generator_tag": GEN_TAG, "check_tags": CHECKS},
        "data": {"items_meta": items_meta, "generator_manifest": {k: gen_manifest[k] for k in ("model", "cli", "effort", "flags", "finished_utc")},
                 "check_manifests": {k: {kk: v[kk] for kk in ("model", "cli", "effort", "finished_utc", "n_prompts")} for k, v in check_manifests.items()},
                 "models_reported_by_cli": dict(models), "unparsed_verdicts": dict(unparsed_verdicts),
                 "input_sha256": {p.name: sha256(p) for p in sorted((DATA / "llm").glob("*"))} | {"items.json": sha256(DATA / "items.json")}},
        "population": pop, "checks": checks, "candidates": cand, "paired_wrong_candidates": paired,
        "confidence_score": {"auroc": auroc, "roc": roc},
        "pilot": {"runs": pilot, "math500_total": pilot_math500},
        "per_attempt_wrong_verdicts": per_attempt, "recall_cues": cues, "recall_labels": recall_labels, "robust": robust,
        "theory_icc_counterexample": theory_icc_counter,
        "never_solved_items": never_detail,
        "protocols": protocols, "limit_gap_to_oracle": gap_oracle_minus, "paired_limit_differences": paired_limits,
        "share_of_oracle_gain_recovered": recovered, "original_key": original_key, "compute": compute, "theory": theory,
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "matplotlib": matplotlib.__version__,
                    "platform": platform.platform()}}
    (OUT / "results.json").write_text(json.dumps(results, indent=1, default=float))
    make_figures(results, ns, curves, boot_curves, items, roc)
    make_robust_figure(results["robust"], ns, curves_r)
    print(json.dumps({"mean_p": pop["mean_p"], "icc": icc, "limits": limits,
                      "checks": {c: [checks[c]["sensitivity"], checks[c]["false_acceptance"]] for c in checks}}, indent=1))


# ---------------------------------------------------------------- figures

def style():
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 9.5, "axes.labelsize": 9, "legend.fontsize": 7.5,
                         "xtick.labelsize": 8, "ytick.labelsize": 8, "font.family": "serif",
                         "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42})


def make_figures(results, ns, curves, boot_curves, items, roc):
    """Figures are drawn at the 6.5-inch text width, so font sizes are final print sizes."""
    style()
    # Figure 1: theory
    fig, ax = plt.subplots(2, 2, figsize=(6.5, 5.6))
    p, s, f = 0.4, 0.9, 0.15
    nn = np.arange(1, 31)
    a = ax[0, 0]
    series = [
        ([th.reliability_oracle(p, n) for n in nn], COLORS["oracle"], "-", "Oracle check"),
        ([th.reliability_check_fallback(p, s, f, n) for n in nn], COLORS["self"], "-", f"Check, $s={s}$, $f={f}$"),
        ([est.vote_plugin({1: 0.4, 2: 0.3, 3: 0.2, 4: 0.1}, 1, n) for n in nn], COLORS["vote"], "-", "Vote, right answer modal"),
        ([p] * len(nn), COLORS["first"], "-", "Accept first output"),
        ([est.vote_plugin({1: 0.4, 2: 0.45, 3: 0.15}, 1, n) for n in nn], COLORS["vote"], "--", "Vote, a wrong answer modal"),
    ]
    label_y = [0.935, 0.735, 0.555, 0.445, 0.285]
    for (ys, col, ls, lab), ly in zip(series, label_y):
        a.plot(nn, ys, color=col, ls=ls, lw=1.4)
        a.text(30, ly, lab, color=col, fontsize=7.5, ha="right", va="center")
    a.set(xlabel="Attempts $n$", ylabel="Reliability", ylim=(0, 1.04), title="(a) One item with $p = 0.4$")
    a = ax[0, 1]
    lr = np.logspace(0, 3, 300)
    for pp, ls in zip((0.1, 0.3, 0.5, 0.7), ("-", "--", "-.", ":")):
        odds = lr * pp / (1 - pp)
        a.plot(lr, odds / (1 + odds), color="k", ls=ls, lw=1.2, label=f"$p = {pp}$")
    a.axhline(0.9, color="#999999", lw=0.7)
    a.axhline(0.99, color="#999999", lw=0.7)
    a.text(1.08, 0.915, "$\\rho = 0.9$", fontsize=7.5, color="#444444", ha="left", va="bottom")
    a.text(1.08, 1.003, "$\\rho = 0.99$", fontsize=7.5, color="#444444", ha="left", va="bottom")
    a.set_xscale("log")
    a.set(xlabel="Likelihood ratio of the check, $s/f$", ylabel="Ceiling $\\pi$", ylim=(0, 1.09), title="(b) Ceiling against check quality")
    a.legend(loc="lower right", frameon=False, handlelength=2.2)
    a = ax[1, 0]
    iccs = np.linspace(0, 1, 101)
    a.plot(iccs, [th.beta_population_ceiling(0.6, c, 0.9, 0.2) for c in iccs], color=COLORS["self"], lw=1.4, label="Population ceiling")
    a.plot(iccs, [th.jensen_second_order(0.6, c * 0.24, 0.9, 0.2) for c in iccs], color=COLORS["self"], ls=":", lw=1.2, label="Second-order approximation")
    a.axhline(th.ceiling(0.6, 0.9, 0.2), color="k", lw=0.8, ls="--", label="Pooled formula $\\pi(\\bar p)$")
    a.axhline(0.6, color=COLORS["first"], lw=1, label="Single attempt $\\bar p$")
    a.set(xlabel="Intraclass correlation of attempt outcomes", ylabel="Limit of reliability", ylim=(0.3, 0.92),
          title="(c) Heterogeneous items")
    a.text(0.98, 0.315, "$\\bar p = 0.6$, $s = 0.9$, $f = 0.2$", fontsize=7.5, color="#444444", ha="right")
    a.legend(loc="lower left", frameon=False, bbox_to_anchor=(0.0, 0.07))
    a = ax[1, 1]
    pi = th.ceiling(p, s, f)
    rhos = np.unique(np.concatenate([np.linspace(0.05, pi - 0.01, 300), pi - np.logspace(-2, -7, 120)]))
    a.plot(rhos, [th.n_star_fallback(r, p, s, f) for r in rhos], color=COLORS["self"], lw=1.4, label="Check of panel (a)")
    ro = np.linspace(0.05, 0.9999, 400)
    a.plot(ro, [math.ceil(math.log(1 - r) / math.log(1 - p) - 1e-12) for r in ro], color=COLORS["oracle"], lw=1.4, label="Oracle check")
    a.axvline(pi, color=COLORS["self"], lw=0.7, ls=":")
    a.text(pi + 0.012, 1.05, "ceiling 0.8", rotation=90, fontsize=7.5, color=COLORS["self"], ha="left", va="bottom")
    a.set_yscale("log")
    a.set(xlabel="Target reliability $\\rho$", ylabel="Attempts needed $n^*(\\rho)$", title="(d) Attempts needed for a target")
    a.legend(loc="upper left", frameon=False)
    fig.tight_layout(h_pad=1.2, w_pad=1.0)
    fig.savefig(FIG / "theory.pdf")
    fig.savefig(OUT / "theory.pdf")
    plt.close(fig)

    # Figure 2: measurement
    fig, ax = plt.subplots(2, 2, figsize=(6.5, 5.9))
    a = ax[0, 0]
    counts = results["population"]["items_by_correct_count"]
    ks = list(range(ATTEMPTS + 1))
    a.bar(ks, [counts[str(k)] for k in ks], color="#555555", width=0.7)
    for k in ks:
        a.text(k, counts[str(k)] + 0.4, str(counts[str(k)]), ha="center", fontsize=7.5)
    a.set(xlabel=f"Correct attempts out of {ATTEMPTS}", ylabel="Items", title=f"(a) Per-item success, {len(items)} items")
    a.set_xticks(ks)
    a = ax[0, 1]
    rf = [r["f"] for r in roc]
    rs = [r["s"] for r in roc]
    a.plot(rf, rs, color=COLORS["confidence"], lw=1, alpha=0.8, label="Confidence, all thresholds")
    for c in ("confidence", "agreement", "self", "strong"):
        ch = results["checks"][c]
        xe = np.array([[ch["false_acceptance"] - ch["false_acceptance_ci95"][0]], [ch["false_acceptance_ci95"][1] - ch["false_acceptance"]]])
        ye = np.array([[ch["sensitivity"] - ch["sensitivity_ci95"][0]], [ch["sensitivity_ci95"][1] - ch["sensitivity"]]])
        a.errorbar([ch["false_acceptance"]], [ch["sensitivity"]], xerr=xe, yerr=ye, fmt="o", color=COLORS[c], ms=4.5,
                   capsize=2, lw=1, label=SHORT[c])
    a.plot([0, 1], [0, 1], color="#bbbbbb", lw=0.7)
    a.set(xlabel="False-acceptance rate $f$", ylabel="Sensitivity $s$", xlim=(-0.02, 1.02), ylim=(0, 1.04), title="(b) Checks against the key")
    a.legend(loc="lower right", frameon=False)
    a = ax[1, 0]
    for p in ("oracle", "strong", "vote", "agreement", "self", "confidence", "first"):
        y = curves[p]
        a.plot(ns[ns <= ATTEMPTS], y[ns <= ATTEMPTS], color=COLORS[p], lw=1.5, label=SHORT[p])
        a.plot(ns[ns >= ATTEMPTS], y[ns >= ATTEMPTS], color=COLORS[p], lw=1.1, ls="--")
    a.set_xscale("log")
    a.axvline(ATTEMPTS, color="#bbbbbb", lw=0.7)
    a.set(xlabel="Generations $n$", ylabel="Reliability", ylim=(0.80, 0.957), title="(c) Reliability against generations")
    a.legend(loc="lower right", frameon=False, ncol=2, columnspacing=0.8, handlelength=1.4)
    a = ax[1, 1]
    order = ["confidence", "agreement", "self", "strong"]
    x = np.arange(len(order))
    pooled = np.array([results["checks"][c]["pooled_precision"] for c in order])
    lim = np.array([results["protocols"][c]["limit"] for c in order])
    pci = np.array([results["checks"][c]["pooled_precision_ci95"] for c in order])
    lci = np.array([results["protocols"][c]["limit_ci95"] for c in order])
    a.errorbar(x - 0.2, pooled, yerr=[pooled - pci[:, 0], pci[:, 1] - pooled], fmt="s", color="k", ms=4.5, capsize=2, lw=1, label="Pooled precision")
    a.errorbar(x + 0.0, lim, yerr=[lim - lci[:, 0], lci[:, 1] - lim], fmt="o", color=COLORS["self"], ms=4.5, capsize=2, lw=1, label="Limit, fallback")
    abst = np.array([results["checks"][c]["ceiling_abstain"] for c in order])
    a.plot(x + 0.2, abst, "v", color="#555555", ms=5, label="Limit, abstaining")
    a.axhline(results["protocols"]["oracle"]["limit"], color=COLORS["oracle"], lw=0.8, ls="--", label="Oracle limit")
    a.axhline(results["population"]["mean_p"], color=COLORS["first"], lw=0.8, label="Single attempt")
    a.set_xticks(x)
    a.set_xticklabels(["Confidence", "Agreement", "Self-check", "Stronger\nmodel"])
    a.set(ylabel="Reliability", ylim=(0.40, 1.01), title="(d) Validated precision against the limit")
    a.legend(loc="lower right", frameon=False, ncol=1, numpoints=1)
    fig.tight_layout(h_pad=1.2, w_pad=1.0)
    fig.savefig(FIG / "measurement.pdf")
    fig.savefig(OUT / "measurement.pdf")
    plt.close(fig)


def make_robust_figure(robust, ns, curves):
    style()
    fig, ax = plt.subplots(1, 2, figsize=(6.5, 2.9))
    a = ax[0]
    counts = robust["items_by_correct_count"]
    ks = list(range(ATTEMPTS + 1))
    a.bar(ks, [counts[str(k)] for k in ks], color="#555555", width=0.7)
    for k in ks:
        a.text(k, counts[str(k)] + 0.2, str(counts[str(k)]), ha="center", fontsize=7.5)
    a.set(xlabel=f"Correct attempts out of {ATTEMPTS}", ylabel="Items", title=f"(a) Per-item success, {robust['n_items']} items")
    a.set_xticks(ks)
    a = ax[1]
    for p in ("oracle", "strong", "vote", "agreement", "self", "confidence", "first"):
        y = curves[p]
        a.plot(ns[ns <= ATTEMPTS], y[ns <= ATTEMPTS], color=COLORS[p], lw=1.5, label=SHORT[p])
        a.plot(ns[ns >= ATTEMPTS], y[ns >= ATTEMPTS], color=COLORS[p], lw=1.1, ls="--")
    a.set_xscale("log")
    a.axvline(ATTEMPTS, color="#bbbbbb", lw=0.7)
    a.set(xlabel="Generations $n$", ylabel="Reliability", title="(b) Reliability against generations")
    a.legend(loc="upper left", frameon=False, ncol=1, handlelength=1.4, bbox_to_anchor=(1.0, 1.0))
    fig.tight_layout(w_pad=1.0)
    fig.savefig(FIG / "robustness.pdf")
    fig.savefig(OUT / "robustness.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
