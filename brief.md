# Brief

## Question

When a person who cannot do a task, or check it, invokes a machine system that sometimes does it correctly, how much reliability can more computation buy them? Under what conditions is the claim that "power equals compute" true for such a person, and what part does their own ability to verify play?

## Claim

Repeated sampling buys reliability only up to the precision of whatever check the invoker uses to accept an output. For one task, with per-attempt success probability p, check sensitivity s and false-acceptance rate f, accepting the first output that passes the check converges to s·p / (s·p + f·(1 − p)). This is the check's positive predictive value at the generator's base rate (Davis et al. 2024 derive the finite-n form). A target reliability ρ is purchasable with finite compute only if ρ is below this ceiling, which in odds form requires the check's likelihood ratio s/f to exceed odds(ρ)/odds(p). Across a population of tasks the ceiling is lower than the pooled precision of the check. The exact shortfall is the covariance between per-task acceptance rate and per-task precision, divided by the mean acceptance rate. With a common check it lies between single-attempt accuracy and the pooled formula, falling as the intraclass correlation of attempt outcomes rises, and at an intraclass correlation of one compute buys nothing under any check. Measured with a current small model on olympiad-level problems, the novice checks available to someone who cannot solve the problems (the model's own stated confidence, its own verdict in a fresh context, agreement between two samples) have false-acceptance rates far from zero. The paper reports where their ceilings bind and where they do not.

## Kind

Formal model with proofs, plus a measurement on real model outputs (has_simulation: true). The theory is checked against simulation and enumeration in tests; the measurement uses frozen outputs of a pinned model on a public benchmark.

## Strongest serious alternative

Verification is not a separate competence that the invoker must bring: it can be bought with the same compute, from a stronger model, a test suite, or a vote among samples. On this view "power equals compute" survives intact, and the ceiling is an artefact of choosing a weak check. The paper takes this seriously. It measures a stronger-model check and the vote alongside the novice checks, and states the condition under which purchased verification restores the claim: the purchased check needs a likelihood ratio large enough, with errors not shared with the generator.

A second alternative holds that the ceiling is practically irrelevant: generators are already reliable on most tasks, and their failures concentrate on items where even a perfect check would not help. The measurement reports how much of the remaining error is of this kind.

## Cornerstone literature

- Repeated sampling and verifiers in machine learning: Stroebl, Kapoor and Narayanan (2024); Davis et al. (2024); Brown et al. (2024); Snell et al. (2024); Cobbe et al. (2021); Lightman et al. (2023); Chen et al. (2024) on vote scaling; Schaeffer et al. (2025); Wang et al. (2023) on self-consistency; Chen et al. (2021) on the unbiased pass@k estimator.
- Self-evaluation by language models: Kadavath et al. (2022); Huang et al. (2024); Stechly et al. (2024); Panickssery et al. (2024).
- Majority voting and reliable systems from unreliable parts: Condorcet (1785); Ladha (1992) and Boland (1989) on correlated voters; List and Goodin (2001); von Neumann (1956); Moore and Shannon (1956).
- Detection and base rates: Green and Swets (1966); Meehl and Rosen (1955).
- Intraclass correlation for binary data: Ridout, Demétrio and Firth (1999).
- Human use of AI assistance, to separate performance improvement from novice sufficiency: Noy and Zhang (2023); Brynjolfsson, Li and Raymond (2025); Dell'Acqua et al. (2023); Becker et al. (2025); Kwa et al. (2025).
- Control of compute: Sastry et al. (2024).
- Benchmark: Omni-MATH (Gao et al. 2024).
