# Post-Competence: Verification Precision Caps the Reliability Compute Buys

A person who cannot do a task, or check it, can still sample a machine system many times. This paper asks how much reliability that repeated sampling can buy. Accepting the first output that passes a check converges to the check's precision at the system's success rate, so a target reliability is reachable with finite compute only when the check's likelihood ratio is large enough. Across tasks, resampling falls short of a check's pooled precision by an exact covariance term and is limited by how strongly attempt outcomes correlate within tasks.

A measurement with a small current model on 40 olympiad-level problems estimates single-attempt accuracy and the intraclass correlation of attempt outcomes, and measures the sensitivity and false-acceptance rate of checks available to someone who cannot solve the problems: stated confidence, agreement between samples and the model's own verdict. These are compared with a stronger model as checker and with the reference key.

[Read the paper](https://piatra.institute/papers/post-competence.pdf)

## Build

```bash
uv run build.py          # -> paper/PAPER.pdf  (vendored canonical recipe)
```

Requires `pandoc` and `xelatex` on PATH. From the workspace you can also run `papers build post-competence`.

## Simulation and data

The analysis, tests, frozen model outputs and data-collection scripts are in `simulation/`; see `simulation/README.md`. The benchmark is Omni-MATH (Apache-2.0).
