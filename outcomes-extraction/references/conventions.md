# Extraction conventions (extractor brief)

This is the brief the extractor and verifier agents work from. It is a **starting template** — reconcile
each rule against what the `*_extraction_examples.xlsx` file actually does, and confirm project-specific
calls with the user, before extracting.

## Golden rules
1. **Provided sources only.** Extract strictly from the source documents for this study (main text +
   its supplements). If a value is not reported there, it is `NA` — never infer it from outside
   knowledge, other papers, or what "should" be true. Design/anchor notes only help you *locate* a value;
   you must still confirm it against the text/table/figure and cite it.
2. **Every non-NA value carries provenance** — a `source` (page/table/figure) plus a short verbatim
   snippet that proves it. No snippet → return `NA`.
3. **Flag every judgment call** — arm/direction changes, HR inversions, endpoint substitutions,
   figure-read values, denominator choices (ITT vs as-analysed), population caveats (e.g. "adapted"
   analyses, ER+ subgroups), and descriptive-only HRs.

## Verification re-reads everything (do not shortcut)
The verifier **re-opens and re-reads every source PDF and supplement IN FULL, independently** — every
page, again, from scratch. It never relies on the extractor's quoted snippets, a cached/partial read, or
"it's probably right". **Consult all the PDFs again even when it costs more tokens — that token spend is
the point.** Two failure modes this catches:
- **Image-only values.** Many HRs and 95% CIs appear ONLY inside KM-curve or forest-plot figures (and
  supplementary figures) that a text dump can't surface. Render/OCR the figure before concluding a value
  is "not reported".
- **A CI with no point estimate is a contradiction.** A reported 95% CI always implies a point estimate.
  If a row has lower/upper CI but no HR, you have almost certainly picked up a **survival-RATE** confidence
  interval and mis-filed it as the HR's CI — move it back onto the rate cell; the effect (HR) is `NA` only
  if the trial truly reports no between-arm hazard ratio (e.g. a single-arm/pooled cohort).

## Arm assignment & HR direction
- **Treatment = the experimental arm; Control = the standard/reference arm** (placebo, tamoxifen,
  shorter/standard duration, "no further therapy"). The `te`/`lower_ci`/`upper_ci` must be the hazard
  ratio of **treatment vs control** (treatment in the numerator).
- You'll be given a default treatment/control per comparison. Confirm it against the paper. If the paper
  reports the HR in the **opposite direction**, invert it: `HR' = 1/HR`, `lower' = 1/upper`,
  `upper' = 1/lower`; set treatment/control accordingly and **flag the inversion**.
- If a trial has no clear control (e.g. two active strategies), use the comparison the paper frames as
  primary and flag the choice.

## Endpoint → table matching (match the name; flag the fallback)
- **OS table** = overall survival (death from any cause).
- **DFS table** = disease-free / invasive-DFS / progression-free survival (the recurrence + second
  primary + death composite). Use the paper's DFS-type composite; note `endpoint_used`.
- **RFS table** = a recurrence-specific endpoint. Preference order: **RFS → RFI (recurrence-free
  interval) → BCFI (breast cancer-free interval) → distant-recurrence-free**. Use the closest available,
  set `endpoint_used` to its exact name, and **flag the substitution**. If the paper reports ONLY a broad
  composite (DFS/iDFS/EFS) and no recurrence-specific endpoint, set the RFS effect cells (`hr`/CI/rates/
  events) to `NA` and flag "no recurrence-specific endpoint reported" — do not silently copy the DFS HR.

## Value formats
- **HR / CI** — decimals exactly as reported (`"0.82"`, `"0.69"`, `"0.98"`). `NA` if not reported.
- **Survival-rate cells (`surv_t`/`surv_c`)** — the event-free percentage at the **longest / headline
  landmark** the paper emphasizes for that endpoint (e.g. 8-, 10-, 12-year). Put the timepoint in
  `surv_timepoint` and cite it. Bare number, no "%". If the paper gives **cumulative incidence** of
  events instead of an event-free rate, report `100 − incidence` and flag the conversion. `NA` if not
  reported.
- **Events / N** — `et`/`ec` = events in treatment/control (deaths for OS; DFS events; the recurrence
  events matching `endpoint_used` for RFS). `nt`/`nc` = N per arm. Prefer ITT / as-randomised
  denominators; if only an as-analysed (full analysis) set is given, use it and flag. Integers; `NA`
  if not reported. A shared control arm across two comparisons of the same trial should show the **same**
  control events/N in both rows — a useful internal check.
- **Median survival** — almost always `NA` (not reached in adjuvant trials). Fill only if explicitly
  reported.
- **Arm names** — short labels as the paper names them (`"Tamoxifen plus ovarian function suppression"`,
  `"Letrozole"`, `"Placebo"`). These columns are TEXT, so `+`, digits, and parentheses are fine.

