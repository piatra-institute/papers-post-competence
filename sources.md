# Sources

The frozen bibliography (references.yaml, 33 entries). For each source: how its identity was checked, what was actually inspected, and the limits of its use in the paper. "Identity" means the registry record was matched for title, authors and year. No quotation or page number in the paper or in claims.yaml comes from a passage that was not read.

## Repeated sampling and verification

- **davis2024**: Davis, Hanin, Chen, Bailis, Stoica, Zaharia (2024), arXiv:2407.16831. Identity: DataCite. Inspected: full text v1, Section 2 (Definition 1, Theorems 1 and 2 with proofs, pp. 3–4). Use: credited as the source of the single-item formula and of the gain condition c > 1 − s. Their protocol returns a random answer when every candidate is rejected; this paper's fallback returns the first candidate, which changes only the finite-n term.
- **stroebl2024**: Stroebl, Kapoor, Narayanan (2024), arXiv:2411.17501. Identity: DataCite (current title "The Limits of Inference Scaling Through Resampling"; v1 was titled "Inference Scaling fLaws: The Limits of LLM Resampling with Imperfect Verifiers"). Inspected: full text v3 (26 March 2026), abstract, Sections 1 and 3, Appendix C. Use: closest prior work; their verifiers are unit tests on HumanEval+/MBPP+, and their population model has two task types.
- **brown2024**, **snell2024**, **cobbe2021**, **lightman2023**, **chen2024calls**, **schaeffer2025**, **wang2022**, **gao2022overopt**: identity via DataCite; abstracts read (arXiv API). Used only for what their abstracts state. Published venues (not used as versions of record because they carry no DOI): Snell et al. ICLR 2025; Lightman et al. ICLR 2024; Chen et al. NeurIPS 2024; Wang et al. ICLR 2023; Gao et al. ICML 2023.
- **chen2021**: Chen et al. (2021), arXiv:2107.03374. Identity: DataCite (58 authors). Inspected: Section 2.1 and Figure 3 (unbiased pass@k estimator; bias of the plug-in estimator).

## Self-evaluation by language models

- **kadavath2022**, **huang2023**, **stechly2024**, **panickssery2024**: identity via DataCite; abstracts read. Huang et al. appeared at ICLR 2024.

## Voting, redundancy, detection and estimation

- **condorcet1785**: identity checked against the archive.org scan (identifier essaisurlapplica00cond; Paris, Imprimerie Royale, 1785). The French text was not read for this paper; cited as the attribution of the jury theorem. `language: fr` prevents title-casing. The author is given as a literal string to keep the title of nobility intact.
- **boland1989**: Crossref identity (10.2307/2348873); pages 181–189 from Semantic Scholar; abstract read via OpenAlex.
- **ladha1992**: Crossref identity (10.2307/2111584); the end page could not be confirmed from an open registry, so no page range is given; abstract and opening text read via OpenAlex.
- **list2001**: Crossref identity; OpenAlex text is the article's opening, which does not state the plurality result. Cited as attribution only; no source claim.
- **vonneumann1956**, **moore1956**: Crossref identity; not read. Attributions only.
- **green1966**: OpenLibrary identity (Wiley, 1966; reprinted by Krieger, 1974). Not read; attribution for the separation of hit rate and false-alarm rate.
- **meehl1955**: Crossref identity; abstract read (OpenAlex).
- **ridout1999**: Crossref identity; abstract read. The ANOVA estimator used in simulation/pc/estimators.py is the standard one-way ANOVA estimator for equal cluster sizes; the paper does not attribute any specific numerical finding to Ridout et al.

## Human use of AI assistance and control of compute

- **noy2023**: Crossref identity and abstract.
- **brynjolfsson2025**: Crossref identity and abstract (published QJE version).
- **dellacqua2023**: Crossref identity for the SSRN working paper (10.2139/ssrn.4573321) and its abstract. A later journal version exists but was not located in Crossref and was not read; the paper cites only the working-paper abstract and does not report its outside-frontier effect size, whose unit (percent or percentage points) the abstract leaves unclear.
- **becker2025**: DataCite identity; full text v2 inspected (abstract, Section 1, Appendix C.1.4).
- **kwa2025**: DataCite identity; full text v4 (10 July 2026) inspected (abstract, Section 3.2.1). The journal-ref field gives NeurIPS 2025.
- **sastry2024**: DataCite identity; abstract read.
- **sen1985**: OpenLibrary identity (North-Holland, 1985, ISBN 0444877304). Not read for this paper; attribution only.

## Benchmark and pilot

- **gao2024omni**: DataCite identity; abstract read; dataset card and data file inspected at the pinned Hugging Face revision (licence Apache-2.0 as declared on the card). The problems originate from competitions; the licence is the dataset authors' declaration.
- **hendrycks2021**: DataCite identity; abstract not needed. Used only to name the source of the MATH-500 pilot items, with **lightman2023** for the 500-problem subset (openai/prm800k, MIT licence, commit 7ecc794703b2877f63226f2477a49b34f9b25163).

## Transcription notes

- No reference title contains arrows or other glyphs missing from the build font.
- Stroebl et al.'s current arXiv title differs from v1; the entry uses the title registered with DataCite.
