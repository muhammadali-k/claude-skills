---
name: outcomes-extraction
description: >-
  Extract time-to-event OUTCOME data — overall survival (OS), disease-free/progression-free survival
  (DFS/PFS), and recurrence-free survival (RFS) — from clinical-trial publications into per-comparison
  "outcome i-tables": one row per treatment-vs-control comparison with the hazard ratio + 95% CI,
  events/N per arm, and landmark survival rates, with provenance. Use whenever the user has an outcomes
  template (an `*_to_extract.xlsx` plus an `*_extraction_examples.xlsx`, often in OS/DFS/RFS folders) and
  reference PDFs and wants survival/recurrence results pulled in. Trigger on "extract OS/DFS/RFS", "pull
  the hazard ratios into the outcomes table", "fill the survival outcomes sheet", or "extract the effect
  estimates for these trials". Also covers RESPONSE outcomes — objective clinical/radiologic response and
  pathologic complete response (pCR) — which use an event/total-per-arm (relative-risk) layout instead of
  HR/CI. This is the OUTCOMES sibling of itable-extraction: prefer it for
  per-comparison effect-estimate tables (HR/CI/events/rates); use itable-extraction for wide baseline
  tables. Handles multi-arm trials (one row per comparison) and emits an upload-ready file plus a
  provenance workbook.
---

# Outcomes (OS / DFS / RFS) extraction

## What this is and why it's built this way

You are filling **effect-estimate tables** from trial publications. Each row is ONE pairwise comparison
(treatment vs control) for ONE endpoint, and holds the hazard ratio + 95% CI, the events and N in each
arm, and the landmark survival rate in each arm. There are usually three parallel tables — **OS**
(overall survival), **DFS** (disease-free / progression-free survival), **RFS** (recurrence-free
survival/interval) — with identical column layouts.

The hard parts are not typing numbers into cells. They are: (1) reading dense trial PDFs and KM
figures/forest plots correctly, (2) getting the **HR direction** right (treatment vs control, inverting
when the paper reports it the other way), (3) mapping each paper's reported endpoint to the right table
(papers rarely report a literal "RFS"), (4) giving **multi-arm trials the right number of rows**, and
(5) never fabricating values the sources don't report. A single pass by one agent tends to hallucinate
plausible-but-wrong numbers, mis-map arms, and silently drop comparisons. So the pipeline is built
around **independent verification** and **per-value provenance**: one agent extracts, a second
re-derives every value from the same sources and reconciles.

This skill is specialized for these per-comparison outcome tables. For wide baseline/population
characteristics tables, use the general `itable-extraction` skill instead.

## Inputs you will receive

- **`*_to_extract.xlsx`** per outcome (e.g. `OS/os_to_extract.xlsx`, `DFS/pfs_to_extract.xlsx`,
  `RFS/rfs_to_extract.xlsx`) — the deliverable to fill. Multi-row merged headers (rows 1–3), data from
  row 4. Cols A–F are pre-seeded study metadata; **col F ("Treatment Arm") is the comparison label that
  keys each row.** Data fields live in G–Y, identified by a `(ID: NNNN)` tag in the header.
- **`*_extraction_examples.xlsx`** per outcome — gold reference: reveals value formats, the missing-value
  convention, and exactly how multi-arm trials are split into rows. **Read it; it is calibration.**
- **A folder of reference publications** — full-text PDFs + supplements (`_suppl`, `_Sup`, `.docx`),
  one set per study.
- Often an **included-studies master file** (e.g. `HR_..._included_studies.xlsx`) whose abstracts give
  headline HRs/rates/events — invaluable anchors for building job specs and sanity-checking.

If which file maps to which study, or which comparison a row wants, is unclear, **ask** rather than
guess. A wrong file→row match or arm flip poisons a whole row.

## The pipeline (work in a `_work/` dir next to the tables)

