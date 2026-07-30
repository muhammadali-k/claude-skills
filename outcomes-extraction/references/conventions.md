# Extraction conventions (reviewer brief)

This is the brief both independent reviewers and the senior adjudicator work from. It is a **starting
template** — reconcile each rule against what the seeded/example rows in the actual template do, and
confirm project-specific calls with the user, before extracting.

## Know which template family you are filling — BEFORE you read a number
Three families, three different meanings for the same-looking columns (full layouts in
`table-layout.md`):

| Family | Row identity | Population | Counts columns |
|---|---|---|---|
| `pwma` | study × comparison | **overall / ITT only** | Et, Nt, Ec, Nc |
| `nma` | study × comparison | **overall / ITT only** | Ec T1, Et T1, Ec T2, Et T2 |
| `pwma_subgroup` | study × comparison × **subgroup level** | one row per subgroup level | Et, Nt, Ec, Nc |

Every job item states its `family`. If it doesn't, stop and ask — you cannot fill counts correctly
without knowing which family the row belongs to.

## ⚠️ THE `Ec` / `Et` TRAP — read this before writing any count ⚠️

```
pwma / pwma_subgroup     Et = EVENTS in treatment     Nt = N in treatment
                         Ec = EVENTS in control       Nc = N in control

nma                      Ec T1 = EVENT COUNT in T1    Et T1 = EVENT TOTAL (participants) in T1
                         Ec T2 = EVENT COUNT in T2    Et T2 = EVENT TOTAL (participants) in T2
```

**`Et` is an event COUNT in pwma and a participant TOTAL in nma.** Carrying one convention into the
other swaps numerator and denominator; the row still looks plausible and nothing downstream catches
it. Guardrails:

- **The result JSON always uses PWMA semantics, in every family.** You return `et` = events in
  treatment, `nt` = N in treatment, `ec` = events in control, `nc` = N in control — *even for an NMA
  row*. `assemble.py` does the NMA relabelling (events → `Ec T?`, N → `Et T?`) once, at write time.
  Never re-map it yourself.
- **NMA arm semantics: T1 = the treatment arm, T2 = the active comparator** (usually the trial's
  control arm). So `treatment_name` → Regimen T1, `control_name` → Regimen T2, `et`/`nt` → T1's
  event count / total, `ec`/`nc` → T2's.
- **Denominators are intention-to-treat / as-randomised** in both families. If only an as-analysed
  (full analysis / evaluable) set is reported, use it and **flag the denominator choice**.
- The events count must never exceed its own arm's N. `scripts/qc.py` flags any row where it does and
  names the two columns to swap — if that check fires, a convention was crossed.

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

## The senior re-reads everything (do not shortcut)
The senior adjudicator **re-opens and re-reads every source PDF and supplement IN FULL, from scratch,
before looking at either reviewer's draft** — every page, again — and re-derives every value,
including the ones both reviewers agreed on. It never relies on a reviewer's quoted snippets, a
cached/partial read, or "it's probably right". **Consult all the PDFs again even when it costs more
tokens — that token spend is the point.** Two failure modes this catches:
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

## ⚠️ Node labels — a controlled vocabulary, never the paper's own wording ⚠️

The `treatment_name` / `control_name` values are **node labels**, and `netmeta` joins arms by **string
equality**. "Nivolumab + Ipilimumab" and "Nivolumab plus iplimumab" become two nodes: the network
fragments, or keeps an edge that quietly vanished, or splits one regimen's evidence in half. Nothing in
the sheet looks wrong — the failure only appears in the league table. Long labels are the secondary
problem: a league table is an n×n grid of node names, and prose regimen names make it unreadable.

The project supplies a `*_node_vocabulary.json`; read it before extracting. The rules:

1. **Agent labels: UPPERCASE, 3–5 characters, no punctuation** — `SUN SOR PAZO AXI EVE PEM NIVO IPI
   ATEZO BELZ GIREN DURVA TREME`.
2. **Combinations join with a bare `+` and NO SPACES** — `NIVO+IPI`, never `NIVO + IPI`, `NIVO plus
   IPI`, `Nivo+Ipi`. Whitespace is forbidden outright rather than normalised: a trailing or
   non-breaking space pasted from a PDF is **visually identical** in a spreadsheet cell.
