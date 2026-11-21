# Research

Findings, tiered by source proximity. T1 primary · T2 authoritative secondary · T3 reference · T4 general web (leads only). A claim that reaches the paper rests on a T1 or T2 source. Seed material in `chats/` was used only as a list of leads; every item below was re-located and inspected at the depth stated.

## Repeated sampling with imperfect verifiers (closest prior work)

- [T1] Davis, Hanin, Chen, Bailis, Stoica and Zaharia (2024), arXiv:2407.16831v1, Section 2.2, Theorems 1 and 2 (PDF pp. 3–4, read). For K i.i.d. generators and a verifier with completeness c and soundness s, the probability of returning the correct answer (random answer if all rejected) is rc(1 − (1 − β)^K)/β + (1 − β)^K/|A|, with β the acceptance probability. The gain over one generator as K → ∞ is positive iff c > 1 − s. The limit rc/β is the precision ceiling of this paper in other notation. The paper's single-item formula is therefore prior work; the paper credits it and does not claim it.
- [T1] Stroebl, Kapoor and Narayanan (2024; v3 26 March 2026), arXiv:2411.17501, abstract, Section 3 (pp. 5–6) and Appendix C (pp. 24–27), read. False positives of imperfect verifiers bound resampling accuracy regardless of compute. Weaker models have higher false-positive rates on HumanEval+/MBPP+, and if P_strong(correct) > P_weak(correct | pass), the weak model cannot match the strong one. Appendix C models easy and hard tasks (r1 = 0.87, r2 = 0.13, prior 0.58/0.42), with completeness and soundness and Bayesian updating after rejections, and finds small optimal K once false positives carry a cost. The verifiers are unit tests (a tool), not the invoker's own judgment. The paper adds the closed-form compute threshold, the population identity and bounds, and a measurement of novice checks.
- [T1] Brown et al. (2024), arXiv:2407.21787, abstract. Coverage rises roughly log-linearly with samples over four orders of magnitude. With automatic verifiers this becomes performance; majority voting and reward models plateau beyond several hundred samples.
- [T1] Chen, Davis, Hanin, Bailis, Stoica, Zaharia and Zou (2024), arXiv:2403.02419, abstract. Vote and Filter-Vote accuracy can rise then fall in the number of calls, explained by mixing easy and hard queries.
- [T1] Schaeffer et al. (2025), arXiv:2502.17578, abstract. Per-problem failure falls exponentially in attempts; aggregate power laws come from a heavy-tailed distribution of single-attempt success probabilities.
- [T1] Snell, Lee, Xu and Kumar (2024), arXiv:2408.03314, abstract. The value of test-time compute depends on prompt difficulty, and compute-optimal allocation beats best-of-N by more than 4x in efficiency.
- [T1] Cobbe et al. (2021), arXiv:2110.14168, abstract. Trained verifiers rank many sampled solutions on GSM8K and improve performance.
- [T1] Lightman et al. (2023), arXiv:2305.20050, abstract. Process supervision outperforms outcome supervision on MATH; the model solves 78% of a representative MATH test subset; PRM800K released. Used only for the MATH-500 pilot.
- [T1] Wang et al. (2022; ICLR 2023), arXiv:2203.11171, abstract. Self-consistency: sample several reasoning paths and take the most consistent answer.
- [T1] Chen et al. (2021), arXiv:2107.03374, Section 2.1 and Figure 3 (read). Unbiased pass@k estimator from n ≥ k samples; the plug-in 1 − (1 − p̂)^k is biased (their Appendix A). This paper uses the same without-replacement logic for all protocols at n ≤ 6 and flags its plug-in extrapolations as such.
- [T1] Gao, Schulman and Hilton (2022), arXiv:2210.10760, abstract. Optimizing against a proxy reward with best-of-n eventually lowers gold reward. This is the continuous analogue of the re-verification limit (Proposition 4).

## Self-evaluation by language models

- [T1] Kadavath et al. (2022), arXiv:2207.05221, abstract. Models can evaluate P(True) of their own samples with useful calibration on many tasks.
- [T1] Huang et al. (2023; ICLR 2024), arXiv:2310.01798, abstract. Without external feedback, models struggle to self-correct reasoning, and performance can degrade.
- [T1] Stechly, Valmeekam and Kambhampati (2024), arXiv:2402.08115, abstract. GPT-4 self-critique collapses on Game of 24, graph colouring and planning, while a sound external verifier yields large gains.
- [T1] Panickssery, Bowman and Feng (2024), arXiv:2404.13076, abstract. LLM evaluators recognize and prefer their own generations (self-preference bias).

## Voting, redundancy and detection (classical)

- [T1] Condorcet (1785), *Essai sur l'application de l'analyse…*, identity checked on archive.org (identifier essaisurlapplica00cond). Cited for the jury theorem as an attribution; no page-level claim.
- [T1] Boland (1989), *The Statistician* 38(3), 181–189, abstract (OpenAlex). States the jury theorem for independent jurors with p > 1/2 and presents generalizations with varying competence and with dependence between voters.
- [T1] Ladha (1992), *American Journal of Political Science* 36(3), abstract and first page (OpenAlex). Relaxes the independence assumption of the jury theorem for correlated votes.
- [T2] List and Goodin (2001), *Journal of Political Philosophy* 9(3), 277–306, identity and opening text (OpenAlex). Plurality generalization of the jury theorem to more than two options; cited as attribution only (the plurality result itself was not re-read).
- [T1] von Neumann (1956), Automata Studies, pp. 43–98; Moore and Shannon (1956), *J. Franklin Inst.* 262(3), 191–208. Identity only (Crossref). Cited as attributions for building reliable systems from unreliable components by redundancy and majority organs.
- [T2] Green and Swets (1966), *Signal Detection Theory and Psychophysics*, Wiley. Identity via OpenLibrary; cited as attribution for hit and false-alarm rates as separate parameters of a detector.
- [T1] Meehl and Rosen (1955), *Psychological Bulletin* 52(3), 194–216, abstract (OpenAlex). A sign is efficient only if it beats the base rates; the base-rate dependence of a test's predictive value.
- [T1] Ridout, Demétrio and Firth (1999), *Biometrics* 55(1), 137–148, abstract (Crossref/OpenAlex). Review and simulation comparison of intraclass-correlation estimators for binary data; the ANOVA estimator used here is among those studied.