### Phase 1 — Learn the layout and conventions
Run `scripts/inspect_tables.py <to_extract...> <examples...>` to dump merged headers, the `(ID: NNNN)`
field map, the pre-seeded rows, and example values. Then read **`references/table-layout.md`** (the
19-field G–Y layout, why you map by field ID not column letter, the per-table ID sets, the all-TEXT
rule) and **`references/conventions.md`** (the extractor brief: HR direction, landmark choice, O/F,
endpoint→table matching, multi-arm rows, missing values). Reconcile the brief against what the example
file actually does and confirm any project-specific calls with the user.

### Phase 2 — Decide the rows (CRITICAL — overall population only)
**Extract the OVERALL (ITT/full) population only, and default to ONE row per study.** Do NOT create
separate rows for biomarker/clinical SUBGROUPS (TNBC vs HR+, PD-L1±, Recurrence-Score groups, PAM50,
nodal/menopausal strata) and do NOT split one arm-comparison across several rows for different endpoints
— a 2-arm trial is exactly ONE row per table even when it reports the result by subgroup or across
several related endpoints. **The ONLY reason a study gets >1 row is a genuine multiple-ARM trial**
(≥2 experimental arms vs a common comparator): then one row per experimental-arm-vs-control comparison,
each in the overall population, distinguished by the col-F "Treatment Arm" label (e.g. a 3-arm trial gets
2 arm-vs-control rows). If the paper *pools* several arms into one primary comparison, that is ONE row —
flag the pooling. The to_extract file is often pre-seeded with only the "Primary" row, so per study
determine whether it is single-comparison (most) or genuinely multi-arm; add arm rows with
`scripts/add_rows.py` (see `references/workflow.md`). **The "Arms" column = the total number of arms in
the trial**, the same value on every row of that study — not the count in the pairwise comparison. See
`references/conventions.md` "OVERALL POPULATION ONLY" for the full rule.

### Phase 3 — Scaffold the job specs, then fill the judgment parts
Run `scripts/scaffold.py --sources <refs_dir> --out-dir _work OS=<os.xlsx> DFS=<dfs.xlsx> RFS=<rfs.xlsx>`.
It writes three skeletons into `_work/`: **`jobs.json`** (one entry per unique paper — its source files
matched by author+year, plus the needed `(table, comparison)` tuples auto-collected from the pre-seeded
rows), **`assemble_config.json`**, and **`add_rows_config.json`**. This absorbs the error-prone plumbing;
you then do only the parts that need judgment:
- **Review the file-match flags it prints** and fix any — an ambiguous match, a main text named by a
  different year (e.g. by submission year), or a supplement-only match where the main text wasn't found.
  A wrong file→paper match poisons a whole row, so confirm them.
- For each paper, fill the `design` note (headline HRs/rates/events from the abstract make great anchors)
  and the default `treatment`/`control` arms.
- Resolve `.docx` supplements to text first (`textutil -convert txt` on macOS) and point the job at the txt.

The jobs schema + a worked example are in `references/workflow.md`.

