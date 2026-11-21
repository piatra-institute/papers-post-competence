"""Consolidate per-call records into one sorted JSONL file per setting (run once after each collection).

data/llm/<tag>/<key>.json + manifest.json  ->  data/llm/<tag>.jsonl + data/llm/<tag>.manifest.json
Each line is the unmodified record written by collect_llm.py. The per-call directory is removed only
after the consolidated file has been written and re-read with the same records. The same applies to
data/pilot/.

Usage: uv run python freeze_llm.py
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent

for root in (HERE / "data" / "llm", HERE / "data" / "pilot"):
    if not root.exists():
        continue
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        recs = [json.loads(p.read_text()) for p in sorted(d.glob("*.json")) if p.name != "manifest.json"]
        recs.sort(key=lambda r: (r["item_id"], r.get("attempt_index", -1), str(r.get("candidate_answer", ""))))
        manifest = json.loads((d / "manifest.json").read_text())
        if len(recs) != manifest["n_prompts"]:
            raise SystemExit(f"{d.name}: {len(recs)} records, manifest says {manifest['n_prompts']}")
        bad = [r for r in recs if r["returncode"] != 0]
        if bad:
            raise SystemExit(f"{d.name}: {len(bad)} failed calls; rerun collection first")
        out = root / f"{d.name}.jsonl"
        out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in recs))
        (root / f"{d.name}.manifest.json").write_text(json.dumps(manifest, indent=1))
        back = [json.loads(line) for line in out.read_text().splitlines()]
        assert back == recs
        shutil.rmtree(d)
        print(f"{root.name}/{d.name}: {len(recs)} records -> {out.name}")