## O/F — Original vs Follow-up
`of` = **O** if this publication is the trial's original / pivotal efficacy report (or the only report of
that trial in the dataset), **F** if it is a long-term follow-up / "N-year update" / "follow-up analysis"
of an earlier-reported trial. This is a judgment call — decide from the title/abstract wording and **flag
it**. When an example file already codes a given study, match the example for that study.

## OVERALL POPULATION ONLY — one row per study (the critical rule)
Extract outcomes for the trial's **overall / ITT (full) population ONLY**. Do **NOT** extract or create
separate rows for **biomarker or clinical SUBGROUPS** — e.g. TNBC vs HR+, PD-L1+/−, Recurrence-Score
groups, PAM50/luminal subtypes, nodal/menopausal strata. A subgroup HR/rate is never its own row.
- **One row per study** is the default. A 2-arm trial = exactly ONE row (treatment vs control), even when
  the paper reports that single comparison broken down by subgroup or across several related endpoints.
- **Do NOT split one comparison across multiple rows for different endpoints.** Within a table, pick the
  one overall endpoint that table wants (OS→overall survival; DFS table→the primary DFS/iDFS composite;
  RFS table→the single recurrence-specific endpoint) and emit ONE row — not one row for iDFS and another
  for distant-DFS of the same arm comparison.
- **The ONLY reason to have >1 row for a study is a genuine multiple-ARM trial** (≥2 experimental arms vs
  a common comparator) — then emit one row per experimental-arm-vs-control comparison (next section).
  Subgroups, sensitivity analyses, and multiple endpoints are NOT reasons for extra rows.

## Multi-arm trials → one row per arm-comparison (overall population)
A trial with **≥2 experimental treatment arms** vs a common comparator contributes **one row per
experimental-arm-vs-control comparison**, each in the OVERALL population, distinguished by the col-F
"Treatment Arm" label (e.g. ALTERNATE: "fulvestrant vs anastrozole" AND "anastrozole+fulvestrant vs
anastrozole"). If several experimental arms are **pooled by the paper** into a single primary comparison
(e.g. PALLET pools 3 palbociclib+letrozole sequencing arms into one "palbociclib+letrozole" group vs
letrozole), that is ONE comparison → ONE row; flag the pooling. Key cautions, learned the hard way:
- **Only comparisons with a reported HR can be filled.** If the trial's multi-arm result is a *global*
  test (e.g. a 3-way log-rank p-value with no pairwise HRs), or the pairwise HR is labelled "for
  description only", flag it and confirm with the user before adding such a row.
- **A comparison may exist for one endpoint but not another.** A trial can report a between-arm HR for
  DFS but only a global p for OS — so the OS table may legitimately have fewer rows than DFS.
- **A later follow-up may report fewer comparisons** than the original (e.g. a long-term paper that
  reports only the monotherapy comparison, with sequential arms shown as descriptive rates) — don't
  invent rows the *publication* doesn't support.
- The **"Arms" field is the trial's total arm count**, identical on every row of that study — it is not
  the number of arms in the pairwise comparison.

## Common honest "missing" cases (expected, not errors)
- **QoL / dosing-schedule / supportive-care trials** that report no survival or recurrence outcome →
  fill arm names + N where given, `NA` the effect cells, and flag (the survival result may live in a
  separate primary publication not provided).
- **Effect estimate only in a figure** (KM landmark, forest plot with no printed numeric HR) → read it,
  mark the `source` as a figure read so the verifier double-checks, and note calibration; if unreadable,
  `NA`.
- **Long-term follow-ups** that omit per-arm event counts (report only a pooled total or cumulative
  incidence) → fill what's reported, `NA` the rest, flag.

## Response & pathologic-complete-response (pCR) outcomes — a different (event/total) template
Some projects also extract **objective response** (clinical and/or radiologic response; ORR = CR+PR) and
**pathologic complete response (pCR)** — common in neoadjuvant trials. These use a **relative-risk**
layout, NOT HR/CI: per arm, the number of **events** (responders / pCRs) and the **total evaluable**
(`event_t`/`total_t` for treatment, `event_c`/`total_c` for control). Rules:
- **Clinical response is usually inclusive of radiological response** — use the headline objective-response
  measure the trial reports; record which (clinical exam vs imaging/RECIST) and the timepoint.
- **Denominator = evaluable N for that response** (often < randomised N — exclude not-evaluable / no-surgery
  patients). The per-arm responder count must be out of that evaluable N, and the trial's reported % should
  reproduce from event/total.
- **Both arms are required to compute a relative risk.** If one arm is filled and the other is blank, check
  whether a comparator genuinely exists: **single-arm, pooled, or converging-design** trials report one arm
  with no control (genuine — flag, no RR computable); otherwise the missing arm is an extraction gap to fix.
- **Per-arm counts often live only in a supplement** — if the main text gives just a pooled "X% in both
  arms", the per-arm split is usually in a supplementary table; fetch it before settling for `NA`.
- The endpoint→table, multi-arm-rows, overall-population-only, and provenance rules above all still apply.