### Phase 4 — Multi-agent extract + verify (the core)
Run `assets/extract_outcomes.js` with the Workflow tool, passing `jobs` via `args` (workflow scripts
can't read files; the agents they spawn can). Per paper: an **extractor** reads the matched sources and
emits each required result with provenance; an **independent verifier** then **re-opens and re-reads
EVERY source PDF and supplement IN FULL, from scratch** — it does NOT trust the extractor's quoted
snippets or a partial/cached read, and it consults all the PDFs again even when that costs more tokens
(this is deliberate — the token spend is the price of a trustworthy check). It re-derives every value,
fixes HR direction / arm mapping / endpoint / denominators, recovers values the extractor missed, and
reconciles. Many CIs and HRs live ONLY inside KM-curve or forest-plot **images** the text layer can't
surface — the verifier renders/OCRs those figures rather than concluding "not reported" from a text dump.
Full orchestration, prompts, and JSON schemas are in `references/workflow.md` — read it before launching.
Save the workflow's returned `{papers:[...]}` to `_work/extraction_results.json`.

If the Workflow tool isn't available in your context (e.g. you are yourself a sub-agent), run the same
two roles **inline**, one paper at a time: extract every required value with provenance, then
independently re-derive and reconcile each one. The orchestration mechanism doesn't matter — the
sources-only + independent-verification + provenance discipline is what makes the output trustworthy.

### Phase 5 — Assemble into the sheets
Run `scripts/assemble.py --config _work/assemble_config.json` (config = file paths + a `study_info` map
of trial name / NCT / PMID / arm-count per paper). It backs up each file, maps every result to the right
cell **by header role** (robust to the example/to_extract column-order difference), writes all data cells
as **TEXT** with `NA` for anything unreported, and emits a provenance workbook (`*_provenance.xlsx`:
sources, flags, verifier changes, long-format).

### Phase 6 — QC
Run `scripts/qc.py <filled files...>`: confirms 25 columns + intact headers, **no empty data cell**,
NA-rate per column, **HR sanity** (lower ≤ HR ≤ upper), and **internal consistency** — a row with a
95% CI but **no TE** is impossible to *report* and is almost always a survival-RATE CI mis-placed into
the HR-CI columns (move it back onto the rate; the rate's CI is not the HR's CI), while a TE with **no
CI** is either genuine (too few events) or an image-only CI the text layer missed — re-read the figure
before accepting it as unreported. Then hand the user the filled files, the
provenance workbook, and a short summary of fill-rates and every flagged judgment call (arm flips,
HR inversions, endpoint substitutions, figure-read values, descriptive-only HRs). **Surface judgment
calls — don't bury them.**

## The conventions that make this trustworthy (full detail in `references/conventions.md`)
- **HR = treatment vs control** (experimental arm in the numerator). If the paper reports the reciprocal,
  invert: HR′ = 1/HR, new CI = (1/upper, 1/lower); flag it.
- **Endpoint → table by name, with flagged fallback.** OS→OS; DFS/iDFS→DFS; RFS table prefers
  RFS → RFI → BCFI → distant-recurrence; if only a broad composite exists, NA the effect cells and flag.
- **Survival-rate cells = event-free % at the longest/headline landmark** (record the timepoint in
  provenance), NOT cumulative incidence — convert 100−incidence if that's all that's given.
- **O/F = Original vs Follow-up** publication (judgment call; flag each).
- **Median survival ≈ always NA** in adjuvant trials (not reached).
- **All G–Y cells are TEXT**, so `NA` is valid everywhere; missing → `NA`.
- **Response & pCR tables are a DIFFERENT template.** Objective clinical/radiologic response and
  pathologic complete response (pCR) are extracted as **events/total per arm** (for a relative risk), NOT
  as HR + CI. A **single-arm, pooled, or converging-design** trial (window-of-opportunity / lead-in where
  all arms collapse to one regimen) legitimately reports **one arm only** — genuine missingness, not an
  incomplete extraction. Per-arm responder counts often live only in a **supplement** (main text may give
  just a pooled "X% in both arms") — fetch it before settling for NA. Match whichever template the
  `*_to_extract` / example file uses; see `references/conventions.md`.

## Scaling the rigor
Dual extract + verify + provenance is the default, and **verification always re-consults all the source
PDFs in full** — never a shortcut, never a trust of the extractor's notes, even though it costs more tokens. For a one-off single study you may collapse to a
single extractor + spot-check — but say so. For many studies the Workflow tool pipelines papers
concurrently; that's the normal mode.

## Files in this skill
- `scripts/scaffold.py` — match sources to studies and emit jobs.json + assemble/add_rows config skeletons
- `scripts/inspect_tables.py` — dump layout, field-ID map, rows, and example values for any tables
- `scripts/assemble.py` — write results into the sheets by header role (backup, NA-fill, provenance)
- `scripts/add_rows.py` — insert multi-arm comparison rows contiguously (grouped by study)
- `scripts/qc.py` — structure + no-empty + HR-sanity + fill-rate checks
- `assets/extract_outcomes.js` — the dual extract+verify Workflow script (parameterized via `args`)
- `references/table-layout.md` — the G–Y field layout, map-by-ID rule, per-table ID sets, data types
- `references/conventions.md` — extractor brief: HR direction, landmark, O/F, endpoint→table, multi-arm
- `references/workflow.md` — orchestration: jobs.json schema, agent prompts, output schemas, configs