3. **Component order comes from the vocabulary's `combinations` list**, not from a rule you apply.
   "Backbone first" and "alphabetical" disagree; look the string up, don't derive it.
4. **The pooled comparator is ONE label** (default `NOADJ`) whatever the trial used — placebo,
   observation, surgery alone. What it actually was is recorded separately (`control_actual` in the
   vocabulary's `arms` map), so a blinding/control-type sensitivity analysis can still separate them.
   **Exception:** an add-on trial whose control is an **active regimen** gets that regimen's label, not
   `NOADJ` — that is what chains the add-on onto the right node instead of dangling it off the
   comparator.
5. **Dose, duration and setting variants are hyphen-suffixed and are part of the node identity** —
   `SOR-1Y SOR-3Y SOR-NEO PAZO-600 PAZO-800 NIVO-PERI`. Never reuse the base label for a variant; that
   silently merges two nodes.

**Emit the canonical label, never the trial's prose wording.** Where the paper's wording differs, use
the vocabulary's `aliases` mapping to get the canonical string. **Where no alias exists, FLAG it — do
not invent a label**, do not guess at a plausible abbreviation, and do not add it to the vocabulary
yourself. An unresolvable arm name is a decision for the reviewer who owns the vocabulary; a guessed
one is a phantom node.

`scripts/qc.py --vocabulary <file>` resolves every label in the filled sheet and **fails the run** on
any rejection; an alias hit passes but is reported as accepted-but-non-canonical. Full rationale and
the vocabulary-file shape are in `node-vocabulary.md`.

**What is *not* a node label:** the col-F (col-H on subgroup sheets) **"Treatment Arm" comparison
label** — `Primary`, `3 year Sorafenib` — is a **row key** copied verbatim from the sheet. Leave it
exactly as the sheet has it; re-writing it to a canonical label orphans the row. The vocabulary governs
`treatment_name` / `control_name` (the Treatment/Control and Regimen T1/T2 data columns) only.

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
  events matching `endpoint_used` for RFS). `nt`/`nc` = N per arm. **These four JSON keys carry the
  PWMA meaning in every family** — for an NMA row, `et`/`nt` are T1's events/participants and
  `ec`/`nc` are T2's; `assemble.py` writes them into `Ec T1 / Et T1 / Ec T2 / Et T2`. Prefer ITT /
  as-randomised denominators; if only an as-analysed (full analysis) set is given, use it and flag.
  Integers; `NA` if not reported. Sanity check before you commit: **events ≤ N, always.** A shared
  control arm across two comparisons of the same trial should show the **same** control events/N in
  both rows — another useful internal check.
- **Median survival** — almost always `NA` (not reached in adjuvant trials). Fill only if explicitly
  reported.
- **Arm names** — the **canonical node label from the project vocabulary** (`"NIVO+IPI"`, `"SOR-1Y"`,
  `"NOADJ"`), not the paper's prose (`"Nivolumab plus ipilimumab"`, `"one year sorafenib"`,
  `"Placebo"`). These columns are TEXT, so `+`, digits and hyphens are fine — but a space, a word
  joiner or a different capitalisation creates a second node. See "Node labels" above; if the paper's
  wording maps to no alias, flag it rather than inventing a label.

## O/F — Original vs Follow-up
`of` = **O** if this publication is the trial's original / pivotal efficacy report (or the only report of
that trial in the dataset), **F** if it is a long-term follow-up / "N-year update" / "follow-up analysis"
of an earlier-reported trial. This is a judgment call — decide from the title/abstract wording and **flag
it**. When an example file already codes a given study, match the example for that study.

## The row rule is CONDITIONAL ON TEMPLATE FAMILY

### Main sheets (`pwma`, `nma`) — OVERALL POPULATION ONLY
Extract outcomes for the trial's **overall / ITT (full) population ONLY**. Do **NOT** extract or create
separate rows for **biomarker or clinical SUBGROUPS** — e.g. risk groups, M1-NED vs M0, PD-L1+/−,
histology, nodal strata. On these sheets a subgroup HR/rate is never its own row.
- **One row per study** is the default. A 2-arm trial = exactly ONE row (treatment vs control), even when
  the paper reports that single comparison broken down by subgroup or across several related endpoints.
