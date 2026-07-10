# Profile: evidence synthesis — systematic reviews, pairwise & network meta-analysis

Applies to systematic reviews (with or without pooling), pairwise meta-analyses, and network
meta-analyses (including living / interactive reviews). This is the profile behind the ASH ruxolitinib-NMA
review. Read it alongside `../method.md`; sibling skill `manuscript-srma` has deeper drafting conventions
you can borrow for wording.

## What to scrutinize

### Completeness of the evidence base (highest yield)
- **Did the search miss an eligible study?** The single most consequential error. Check the databases
  searched vs. what's standard (MEDLINE/Embase/CENTRAL at minimum; Scopus/Web of Science optional). A
  MEDLINE/Scopus/CENTRAL-only search routinely misses trials that live mainly as **registry postings or
  congress abstracts** — ask whether trial registries (ClinicalTrials.gov, WHO ICTRP) and conference
  proceedings (ASH/ASCO/EHA) were searched. A negative/terminated add-on trial that is omitted is *not*
  neutral: it biases a shared-comparator network toward more favorable combination effects.
- **Eligibility applied consistently** — every included study meets the stated PICO; near-miss exclusions
  (e.g. a trial in second-line/suboptimal responders when the question is first-line/naive) are correctly
  reasoned. When you suspect a missing study, name it (registry ID) and ask for inclusion or an explicit
  exclusion rationale.
- **Protocol / reporting standard** — PROSPERO registration and PRISMA 2020 (or **PRISMA-NMA**) adherence.
  Often omitted in abstracts for space; note it, don't insist.

### Transitivity & network geometry `[NMA]`
- **Star-shaped network** (one common comparator, no head-to-head trials): every
  combination-vs-combination estimate is **indirect**, there are **no closed loops**, and statistical
  **inconsistency cannot be assessed** — so all between-arm inference rests entirely on the **transitivity
  assumption**. This must be stated as a limitation. (Adding this clause was a core fix in the ASH review.)
- **Effect modifiers across trials** — differences in eligibility (e.g. baseline platelet thresholds),
  risk-group mix (DIPSS), dosing, follow-up, and outcome-ascertainment can break transitivity. Reassuring
  features (all double-blind, same control arm, same symptom instrument) are worth acknowledging alongside
  the residual concerns.
- **Comparability of the outcome definition** — "response at any time" depends on each trial's imaging
  frequency and central-vs-local review and is less comparable than a protocol-defined landmark
  (e.g. week-24). Prefer/recommend the landmark definition.

### Model & statistics
- **Fixed vs. random effects** stated, with rationale. With **one trial per direct comparison**,
  between-study heterogeneity (τ²) **cannot be estimated** — a fixed-effect model is usually forced;
  say so.
- **Software/package** (e.g. R `netmeta`, `gemtc`, `BUGSnet`) and **effect measure** (RR/OR/HR/MD) named.
- **Sparse/zero-event handling** — continuity correction or equivalent, especially when toxicity CIs are
  very wide (a giveaway of few events, e.g. RR 5.26, 1.92–14.29). Flag if unstated.
- **Ranking metrics** — **P-scores / SUCRA** convey *ranking probability only*, not effect magnitude or
  certainty, and are unstable with few studies (values like 100%, 98%, 96% from three trials). Recommend
  framing rankings as **hypothesis-generating and secondary to the effect estimates and CIs**. Watch for
  a ranking being read as a clinical winner.

### Certainty & risk of bias
- **Risk of bias** (RoB 2 / ROBINS-I) and **certainty of evidence** (**GRADE / CINeMA for NMA**) are core
  PRISMA elements. Frequently dropped from abstracts — accept the omission if the author justifies it, but
  recommend at minimum one clause that between-combination comparisons are **low/very-low certainty owing
  to indirectness and imprecision**.

### Effect estimates & claims
- **Direction/sign conventions** — for continuous outcomes (mean differences), state which sign favors
  which arm so a positive MD isn't misread as benefit (e.g. a *lower/negative* symptom-score change =
  greater improvement).
- **Immature time-to-event data** — OS/PFS from early data cuts with few events: label **preliminary**,
  don't rank, and soften "significant benefit" when a CI touches the null or the result is one-sided /
  not alpha-protected (a co-primary endpoint miss removes alpha protection).
- **Data vintage consistency** — when estimates derive from a trial with multiple reports (a congress
  abstract then a full paper), confirm a **single, consistent vintage** across all outcomes from that
  trial; cytopenia rates in particular shift between data cuts.
- **Per-outcome contributing-study counts** — report how many trials inform each outcome; keep it parallel
  across outcomes so a silently-absent arm (no data for that outcome) is distinguishable from an
  oversight.

## Reporting-standard anchors
PRISMA 2020; **PRISMA-NMA** (Hutton 2015); PRISMA for Abstracts; GRADE and **CINeMA** for NMA certainty;
RoB 2 / ROBINS-I; Cochrane Handbook. For interactive/living reviews, the LIvE-synthesis conventions in
`manuscript-srma`.

## Edit vs. comment for this profile
- **Edits:** propagate a changed study/arm count everywhere (Intro/Results/Conclusion); fix a conclusion
  that claims "all X improved" after one didn't; add the transitivity/indirectness caveat clause; tighten
  ranking or significance wording; terminology/precision consistency.
- **Comments (flag, don't edit):** a suspected missing trial (with its registry ID); un-searched
  databases / no PROSPERO; unstated software or zero-cell handling; data values you can't verify (with the
  likely source/vintage); RoB/certainty omission; sign-convention clarification the author must word.

## Verify-before-asserting hot spots
Any specific trial result, effect estimate, or "trial X reported/omitted" claim needs external
verification (registry / publication) — and adversarial verification for consequential ones. Do **not**
edit a hazard ratio, CI bound, or event count you cannot confirm; comment and ask the author to verify.
