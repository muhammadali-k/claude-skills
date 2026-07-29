---
name: outcomes-extraction
description: >-
  Extract time-to-event OUTCOME data — overall survival (OS), disease-free/progression-free survival
  (DFS/PFS), and recurrence-free survival (RFS) — from clinical-trial publications into per-comparison
  "outcome i-tables": one row per treatment-vs-control comparison with the hazard ratio + 95% CI,
  events/N per arm, and landmark survival rates, with provenance. Use whenever the user has an outcomes
  template (a `pwma_template.xlsx` / `nma_template.xlsx` / `pwma_subgroup_template.xlsx`, or an
  `*_to_extract.xlsx` plus an `*_extraction_examples.xlsx`, often in PWMA/NMA or OS/DFS/RFS folders) and
  reference PDFs and wants survival/recurrence results pulled in. Trigger on "extract OS/DFS/RFS", "pull
  the hazard ratios into the outcomes table", "fill the survival outcomes sheet", "fill the NMA/pairwise
  sheet", "extract the subgroup results for the interaction analysis", or "extract the effect
  estimates for these trials". Also covers RESPONSE outcomes — objective clinical/radiologic response and
  pathologic complete response (pCR) — which use an event/total-per-arm (relative-risk) layout instead of
  HR/CI. Fills three template families — the PAIRWISE (PWMA) sheet, the NETWORK (NMA) sheet, and the
  PWMA SUBGROUP sheet (one row per subgroup level, for subgroup and interaction analyses). This is the
  OUTCOMES sibling of itable-extraction: prefer it for
  per-comparison effect-estimate tables (HR/CI/events/rates); use itable-extraction for wide baseline
  tables. Handles multi-arm trials (one row per comparison) and emits an upload-ready file plus a
  provenance workbook.
---

# Outcomes (OS / DFS / RFS) extraction

## What this is and why it's built this way

You are filling **effect-estimate tables** from trial publications. Each row is ONE pairwise comparison
(treatment vs control) for ONE endpoint — and, on the subgroup template, for ONE subgroup level — and
holds the hazard ratio + 95% CI, the events and N in each arm, and the landmark survival rate in each
arm. Tables usually come per endpoint (**OS**, **DFS**, **RFS**) and in up to three **template
families** (pairwise / network / subgroup) whose column layouts differ; see the next section.

The hard parts are not typing numbers into cells. They are: (1) reading dense trial PDFs and KM
figures/forest plots correctly, (2) getting the **HR direction** right (treatment vs control, inverting
when the paper reports it the other way), (3) mapping each paper's reported endpoint to the right table
(papers rarely report a literal "RFS"), (4) giving **multi-arm trials the right number of rows**,
(5) putting the right **population** in each row — overall ITT on the main sheets, the named stratum on
the subgroup sheet — and never letting the two mix, (6) writing the counts under the right convention
(the `Ec`/`Et` trap below), and (7) never fabricating values the sources don't report. A single pass by
one agent tends to hallucinate plausible-but-wrong numbers, mis-map arms, and silently drop comparisons.

So the pipeline mimics **the two-reviewer process of a real systematic review**: two reviewers extract
the same paper **independently**, neither seeing the other's work, and a **senior reviewer** then
re-derives every value from source and adjudicates. This is not the same as extract-then-check. A
verifier shown the first agent's answer anchors on it and rubber-stamps plausible errors; two reviewers
who commit independently produce genuinely separate readings, and their agreement or disagreement is
information you would not otherwise have.

**Concordance between the two reviewers is recorded, not trusted.** It measures how legible a value was
in the source, not whether it is correct — two readers can make the same mistake for the same reason,
and models sharing a base model make correlated errors. So the senior re-derives *every* value,
including the agreed ones, and the run reports how often it had to override both reviewers. That
number is the honest estimate of what a two-reviewer-only design would have gotten wrong.

This skill is specialized for these per-comparison outcome tables. For wide baseline/population
characteristics tables, use the general `itable-extraction` skill instead.

## The three template families (know which one you are filling)

| Family | File | Columns | Row identity | Population | What it feeds |
|---|---|---|---|---|---|
| `pwma` | `pwma_template.xlsx`, legacy `*_to_extract.xlsx` | A–Y | study × comparison | overall / ITT | **primary and sensitivity** pairwise meta-analysis |
| `nma` | `nma_template.xlsx` | A–X | study × comparison | overall / ITT | **primary and secondary** network meta-analysis |
| `pwma_subgroup` | `pwma_subgroup_template.xlsx` | A–AA | study × comparison × **subgroup level** | one row per level | **subgroup analysis** and **tests for interaction** in pairwise MA |

