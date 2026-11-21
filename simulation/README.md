# Simulation and measurement

Code for the theory checks and the measurement in the paper. Every number in the paper comes from `output/results.json`, written by the recorded run of `run_all.py`.

## Layout

- `pc/theory.py`: closed forms (ceiling, reliability with and without fallback, compute threshold, required likelihood ratio, Beta-population ceiling, repeated-check ceiling).
- `pc/estimators.py`: per-item estimators from observed attempts (exact without-replacement averages for budgets up to the number of attempts; plug-in values beyond), the intraclass-correlation estimator and pooled sensitivity and false-acceptance rates.
- `pc/grading.py`: parsing of final answers, stated confidences and verdicts.
- `run_all.py`: the recorded analysis. It reads only frozen files and writes `output/results.json`, `output/theory.pdf`, `output/measurement.pdf` and copies of the figures into `../paper/figures/`.
- `tests/`: closed forms against simulation and exhaustive enumeration, estimator checks, and an exact check of the corrected reference answer.
- `key_corrections.json`: the one corrected reference answer (item h09) with its reason.
- `fetch_data.py`: downloads the benchmark file and freezes the study items (run once; not part of the analysis).
- `collect_llm.py`, `freeze_llm.py`: model calls through the `claude` command-line interface and their consolidation into frozen files (run once; not part of the analysis).
- `data/`: frozen inputs. `items.json` and `omni_math_test.jsonl` (Omni-MATH, Apache-2.0); `llm/*.jsonl` with `*.manifest.json` (raw CLI JSON for every analysed call); `pilot/` (pilot calls and the MATH-500 pilot items, MIT licence); `*_log.txt` (collection progress logs).

## Reproduce the analysis

```bash
uv sync
uv run python run_all.py
uv run --group dev python -m pytest -q tests
```

The recorded runs were made from the archive root with

```bash
./papers run post-competence --id analysis --cwd simulation --artifact simulation/output/results.json --artifact simulation/output/theory.pdf --artifact simulation/output/measurement.pdf --input <every file under simulation/data/llm and simulation/data/pilot, plus items.json and omni_math_test.jsonl> -- uv run python run_all.py
./papers run post-competence --id tests --cwd simulation --artifact simulation/output/tests.xml -- uv run --group dev python -m pytest -q tests --junitxml=output/tests.xml
```

Seeds: item order 20261121 (`fetch_data.py`); bootstrap and vote simulation 20261121 (`run_all.py`).

## Data collection (already done; not needed to reproduce)

All calls used `claude` CLI 2.1.329 non-interactively with `--tools ""`, `--output-format json`, `--no-session-persistence`, `--setting-sources ""`, `--strict-mcp-config`, `--effort low`, a fixed system prompt and stdin closed, on 21 November 2026.

```bash
uv run python fetch_data.py
uv run python collect_llm.py gen --model claude-haiku-5-5 --effort low --attempts 6 --items 40
uv run python freeze_llm.py
uv run python collect_llm.py check --model claude-haiku-5-5 --effort low --source gen__claude-haiku-5-5__low
uv run python collect_llm.py check --model claude-sonnet-5-5 --effort low --source gen__claude-haiku-5-5__low
uv run python freeze_llm.py
```

Calls: 240 generations, 56 self-check verdicts and 56 stronger-model verdicts (352 analysed). The pilot used 18 calls: 4 attempts by `claude-haiku-5-5` and 6 by `claude-haiku-4-5-20251001` on MATH-500 Level-5 problems (all correct), then 8 by `claude-haiku-5-5` on the first 8 study items (excluded from the analysis). Two one-word calls checked that the `claude-haiku-4-5` identifiers were available; they were not stored. Total: 372 calls.

The stated-confidence threshold of 90 was fixed after the pilot and before the study data were analysed. Item h09's reference answer in Omni-MATH (2009) is wrong; the analysis uses −2009 (see `key_corrections.json` and `tests/test_keys.py`) and also reports results under the original key.
