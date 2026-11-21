"""Collect model outputs for the reliability study (run separately, never by run_all.py).

Two kinds of call, each sent once, non-interactively, through the `claude` CLI with a pinned model,
a fixed system prompt, no tools, no setting sources, no session persistence and stdin closed:

  gen    one independent attempt at one item (fresh session per attempt);
  check  one verdict on one distinct (item, final answer) candidate, shown with the full text of
         the first attempt that produced that answer (fresh session per verdict).

Raw CLI JSON output is written per call under data/llm/<tag>/ and later consolidated by
freeze_llm.py into data/llm/<tag>.jsonl plus a manifest with the model identifier, CLI version,
flags, dates and the SHA-256 of every prompt. run_all.py analyses only the frozen files.

Usage:
    uv run python collect_llm.py gen --model claude-haiku-5-5 --effort low --attempts 8
    uv run python collect_llm.py check --model claude-haiku-5-5 --effort low --source gen__claude-haiku-5-5__low
    uv run python collect_llm.py gen --model claude-haiku-5-5 --effort low --attempts 1 --pilot 4
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path

from pc.grading import parse_answer

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

SOLVER_SYSTEM = (
    "You solve competition mathematics problems. Reason as needed, then end your reply with exactly "
    "two lines in this form:\n"
    "ANSWER: <the final answer, written as an integer>\n"
    "CONFIDENCE: <an integer from 0 to 100: your probability, in percent, that the answer is correct>"
)
CHECK_SYSTEM = (
    "You check proposed solutions to competition mathematics problems. Decide whether the proposed "
    "final answer is correct. End your reply with exactly one line, either\n"
    "VERDICT: CORRECT\n"
    "or\n"
    "VERDICT: INCORRECT"
)


def gen_prompt(problem: str) -> str:
    return f"Problem:\n{problem}"


def check_prompt(problem: str, solution: str, answer: str) -> str:
    return f"Problem:\n{problem}\n\nProposed solution:\n{solution}\n\nProposed final answer: {answer}"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def flags(effort: str) -> list[str]:
    base = ["--tools", "", "--output-format", "json", "--no-session-persistence", "--setting-sources", "",
            "--strict-mcp-config"]
    return base if effort == "default" else [*base, "--effort", effort]


def call(model: str, system: str, prompt: str, effort: str, workdir: str, timeout: int = 900) -> dict:
    cmd = ["claude", "-p", prompt, "--model", model, "--system-prompt", system, *flags(effort)]
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=workdir, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                          timeout=timeout)
    return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr[-2000:],
            "wall_seconds": round(time.time() - t0, 2)}


def load_items(items_file: str = "items.json") -> list[dict]:
    return json.loads((DATA / items_file).read_text())["items"]


def load_records(tag: str) -> list[dict]:
    frozen = DATA / "llm" / f"{tag}.jsonl"
    if frozen.exists():
        return [json.loads(line) for line in frozen.read_text().splitlines()]
    return [json.loads(p.read_text()) for p in sorted((DATA / "llm" / tag).glob("*.json")) if p.name != "manifest.json"]


def result_text(rec: dict) -> str:
    try:
        return json.loads(rec["stdout"]).get("result", "") or ""
    except (json.JSONDecodeError, TypeError):
        return ""


def run_jobs(jobs, out: Path, model: str, effort: str, workers: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    workdir = tempfile.mkdtemp(prefix="pc-llm-")

    def run(job):
        path = out / f"{job['key']}.json"
        if path.exists():
            return path, "cached"
        rec = None
        for attempt in range(1, 4):
            started = dt.datetime.now(dt.timezone.utc).isoformat()
            try:
                res = call(model, job["system"], job["prompt"], effort, workdir)
            except subprocess.TimeoutExpired:
                res = {"returncode": -1, "stdout": "", "stderr": "timeout", "wall_seconds": None}
            rec = {**job["meta"], "model": model, "effort": effort, "prompt_sha256": sha(job["prompt"]),
                   "system_sha256": sha(job["system"]), "started_utc": started, "cli_attempt": attempt, **res}
            if res["returncode"] == 0 and res["stdout"].strip():
                break
            time.sleep(5 * attempt)
        path.write_text(json.dumps(rec, indent=1))
        return path, rec["returncode"]

    t0 = time.time()
    done = 0
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for path, rc in ex.map(run, jobs):
            done += 1
            if done % 10 == 0 or done == len(jobs):
                print(f"{done}/{len(jobs)} {path.name} rc={rc} {time.time() - t0:.0f}s", flush=True)


def write_manifest(out: Path, kind: str, model: str, effort: str, system: str, jobs: list[dict], extra: dict) -> None:
    version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    manifest = {"kind": kind, "model": model, "cli": version, "effort": effort, "system_prompt": system,
                "flags": flags(effort), "n_prompts": len(jobs),
                "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "prompt_sha256": {j["key"]: sha(j["prompt"]) for j in jobs}, **extra}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))


def cmd_gen(args) -> None:
    items = load_items(args.items_file)
    if args.items:
        items = items[: args.items]
    jobs = [{"key": f"{it['item_id']}__a{k}", "system": SOLVER_SYSTEM, "prompt": gen_prompt(it["problem"]),
             "meta": {"kind": "gen", "item_id": it["item_id"], "attempt_index": k}}
            for it in items for k in range(args.attempts)]
    if args.pilot:
        jobs = jobs[: args.pilot]
    tag = f"gen__{args.model}__{args.effort}{args.tag_suffix}"
    out = DATA / ("pilot" if args.pilot else "llm") / tag
    run_jobs(jobs, out, args.model, args.effort, args.workers)
    write_manifest(out, "gen", args.model, args.effort, SOLVER_SYSTEM, jobs,
                   {"attempts_per_item": args.attempts, "n_items": len(items)})
    print("wrote", out)


def cmd_check(args) -> None:
    items = {it["item_id"]: it for it in load_items(args.items_file)}
    recs = sorted(load_records(args.source), key=lambda r: (r["item_id"], r["attempt_index"]))
    if args.per_attempt_wrong:
        return cmd_check_wrong_attempts(args, items, recs)
    first = {}
    for r in recs:
        text = result_text(r)
        ans = parse_answer(text)
        key = (r["item_id"], ans)
        if ans is not None and key not in first:
            first[key] = (r["attempt_index"], text)
    jobs = []
    for (item_id, ans), (k, text) in sorted(first.items(), key=lambda kv: (kv[0][0], kv[1][0])):
        prompt = check_prompt(items[item_id]["problem"], text, str(ans))
        jobs.append({"key": f"{item_id}__ans{ans}", "system": CHECK_SYSTEM, "prompt": prompt,
                     "meta": {"kind": "check", "item_id": item_id, "candidate_answer": ans,
                              "from_attempt_index": k, "source": args.source}})
    tag = f"check__{args.model}__{args.effort}__on__{args.source}"
    out = DATA / "llm" / tag
    run_jobs(jobs, out, args.model, args.effort, args.workers)
    write_manifest(out, "check", args.model, args.effort, CHECK_SYSTEM, jobs, {"source": args.source})
    print("wrote", out, len(jobs), "checks")


def cmd_check_wrong_attempts(args, items, recs) -> None:
    """Verdicts on every wrong attempt not already judged as the first attempt with its answer.

    Added in revision: the main check judges one attempt per distinct (item, answer); this collects a
    verdict on each remaining wrong attempt, shown with its own solution text, so the false-acceptance
    rate can also be computed with one verdict per attempt. Correctness is used only to select attempts.
    """
    corrections = {c["item_id"]: c["corrected_answer"] for c in
                   json.loads((HERE / "key_corrections.json").read_text())["corrections"]}
    seen = set()
    jobs = []
    for r in recs:
        text = result_text(r)
        ans = parse_answer(text)
        key = (r["item_id"], ans)
        if ans is None:
            continue
        first_time = key not in seen
        seen.add(key)
        truth = corrections.get(r["item_id"], items[r["item_id"]]["answer"])
        if first_time or ans == truth:
            continue
        prompt = check_prompt(items[r["item_id"]]["problem"], text, str(ans))
        jobs.append({"key": f"{r['item_id']}__a{r['attempt_index']}", "system": CHECK_SYSTEM, "prompt": prompt,
                     "meta": {"kind": "check", "item_id": r["item_id"], "candidate_answer": ans,
                              "attempt_index": r["attempt_index"], "source": args.source}})
    tag = f"checkwrong__{args.model}__{args.effort}__on__{args.source}"
    out = DATA / "llm" / tag
    run_jobs(jobs, out, args.model, args.effort, args.workers)
    write_manifest(out, "check-wrong-attempts", args.model, args.effort, CHECK_SYSTEM, jobs, {"source": args.source})
    print("wrote", out, len(jobs), "checks")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("--model", required=True)
    g.add_argument("--effort", default="low", help="low|medium|high, or 'default' to omit the flag")
    g.add_argument("--attempts", type=int, required=True)
    g.add_argument("--items", type=int, default=0)
    g.add_argument("--pilot", type=int, default=0)
    g.add_argument("--workers", type=int, default=6)
    g.add_argument("--items-file", default="items.json")
    g.add_argument("--tag-suffix", default="")
    c = sub.add_parser("check")
    c.add_argument("--model", required=True)
    c.add_argument("--effort", default="low")
    c.add_argument("--source", required=True)
    c.add_argument("--workers", type=int, default=6)
    c.add_argument("--items-file", default="items.json")
    c.add_argument("--per-attempt-wrong", action="store_true")
    args = ap.parse_args()
    {"gen": cmd_gen, "check": cmd_check}[args.cmd](args)


if __name__ == "__main__":
    main()