That last column is the project owner's stated intent: *the main PWMA and NMA sheets carry the primary
and sensitivity analyses for pairwise meta-analysis and the primary and secondary analyses for network
meta-analysis; the subgroup template is used when performing subgroup analysis in pairwise
meta-analysis and when testing for interaction between subgroups.* It is why the row rule differs by
family (Phase 2) and why a subgroup value must never be smuggled onto a main sheet.

**Each family has its own field-ID set** — NMA `21972–21993`, PWMA `3069–3089`, subgroup `9432–9452`,
legacy OS/DFS/RFS `3223–3287` — and the subgroup template inserts two columns that shift every data
field two letters right. That is precisely why every script maps **by field ID / header role and never
by column letter**. `scripts/families.py` detects the family from the header; nothing keys off a
filename.

## ⚠️ `Ec` AND `Et` MEAN DIFFERENT THINGS IN THE TWO LAYOUTS ⚠️

```
pwma / pwma_subgroup     Et = EVENTS in treatment     Nt = N in treatment
                         Ec = EVENTS in control       Nc = N in control

nma                      Ec T1 = EVENT COUNT in T1    Et T1 = EVENT TOTAL (participants) in T1
                         Ec T2 = EVENT COUNT in T2    Et T2 = EVENT TOTAL (participants) in T2
```