- **Do NOT split one comparison across multiple rows for different endpoints.** Within a table, pick the
  one overall endpoint that table wants (OS→overall survival; DFS table→the primary DFS/iDFS composite;
  RFS table→the single recurrence-specific endpoint) and emit ONE row — not one row for iDFS and another
  for distant-DFS of the same arm comparison.
- **The ONLY reason to have >1 row for a study is a genuine multiple-ARM trial** (≥2 experimental arms vs
  a common comparator) — then emit one row per experimental-arm-vs-control comparison (next section).
  Subgroups, sensitivity analyses, and multiple endpoints are NOT reasons for extra rows.

### Subgroup sheet (`pwma_subgroup`) — ONE ROW PER SUBGROUP LEVEL
This template exists **precisely to hold what the main sheets exclude.** The rule above is inverted,
not relaxed: here you emit **one row per (study × comparison × subgroup level)**, with the level named
in **col F "Subgroup"** and the comparison in **col H "Treatment Arm"**. Extract the effect estimate,
rates and counts **within that subgroup**, not the overall population.
- **The number of levels varies by study and by subgroup type.** Never assume a fixed set. The seeded
  Living-Periop-RCC sheet mostly uses four risk-group levels (`Risk group: High`,
  `Risk group: Intermediate-to-high`, `Risk group: M0 High`, `Risk group: M1 NED`), but one study
  carries two and another carries four levels for each of its two comparisons. The job spec tells you
  which levels are required for this study; produce exactly those.
- **Subgroup labels are copied verbatim** from the job spec / the pre-seeded col F, including the
  `Type: Level` form (`Risk group: M1 NED`). The label is part of the row key — a re-worded label
  silently creates a new row and orphans the intended one.
- **Never blend levels.** If the paper reports "intermediate-high and high combined" but the sheet asks
  for them separately, you cannot split it: mark both rows not extractable (below) and flag it. Do not
  put the combined estimate on one of them.
- **Counts still use the PWMA meaning** (Et = events treatment, Nt = N treatment, Ec = events control,
  Nc = N control) — the subgroup sheet is a `pwma` sheet with two extra left-hand columns.
- Denominators are the **subgroup's own** ITT N, not the trial's.

### "Extraction Possible" (col G, subgroup sheet only) — where an honest "no" goes
A subgroup result that the paper does not report is **common and expected**: a trial may report a
forest plot for two of four risk strata, or none at all. Record that fact rather than hiding it.
- Set `extraction_possible` = **`Yes`** when the subgroup result is reported and you extracted it.
- Set **`No`** when the paper does not report that subgroup at all, reports it only in a form that
  can't be used (combined with another level; a p-value for interaction with no per-level estimate;
  a figure too coarse to read), and set every data field on that row to `NA`.
- A `No` row is a **finding**, not a gap: it tells the analyst the interaction test can't include that
  level. Never leave the row blank, never delete it, and never invent a value to fill it.
- `qc.py` flags any row where the flag is unanswered, and any row that says `No` while still carrying
  an effect estimate.

## Multi-arm trials → one row per arm-comparison (overall population)
A trial with **≥2 experimental treatment arms** vs a common comparator contributes **one row per
experimental-arm-vs-control comparison**, each in the OVERALL population, distinguished by the
"Treatment Arm" label (col F on `pwma`/`nma`, **col H** on `pwma_subgroup`) — e.g. SORCE: "Primary"
(1-year sorafenib) AND "3 year Sorafenib". On the subgroup sheet each of those comparisons then gets
its own set of subgroup rows. If several experimental arms are **pooled by the paper** into a single primary comparison
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
  mark the `source` as a figure read so the senior double-checks, and note calibration; if unreadable,
  `NA`. Subgroup results in particular usually live **only** in a forest plot — render it.
- **A subgroup the paper never reports** → on the subgroup sheet that is `Extraction Possible = No`
  with the row `NA`'d, not an omission and not a question for a human.
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
