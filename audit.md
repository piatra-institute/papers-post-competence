# Audit

Dated log of editorial passes and verification runs. Newest first.

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