**`Et` is an event COUNT in PWMA and a PARTICIPANT TOTAL in NMA.** An extractor who carries one
convention into the other silently swaps numerator and denominator — and the output still looks
entirely plausible, so **nothing downstream catches it**; the pooled estimate is just wrong. In NMA,
**T1 = the treatment arm and T2 = the active comparator** (usually the trial's control arm), and both
denominators are intention-to-treat.

Three defences, already built in — do not work around them:
1. **The result JSON speaks only PWMA semantics**, in every family: `et`=events-treatment,
   `nt`=N-treatment, `ec`=events-control, `nc`=N-control. `assemble.py` performs the NMA relabelling
   (events → `Ec T?`, N → `Et T?`) once, at write time.
2. **`scripts/families.py` holds the one label→role table** and uses unambiguous internal names
   (`events_t`, `n_t`, `events_c`, `n_c`), so no other code has to know what "Et" means.
3. **`scripts/qc.py` flags any row where an event count exceeds its own arm's denominator**, per
   family, and names the two columns to swap. If that check fires, a convention was crossed.

If you hand-fill an NMA sheet, read the header out loud first: *Ec T1 is the number of events; Et T1
is the number of patients.*

## Inputs you will receive

- **The templates to fill** — `pwma_template.xlsx`, `nma_template.xlsx`,
  `pwma_subgroup_template.xlsx`, and/or the legacy per-outcome `*_to_extract.xlsx`
  (`OS/os_to_extract.xlsx`, `DFS/pfs_to_extract.xlsx`, `RFS/rfs_to_extract.xlsx`). All share the shape:
  sheet "Outcome Table", multi-row merged headers (rows 1–3), data from row 4, pre-seeded study
  metadata on the left, and data fields tagged `(ID: NNNN)` in the header. **Which columns are which
  differs by family** — run `inspect_tables.py` and read `references/table-layout.md`; don't assume.
- **Seeded / example rows** — either a separate `*_extraction_examples.xlsx` or already-filled rows in
  the template itself (the PWMA template ships with 15 filled rows). They reveal value formats, the
  missing-value convention, and how multi-arm trials are split. **Read them; they are calibration** —
  but treat obvious seed noise (a DOI sitting in the NCT or PMID column, an author name in O/F) as
  noise, not as a convention to copy.
- **A folder of reference publications** — full-text PDFs + supplements (`_suppl`, `_Sup`, `.docx`),
  one set per study.
- Often an **included-studies master file** (e.g. `HR_..._included_studies.xlsx`) whose abstracts give
  headline HRs/rates/events — invaluable anchors for building job specs and sanity-checking.

If which file maps to which study, which comparison a row wants, or which subgroup levels are required,
is unclear, **ask** rather than guess. A wrong file→row match, arm flip, or mis-keyed subgroup label
poisons a whole row.

## The pipeline (work in a `_work/` dir next to the tables)

### Phase 1 — Identify the family, then learn the layout and conventions
Run `scripts/inspect_tables.py <template...>` on **every** file you were given. It prints the detected
**template family**, the role → column → field-ID map (resolving the NMA sheet's duplicate `T1`/`T2`
labels via their row-2 group banner), the counts semantics for that family, the pre-seeded rows, and —
for subgroup sheets — **the subgroup levels present per study**. Then read
**`references/table-layout.md`** (all three layouts, the two-column shift in the subgroup template, the
Ec/Et divergence, the all-TEXT rule) and **`references/conventions.md`** (the reviewer brief: HR
direction, landmark choice, O/F, endpoint→table matching, multi-arm rows, subgroup labels, the
"Extraction Possible" flag, missing values). Reconcile the brief against what the seeded rows actually
do and confirm any project-specific calls with the user.

### Phase 2 — Decide the rows (CRITICAL — the rule is CONDITIONAL ON FAMILY)

**Look up the family first. The two rules below contradict each other on purpose; applying the wrong
one to the wrong sheet is the single easiest way to ruin this deliverable.**

**(a) Main sheets — `pwma` and `nma` → OVERALL (ITT/full) population only, default ONE row per study.**
Do NOT create separate rows for biomarker/clinical SUBGROUPS (risk groups, M1-NED vs M0, PD-L1±,
histology, nodal strata) and do NOT split one arm-comparison across several rows for different
endpoints — a 2-arm trial is exactly ONE row per table even when it reports the result by subgroup or
across several related endpoints. **The ONLY reason a study gets >1 row is a genuine multiple-ARM
trial** (≥2 experimental arms vs a common comparator): then one row per experimental-arm-vs-control
comparison, each in the overall population, distinguished by the col-F "Treatment Arm" label (e.g. a
3-arm trial gets 2 arm-vs-control rows). If the paper *pools* several arms into one primary comparison,
that is ONE row — flag the pooling. These sheets are pre-seeded mostly with the "Primary" row, so per
study determine whether it is single-comparison (most) or genuinely multi-arm; add arm rows with
`scripts/add_rows.py`.

**(b) Subgroup sheet — `pwma_subgroup` → ONE row per (study × comparison × SUBGROUP LEVEL).**
Rule (a) is *inverted* here, not relaxed: this template exists to hold exactly what the main sheets
exclude. The level goes in **col F "Subgroup"**, the comparison in **col H "Treatment Arm"**, and the
effect/rates/counts are those **within that subgroup**, with the subgroup's own ITT denominators.
**The number of levels varies by study and by subgroup type — never hardcode it** (in the seeded
Living-Periop-RCC sheet most studies carry four risk-group levels, one carries two, and one carries
four levels for each of its two comparisons). Take the required levels from the sheet or the job spec,
copy the labels verbatim, and add rows with `scripts/add_rows.py`, which inserts a variable number per
study. Where a level genuinely can't be extracted, say so in **col G "Extraction Possible"** and `NA`
the row — see below.

**The two rules never mix.** A subgroup estimate never goes on a `pwma`/`nma` sheet, and an overall-ITT
estimate never goes on a subgroup row. If you find yourself wanting to do either, you have the wrong
target file.

**Both (a) and (b):** the **"Arms" column = the total number of arms in the trial**, the same value on
every row of that study — not the count in the pairwise comparison. Full rules in
`references/conventions.md` → "The row rule is CONDITIONAL ON TEMPLATE FAMILY".

**"Extraction Possible" (subgroup sheet, col G) is where an honest "no" goes.** Set `Yes` when the
subgroup result is reported and extracted; set `No` — with every data field `NA` — when the paper
doesn't report that level, reports it only combined with another, or gives only an interaction p-value.
A `No` row is a **finding** (it tells the analyst the interaction test can't include that level), not a
gap. Never leave the row blank, never delete it, never invent a value to fill it.

### Phase 3 — Scaffold the job specs, then fill the judgment parts
Run `scripts/scaffold.py --sources <refs_dir> --out-dir _work PWMA=<pwma.xlsx> NMA=<nma.xlsx>
SUB=<pwma_subgroup.xlsx>` (the table KEY is yours to choose; the FAMILY is detected from each file's
header). It writes three skeletons into `_work/`: **`jobs.json`** (one entry per unique paper — its
source files matched by author+year, plus the needed `(table, family, comparison, subgroup)` tuples
auto-collected from the pre-seeded rows), **`assemble_config.json`**, and **`add_rows_config.json`**.
It also prints the subgroup levels it found per study, so you can see the counts vary. This absorbs the
error-prone plumbing; you then do only the parts that need judgment:
- **Review the file-match flags it prints** and fix any — an ambiguous match, a main text named by a
  different year (e.g. by submission year), or a supplement-only match where the main text wasn't found.
  A wrong file→paper match poisons a whole row, so confirm them.
- For each paper, fill the `design` note (headline HRs/rates/events from the abstract make great anchors)
  and the default `treatment`/`control` arms (on `nma` items, treatment = T1, control = T2).
- **Check every `needed` item carries a `family`**, and every `pwma_subgroup` item a `subgroup` label
  copied verbatim. A reviewer without the family can't know whether it is extracting the ITT population
  or one stratum.
- Resolve `.docx` supplements to text first (`textutil -convert txt` on macOS) and point the job at the txt.

The jobs schema + a worked example are in `references/workflow.md`.

### Phase 4 — Two independent reviewers + senior adjudication (the core)
Run `assets/extract_outcomes.js` with the Workflow tool, passing `jobs` via `args` (workflow scripts
can't read files; the agents they spawn can). Three roles per paper:

- **Reviewer A and Reviewer B** extract the paper **concurrently and independently**, from the same
  sources, with the identical brief. Neither is told what the other found; neither ever sees the other's
  output. They run on **different models** so their failure modes differ — two instances of one model
  agree too easily. Each emits every required result with per-field provenance. Each item tells them
  its **template family**, so they know whether the row wants the ITT population or one subgroup level
  — and both write counts in the PWMA meaning regardless of family.
- **Concordance** is then computed **in code, not by an agent** — field-by-field, with numeric
  normalisation so "0.80" and "0.8" match and "NA"/"not reported" collapse. It is recorded as a metric
  and does **not** gate anything.
- **The senior reviewer** re-opens and re-reads **EVERY source PDF and supplement IN FULL, from scratch,
  before looking at either draft**, and re-derives **every value — including the ones both reviewers
  agreed on**. Only then does it compare against the two drafts and log an adjudication for every field
  where any of the three differ. Its values are what get written to the sheet.

The senior is pinned to a strong model (Opus by default) rather than inheriting the session model.
Adjudication means reading verbatim clinical trial text and quoting it back; a model with heavier
response filtering may decline or soften that, and a senior that hedges is worse than useless because
everything downstream trusts it.

Two rules the senior must not break. It must **not split the difference** between reviewers — it either
proves a value from source or declares it unresolved. And anything it genuinely cannot settle (ambiguous
printing, a figure too coarse to read, main text contradicting the supplement) goes to `unresolved[]`
for a **human**, with the cell left `NA`. An honest unresolved entry is a correct outcome; a fabricated
resolution is the worst one.

Many CIs and HRs live ONLY inside KM-curve or forest-plot **images** the text layer can't surface — all
three roles render and read those figures rather than concluding "not reported" from a text dump.

Full orchestration, prompts, JSON schemas, and the model-assignment config are in
`references/workflow.md` — read it before launching. Save the workflow's returned
`{papers:[...], run_metrics:{...}}` to `_work/extraction_results.json`, and **report `run_metrics` to
the user** — concordance rate, how often the senior overrode both reviewers, and the unresolved count.

If the Workflow tool isn't available in your context (e.g. you are yourself a sub-agent), run the same
three roles **inline**, one paper at a time — but preserve the independence: produce reviewer A's full
answer, then produce reviewer B's answer *without consulting A*, then adjudicate from source. The
orchestration mechanism doesn't matter; independent commitment before comparison is what makes the
concordance signal meaningful, and re-derivation from source is what makes the output trustworthy.

### Phase 5 — Assemble into the sheets
Run `scripts/assemble.py --config _work/assemble_config.json` (config = file paths + a `study_info` map
of trial name / NCT / PMID / arm-count per paper). It detects each file's family, backs the file up,
maps every result to the right cell **by header role** (never by column letter), **performs the NMA
Ec/Et relabelling at write time**, writes all data cells as **TEXT** with `NA` for anything unreported,
fills "Extraction Possible" on subgroup sheets, and emits a provenance workbook
(`outcomes_provenance.xlsx`: sources, flags, senior adjudications, unresolved-for-human items, and a
long-format sheet whose count columns are named unambiguously). Rows are matched on
(paper_id, table, comparison, **subgroup**), so a re-worded subgroup label shows up as
`NO RESULT MATCHED` rather than landing in the wrong row.

### Phase 6 — QC
Run `scripts/qc.py <filled files...>`. Per family it confirms the expected column count + intact
headers, **no empty data cell**, NA-rate per column, **effect sanity** (lower ≤ TE ≤ upper), and:
- **⚠️ EVENTS > DENOMINATOR** — the Ec/Et guard. Any row whose event count exceeds its own arm's N is
  reported with the two columns to swap. This is the one arithmetic fact a crossed convention always
  breaks, and it is the only automated defence against a PWMA↔NMA count swap. Never wave it through.
- **CI with no TE** — impossible to *report*, and almost always a survival-RATE CI mis-placed into the
  effect-CI columns (move it back onto the rate; the rate's CI is not the HR's CI). A TE with **no CI**
  is either genuine (too few events) or an image-only CI the text layer missed — re-read the figure
  before accepting it as unreported.
- **Subgroup sheets:** "Extraction Possible" unanswered, a `No` row that still carries an effect
  estimate, blank subgroup labels, and duplicate (study × comparison × subgroup) keys.

Then hand the user the filled files, the provenance workbook, and a short summary of fill-rates and
every flagged judgment call (arm flips, HR inversions, endpoint substitutions, figure-read values,
descriptive-only HRs, not-extractable subgroups). **Surface judgment calls — don't bury them.**

## The conventions that make this trustworthy (full detail in `references/conventions.md`)
- **HR = treatment vs control** (experimental arm in the numerator). If the paper reports the reciprocal,
  invert: HR′ = 1/HR, new CI = (1/upper, 1/lower); flag it.
- **Endpoint → table by name, with flagged fallback.** OS→OS; DFS/iDFS→DFS; RFS table prefers
  RFS → RFI → BCFI → distant-recurrence; if only a broad composite exists, NA the effect cells and flag.
- **Survival-rate cells = event-free % at the longest/headline landmark** (record the timepoint in
  provenance), NOT cumulative incidence — convert 100−incidence if that's all that's given.
- **O/F = Original vs Follow-up** publication (judgment call; flag each).
- **Median survival ≈ always NA** in adjuvant trials (not reached).
- **Counts: `et`/`nt`/`ec`/`nc` in the JSON always mean events-T / N-T / events-C / N-C**, in every
  family; the NMA sheet's `Ec`/`Et` relabelling happens only in `assemble.py`. Denominators are ITT.
- **Every data cell is TEXT**, so `NA` is valid everywhere; missing → `NA`. (The seeded sheets mix
  `NA`, `N/A`, `NR` and `NM`; write `NA` — `qc.py` recognises the variants when reading.)
- **Response & pCR tables are a DIFFERENT template.** Objective clinical/radiologic response and
  pathologic complete response (pCR) are extracted as **events/total per arm** (for a relative risk), NOT
  as HR + CI. A **single-arm, pooled, or converging-design** trial (window-of-opportunity / lead-in where
  all arms collapse to one regimen) legitimately reports **one arm only** — genuine missingness, not an
  incomplete extraction. Per-arm responder counts often live only in a **supplement** (main text may give
  just a pooled "X% in both arms") — fetch it before settling for NA. Match whichever template the
  `*_to_extract` / example file uses; see `references/conventions.md`.

## Scaling the rigor
Two independent reviewers + a senior who re-derives everything is the default, and **the senior always
re-consults all the source PDFs in full** — never a shortcut, never a trust of a reviewer's notes, even
though it costs more tokens. For a one-off single study you may collapse to one reviewer + a
source-checking senior — but say so. For many studies the Workflow tool pipelines papers concurrently;
that's the normal mode.

## Files in this skill
- `scripts/families.py` — template-family detection + the single label→role table (incl. the Ec/Et map)
- `scripts/scaffold.py` — match sources to studies and emit jobs.json + assemble/add_rows config skeletons
- `scripts/inspect_tables.py` — dump family, field-ID map, counts semantics, rows, subgroup levels
- `scripts/assemble.py` — write results into the sheets by header role (backup, NA-fill, provenance)
- `scripts/add_rows.py` — insert comparison rows, and a variable number of subgroup rows per study
- `scripts/qc.py` — structure + no-empty + effect-sanity + **events>denominator** + subgroup checks
- `assets/extract_outcomes.js` — the two-reviewer + senior-adjudicator Workflow script (via `args`)
- `references/table-layout.md` — all three layouts, map-by-ID rule, per-family ID sets, the Ec/Et trap
- `references/conventions.md` — reviewer brief: family-conditional row rule, HR direction, landmark,
  O/F, endpoint→table, multi-arm, subgroup labels, "Extraction Possible"
- `references/workflow.md` — orchestration: jobs.json schema, agent prompts, output schemas, configs
