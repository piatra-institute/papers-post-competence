"""Fetch Omni-MATH and freeze the study items (run once, never by run_all.py).

Source: the Hugging Face dataset KbsdJames/Omni-MATH at a pinned revision (Apache-2.0 licence),
file test.jsonl (4,428 problems; Gao et al., 2024). The script verifies the file's SHA-256 and keeps
the problems that satisfy all of:
  source == "HMMT_2" (HMMT February), Omni-MATH difficulty >= 5.5,
  reference answer an integer (optionally wrapped in $...$),
  no reference to a figure or diagram in the problem text.
The eligible problems are put in a seeded random order; the study uses a prefix of that order.
Writes data/omni_math_test.jsonl (the unmodified file) and data/items.json.

Usage: uv run python fetch_data.py
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REVISION = "40ba231d8f16e29ecd40e6407e2c8640145a8f62"
URL = f"https://huggingface.co/datasets/KbsdJames/Omni-MATH/resolve/{REVISION}/test.jsonl"
SHA256 = "7c87be8ee41ac7c7a597ef5a5500e84bd2b639a85a06db3da7f69bf9a32ef168"
ORDER_SEED = 20261121
INT = re.compile(r"\s*\$?\s*(-?\d+)\s*\$?\s*")
FIGURE = re.compile(r"figure|diagram|pictured|\[asy\]|shown (below|above|at right|at left|here)", re.IGNORECASE)


def main() -> None:
    raw = urllib.request.urlopen(URL, timeout=120).read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"checksum mismatch: {digest}")
    data = HERE / "data"
    data.mkdir(exist_ok=True)
    (data / "omni_math_test.jsonl").write_bytes(raw)
    rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    eligible = []
    for idx, r in enumerate(rows):
        m = INT.fullmatch(str(r["answer"]))
        if r["source"] == "HMMT_2" and float(r["difficulty"]) >= 5.5 and m and not FIGURE.search(r["problem"]):
            eligible.append({"row": idx, "domain": r["domain"], "difficulty": float(r["difficulty"]),
                             "source": r["source"], "problem": r["problem"], "answer": int(m.group(1))})
    random.Random(ORDER_SEED).shuffle(eligible)
    items = [{"item_id": f"h{k:02d}", **it} for k, it in enumerate(eligible)]
    meta = {"dataset": "KbsdJames/Omni-MATH", "revision": REVISION, "source_url": URL, "sha256": SHA256,
            "licence": "Apache-2.0", "n_rows": len(rows), "order_seed": ORDER_SEED,
            "selection": "source == HMMT_2, difficulty >= 5.5, integer answer, no figure reference",
            "n_eligible": len(items)}
    (data / "items.json").write_text(json.dumps({"meta": meta, "items": items}, indent=1, ensure_ascii=False))
    print(f"{len(rows)} rows; {len(items)} eligible items")


if __name__ == "__main__":
    main()
