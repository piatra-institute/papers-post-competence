# Audit

Dated log of editorial passes and verification runs. Newest first.

## 2026-11-21: revision round 3 (closure check 2)

Changes:
- Figure 1 caption no longer promises a dotted ceiling line in panel (a).
- Two recall labels corrected (robust|strong|r15|25 and robust|self|r06|1 are now remembered_answer), so the robustness set reads stronger model 33/49 (67%) and self-check 21/49. The shares are stated as lower bounds; the abstract now reads "at least 30% and 67%".
- The sentence in Section 5.6 now attributes the near-zero gain to Proposition 3(a), not Proposition 2.

Verification: `analysis` and `tests` re-recorded (PASS); 412 claims, no FAIL; coverage 355 numerals bound, 0 unbound; standards PASS (abstract 248 words); 21 pages, 0 missing glyphs; `papers check`: 425 PASS, 34 NEEDS_REVIEW, 5 NOT_APPLICABLE, 0 FAIL.

## 2026-11-21: revision round 2 (closure check)

Scope: closure findings F3 (memorisation, partly closed), e-ridout (not checkable), unbound quantities, a stale caption, and two Figure 1 overlaps.

Changes:
- Every checker verdict that matches the recall-cue pattern (84 verdicts) was hand-classified as remembered answer, related fact, or no recall. Labels are frozen in simulation/recall_labels.json and summarised in results.json /recall_labels. The abstract, Sections 5.4, 5.5 and 6 now report hand-classified shares: the stronger model invoked a remembered answer in 17/56 and 32/49 verdicts. On the robustness set, remembered answers led the self-check to accept 13/15 and the stronger model 4/23 wrong candidates.
- e-ridout converted to an attribution (interpretation claim); sources.md updated. The 31 other source claims are unchanged.
- Unbound quantities bound: example parameters, the corrected-key count (rewritten with numerals), the robustness item where self-check precision is below p (new field /robust/items_self_precision_below_p), and definition or assumption claims for the unit-cost, agreement, one-verdict and scope statements.
- Figure 2 caption corrected. Figure 1b and 1c labels and legend moved clear of the lines.

Verification:
- Recorded runs `analysis` and `tests` re-recorded: PASS.
- `papers claims`: 410 claims (306 computation, 31 source, 73 other). No FAIL.
- Coverage self-audit: 355 numerals bound, 0 unbound. 45 one/second/single/once words lie inside bound passages; the 10 outside are terms, headings, ordinals or pronouns.
- `papers refs --verify`: PASS. `papers standards`: PASS (abstract 249 words).
- Build: 21 pages, 0 missing-character warnings; changed pages re-inspected.

## 2026-11-21: revision round 1 (referee Gemini 4 Hydrogen)

Scope: responses to findings F1–F11 (ledger: revision/2026-11/ledger/post-competence/fix-round1.json).

Changes:
- Theory: Proposition 3(b) restated as bounds plus a second-order term, with a counterexample showing the ICC does not fix the ceiling and the mean-preserving-spread ordering (F1). Proposition 4 restated exactly through $\beta_k$ (F4). The sign error in the proof of Proposition 1 is corrected and boundary conditions are added to Propositions 1–3 (F7).
- Compute counted in generations; agreement re-estimated by generations with a new exact estimator and test (F2). Section 6 separates frontier-model verification from local tools (F5). Five oversight and automation-bias references added (F6), plus Rothschild and Stiglitz (1970); versions of record for Dell'Acqua et al. (2026) and Panickssery et al. (2024) (F11). Figure 2d shows the abstaining limit (F8). Verdict caching is stated as a modelling choice, and 22 per-attempt re-judgements are reported (F9). The intro no longer states an extrapolation as observed (F10).
- New data (F3), same CLI 2.1.329, models and flags:
  - 22 verdicts on repeated wrong attempts;
  - a robustness run of 248 calls on the first 25 of 115 non-HMMT Omni-MATH items with difficulty of at least 7 (150 generations, 49 self-check and 49 stronger-model verdicts);
  - recall-cue counts on all frozen outputs.
  - Total calls over both rounds: 642.

Verification:
- Recorded runs `analysis` (27 declared frozen inputs) and `tests` (14 tests): PASS.
- `papers claims`: 382 claims (289 computation, 32 source, 61 other). No FAIL; source claims `verified: false`.
- Coverage self-audit: 341 numerals bound, 2 spelled-out quantities bound, 0 unbound. Exempt: 121 constants inside math, 27 cross-references, 16 heading numbers, 4 identifiers, 2 citation locators.
- `papers refs --verify`: 37 DOIs match (4 with advisory page or container differences); 3 entries without DOI, identity checked by hand.
- `papers standards`: PASS (abstract 247 words).
- Build: 20 pages, 0 missing-character warnings; every page rendered at 80 dpi and inspected.

## 2026-11-21: first build

Scope: new paper written from the seed material in `chats/`, which was used only as leads. The result promised there was untested; the paper makes it the result, with proofs and a measurement.

Built:
- Theory: Propositions 1–4 (fallback reliability and its limit, compute threshold and likelihood-ratio condition, population identity and ICC bounds, re-verification limit), checked against simulation and enumeration in `simulation/tests/test_theory.py`.
- Measurement: 40 Omni-MATH HMMT February items (difficulty at least 5.5, integer answers), 6 attempts each by `claude-haiku-5-5` at low effort. One verdict per distinct candidate from `claude-haiku-5-5` (self-check) and `claude-sonnet-5-5`. 352 analysed calls, 18 pilot calls and 2 unstored availability probes, 372 in all. CLI 2.1.329, 21 November 2026.
- Key audit: item h09 key corrected from 2009 to −2009, with an exact check in `simulation/tests/test_keys.py`; original-key results are reported.

Verification:
- Recorded runs: `analysis` (run_all.py, all frozen data declared with `--input`) and `tests` (13 tests). Both PASS.
- `papers claims`: 256 claims (191 computation, 27 source, 38 definition, assumption, interpretation or normative). No FAIL; source claims stay `verified: false` for the independent reviewer. Classics not re-read (Condorcet, List and Goodin, Green and Swets, Sen, von Neumann, Moore and Shannon) are attributions without source claims.
- Coverage self-audit (every numeral per paragraph against claims.yaml): 233 numerals bound, 0 unbound, 0 spelled-out quantities. Exempt: 101 constants inside math, 19 cross-references, 15 heading numbers, 4 identifiers, 2 citation locators.
- `papers refs --verify`: 31 DOIs match their registries (3 with advisory page or container differences); 3 entries without DOIs (Condorcet 1785, Green and Swets 1966, Sen 1985) identity-checked by hand via archive.org and OpenLibrary.
- `papers standards`: PASS (abstract 249 words).
- Build: 17 pages, 0 missing-character warnings; every page rendered at 80 dpi and inspected; figures drawn at the 6.5-inch text width with text of at least 7.5 pt.