## Human use of AI assistance (performance improvement versus novice sufficiency)

- [T1] Noy and Zhang (2023), *Science* 381(6654), 187–192, abstract (Crossref). 453 college-educated professionals; ChatGPT cut time by 40% and raised quality by 18%; inequality between workers decreased.
- [T1] Brynjolfsson, Li and Raymond (2025), *QJE* 140(2), 889–942, abstract (Crossref). 5,172 support agents; 15% more issues resolved per hour on average; less experienced and lower-skilled workers gain in speed and quality; the most experienced see small speed gains and small quality declines.
- [T1] Dell'Acqua et al. (2023), SSRN working paper 10.2139/ssrn.4573321, abstract (Crossref). 758 consultants; inside the frontier AI users completed 12.2% more tasks 25.1% faster with higher quality; on a task outside the frontier they were less likely to be correct (abstract: "19% less likely"). The published version is not used.
- [T1] Becker, Rush, Barnes and Rein (2025), arXiv:2507.09089v2, abstract and Appendix C.1.4 (read). RCT: 16 experienced developers, 246 tasks; AI allowed increased completion time by 19%; developers had forecast a 24% reduction and afterwards estimated a 20% reduction. Developers accepted under 44% of AI generations; about 9% of time with AI went to reviewing and cleaning AI output (on 44 issues with labelled screen recordings).
- [T1] Kwa et al. (2025; v4 10 July 2026), arXiv:2503.14499, abstract and Section 3.2.1 (read). 50% time horizon of frontier models around 110 minutes, doubling about every seven months since 2019. 80% horizons are 4–6x shorter, and the task suite cannot measure horizons at very high success rates such as 95%.
- [T1] Sastry et al. (2024), arXiv:2402.08797, abstract. Compute is detectable, excludable and quantifiable, and is produced by an extremely concentrated supply chain.
- [T2] Sen (1985), *Commodities and Capabilities*, North-Holland. Identity via OpenLibrary; attribution for the capability set as the set of achievable functionings.

## Benchmark

- [T1] Omni-MATH: Gao et al. (2024), arXiv:2410.07985, abstract; dataset card and file test.jsonl at Hugging Face revision 40ba231d8f16e29ecd40e6407e2c8640145a8f62 (Apache-2.0), SHA-256 7c87be8e…f168, 4,428 rows. Study items: source HMMT_2, difficulty ≥ 5.5, integer answer, no figure reference (69 eligible; first 40 in a seeded order).
- [T1] Key audit: h09 reference answer 2009 is wrong; the recursion gives −2009 (exact check in tests/test_keys.py). h07 reference −5892 checked algebraically. h22 reference 6014950 matches the formula in the reference solution (n = 100); the extremal argument was not re-derived.
- [T1] MATH-500 (Lightman et al. 2023; MIT licence, openai/prm800k commit 7ecc794): used only for a 10-call pilot (all correct), which led to the harder item set.

## Negative and open findings

- The single-item ceiling is Davis et al.'s Theorem 1 limit; the paper's novelty is restricted to the compute-threshold reading, the population identity and bounds, the re-verification limit and the measurement.
- Verdicts are elicited once per distinct candidate, so the measurement treats each check as a deterministic function of the candidate. Proposition 4 says re-checking such a check cannot raise its ceiling; the repeatability of model verdicts was not measured.

## Revision round 1 (2026-11-21)

- [T1] Bowman et al. (2022), arXiv:2211.03540, abstract: scalable oversight; sandwiching experiments on MMLU and time-limited QuALITY. Assisted participants beat the model alone and themselves unaided.
- [T1] Saunders et al. (2022), arXiv:2206.05802, abstract: self-critiquing models assist human evaluators.
- [T1] Burns et al. (2023), arXiv:2312.09390, abstract: weak-to-strong generalization.
- [T1] Bainbridge (1983), Automatica 19(6), 775–779, full text, §1.1.3 (p. 776): an automatic system installed because it does the job better than the operator is monitored by that operator; "Another problem arises when one asks whether monitoring can be done by an unskilled operator."
- [T1] Parasuraman and Manzey (2010), Human Factors 52(3), 381–410, abstract: automation bias yields omission and commission errors, in naive and expert users, not prevented by training or instructions.
- [T1] Rothschild and Stiglitz (1970), JET 2(3), 225–243, identity only: mean-preserving spread.
- [T1] Versions of record: Dell'Acqua et al. (2026), Organization Science 37(2), 403–423, abstract; Panickssery et al. (2024), NeurIPS 37, pp. 68772–68802.
- Memorization: explicit recall cues in the frozen outputs, counted by a fixed pattern in run_all.py (19 of 56 stronger-model verdicts in the main set). This motivated the robustness run on non-HMMT items of difficulty 7 or more.
