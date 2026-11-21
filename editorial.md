# Editorial record

Status: authored and read in full by the authoring agent; independent editorial and visual review pending.

## Contribution and reader

Question: how much reliability can compute buy for someone who cannot do a task and has only an imperfect way of checking it? Reader: an informed reader outside machine learning, and researchers on test-time compute and verification.

What is new, against the closest prior work:

- Davis et al. (2024) give the single-task formula for a verifier-based judge and the gain condition. Stroebl, Kapoor and Narayanan (2024) show the cap empirically for unit-test verifiers and model a two-type task mixture.
- The paper adds the compute threshold $n^*(\rho)$ for the fallback protocol, finite exactly when $\rho$ lies below the ceiling, with the equivalent likelihood-ratio condition.
- It adds the exact identity linking pooled (validated) precision to the resampling limit across tasks, with the intraclass-correlation bounds for a common check.
- It adds the re-verification limit under correlated verdicts.
- It adds a measurement of novice checks (stated confidence, agreement, self-check) against a stronger-model check and the key, on 40 Omni-MATH items with a current small model.

Confidence: the propositions are proved and checked numerically; the measurement is small (40 items) and its differences between checks are not resolved from zero.

## Material worth preserving

- The odds form of the ceiling and its reading: the invoker's evidence is applied once.
- The covariance identity, and the observation that tasks where the check rejects everything never enter pooled precision yet lower the limit. In the data, the stronger checker's validated precision of 0.991 became 0.938 under resampling.
- The self-check's errors concentrated on the generator's repeated wrong answers (3 of 4 against 1 of 14).
- The benchmark key error, read as false acceptance by both model checks under the original key.

## Reverse outline

1. Opening case and question; the thesis stated neutrally; prior work credited; contributions listed.
2. Attainable set and compute threshold; performance improvement versus novice sufficiency; verified human-AI evidence that reliability and verification are where the two claims differ.
3. Model: i.i.d. attempts, check with $s,f$, four protocols, compute counted in attempts.
4. Propositions 1 to 4 with proofs, plurality voting (Condorcet and correlated voters), and the conditional reading of "power equals compute".
5. Measurement: design, call budget, key audit, estimation, generator, checks and curves, uncertainty, pooled precision against the limit, original-key sensitivity, cost, and what the measurement does not show.
6. Who holds the check: purchased verification as compute under others' control; open questions.

## Strongest rival

Verification is not a separate competence: it can be bought with the same compute, from a stronger model, a test suite or a vote, so "power equals compute" survives. The paper measures this directly. The stronger-model check recovered 82% of the oracle gain, and the vote 65%. The paper states the condition under which purchased verification restores the claim: the likelihood-ratio threshold of Proposition 2, with errors not shared with the generator, as in Proposition 3. A second rival says the ceiling is practically irrelevant because failures concentrate on items no check can rescue. The measurement partly supports it: 2 never-solved items cost 5 points, more than the self-check's 3-point shortfall against the oracle, and the latter is not resolved from zero.

## Decisions and remaining checks

- The single-task formula is presented as prior work (Davis et al.); novelty is restricted to the threshold, population identity and bounds, the re-verification limit and the measurement.
- Fallback to the first attempt is the main protocol, because an invoker always receives an output; the abstaining variant is stated and used for the covariance identity.
- MATH-500 was too easy for both available small models (10 of 10 pilot attempts correct). Omni-MATH HMMT February items at difficulty 5.5 and above were used instead.
- Model checks give one verdict per distinct candidate. This models an invoker who does not re-judge, and leaves Proposition 4 untested.
- One key error (h09) was corrected after hand inspection with an exact check; results under the original key are reported.
- The draft's long literature-review sections were not carried over; only the attainable-set definition, the improvement/sufficiency distinction and a short treatment of who controls verification remain.
- Remaining: independent review of all 27 source claims (all `verified: false`), coverage stamp, editorial and visual review records by a reviewer from another model family.
