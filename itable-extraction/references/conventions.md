# Extraction conventions (extractor brief)

This is the brief handed to the extractor and verifier agents. It is a **starting template** — when an
example file exists, reconcile each rule below with what the example actually does and overwrite the
finalized version into `_work/conventions.md`. The agents read that finalized file, not this one.

Fill cells by **column letter / id** using the column→meaning map in `_work/field_guide.md`.

## Golden rules (these are what make the output trustworthy)
1. **Provided sources only.** Extract strictly from the source documents supplied for this study (main
   text + its supplements). If a value is not reported there, **omit the cell** (it becomes the missing
   marker). Never infer from outside knowledge, other papers, or what "should" be true.
2. **Every emitted value needs provenance** — a `source` string giving page/table/figure plus a short
   verbatim snippet that proves the value. No snippet → don't emit it.
3. **Respect the column granularity.** Many evidence tables split a variable across sub-columns (per
   study arm, per subgroup, per timepoint). Put each number in the correct sub-column; don't collapse.
4. **Flag judgment calls.** Arm-mapping choices, figure-read values, denominator choices (ITT vs
   as-randomized), population/timepoint caveats — record each in `flags` so a human can check.

## Arm / comparator assignment (for trial tables with per-arm columns)
- The **standard treatment is ALWAYS the Control arm** (e.g. placebo, tamoxifen, no-further-therapy, the
  shorter/standard duration); experimental therapies go in Treatment 1, 2, ...
- If by any chance **all arms are experimental**, check whether the paper presents a comparison against
  one particular arm — if so, that arm is the Control.
- If all arms are experimental **and the paper is silent** about which arm the others are compared
  against, treat them all as treatment arms and leave Control as `NA`.
- You'll be given a *proposed* mapping per study — confirm it against the actual paper; if you change it,
  add a `flags` entry explaining why.

## Value formats (defaults; an example file overrides these)
- **Counts:** `N (%)`, e.g. `1848 (93.2)`. If only N or only % is reported, record what's there.
- **Medians / rates / ages / doses:** plain number. Convert durations to the unit the column names
  (e.g. years→months: `10.3 yr → 123.6`). "Not reached"/not reported → missing.
- **Survival/event RATE columns** (e.g. "OS rate % (at years)"): the percentage as a bare number; put the
  timepoint (e.g. "10-year") in the `source`. Map endpoints to the right row: DFS/PFS → the PFS/DFS row;
  DRFI/DDFS/DMFS → the MFS/distant row; RFI/locoregional → the RFS row; OS → the OS row.
- **Arm-name / category-label columns:** short label. **Caution:** many systems type these as
  letters-only (see `data_types.md`) — prefer plain words ("Tamoxifen plus OFS", "Anastrozole six years")
  over symbols/digits if the example shows letters-only values.
- **Identifiers:** registry/NCT id, PubMed id, etc. as the example formats them.
- **Endpoints:** comma-separated abbreviations as the paper names them (OS, DFS, DRFI, BCFI, RFI, ...).
- **Adverse events:** distinguish all-grade / grade ≥3 / grade 5 (fatal) and treatment-related vs
  all-cause as the table reports; `N` or `N (%)`. If not broken out, missing.

## The most common honest "missing" cases (expected, not errors)
- **Long-term follow-up reports usually omit baseline tables** — the demographics live in the original
  primary publication. If that primary paper is not in the provided sources, those baseline cells are
  legitimately missing. Do not pull them from memory.
- **Per-arm splits not reported** — if a baseline table reports a characteristic only overall (not by
  arm), leave the per-arm cells missing rather than spreading an overall figure into one arm's column.
- **Values only in figures** (KM-curve rates) — read them visually and mark the cell's `source` as a
  figure read so the verifier double-checks; if unreadable, missing.

## Output
Return the structured object the workflow expects (see `workflow.md`): identifiers, arm mapping, the list
of filled cells each with `{col, value, source}`, and `flags`. Be exhaustive but never fabricate.
