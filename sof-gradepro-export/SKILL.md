---
name: sof-gradepro-export
description: >-
  Converts the internal system's per-outcome Summary-of-Findings (SoF) Excel export — one .xlsx per
  outcome, or a folder of them for one PICO/clinical question — into a single combined GRADEpro-GDT-format
  JSON-LD file, ready to import via MAGICapp's Evidence tab → Add PICO → "Import PICO using a GDT
  Gradepro file" beta feature. Use whenever the user hands over one or more SoF exports (filenames like
  `DFS_(Arm1_vs_Arm2)_Stratum_YYYYMMDD_HHMM.xlsx`) and wants a GDT import file, or asks to "combine these
  outcome exports into one PICO", "build a GRADEpro import file", or "convert this SoF export for
  MAGICapp" — even a bare folder of .xlsx files. Along the way it generates a GRADE-conventions
  plain-language summary and a recommended "Direction of benefit" per outcome (certainty-keyed verb,
  magnitude classification, the null-crossing hedge), and computes the absolute-effect confidence interval
  using the same formula confirmed live against MAGICapp's own "Calculate estimates" feature — since
  MAGICapp's beta GDT importer is confirmed, by live testing, not to set any of these three on import even
  though it does import the two values needed to compute them. Always writes a companion post-import
  checklist for the required one-click-per-outcome manual step. Parses HR/RR/OR and both risk-difference
  directions generically. Not for extracting data out of trial PDFs — that's itable-extraction/
  outcomes-extraction; this skill starts downstream, from an already-produced SoF export.
---

# SoF → GRADEpro GDT export

## What this does and why it works this way

The user's internal system exports one Summary-of-Findings table per outcome/comparison as a small,
rigidly-shaped `.xlsx` — a single "Summary of Findings" sheet, one data row per outcome, headers that
carry the relative effect, the two arms' absolute rates, the signed risk difference, and an overall GRADE
certainty rating. MAGICapp (the guideline-building tool) can import a whole PICO's worth of outcomes at
once, but only from a **GRADEpro GDT JSON-LD file** — a completely different, much richer schema that
groups every outcome under one PICO and expects fields (per-arm N, GRADE domain ratings, a study design)
the source Excel simply does not contain.

This skill is the converter in between: it reads one or many of the per-outcome exports, reshapes them
into one combined GDT JSON-LD document, computes what can be honestly computed (the absolute-effect CI —
see below), and — because GRADE evidence tables are expected to carry a plain-language interpretation and
this export format has no such column — synthesizes one deterministically, using the certainty→verb and
magnitude-classification conventions from `references/plain_language_conventions.md`. No field is invented
that the source doesn't support: where the target schema wants something this Excel format cannot honestly
provide (arm sizes, GRADE domain sub-ratings), the converter leaves it null rather than guessing a
plausible-looking number. Every one of those gaps is catalogued in `references/schema_mapping.md` — read it
before treating the output as complete.

**Live-verified against a real MAGICapp import**, not just built from documentation: this skill's JSON-LD
output was actually imported through the beta "Import PICO using a GDT Gradepro file" feature into a real
guideline. Population/intervention/comparator, the outcome name, the relative effect (with CI), the control
arm's risk, and the certainty label all imported correctly. Three things did not, and cannot currently be
made to via the JSON-LD file alone — see "The three things MAGICapp won't set on import" below.

## Inputs you will receive

- **One `.xlsx` file** — a single outcome/comparison's SoF export. Confirmed structure: sheet "Summary of
  Findings" (or the first sheet, as a fallback), merged headers in rows 1–2 (`Outcomes` / `Relative` /
  `Absolute` → `Intervention`/`Control`/`Risk Difference` / `Certainty of Evidence` / `Citations`), one
  data record starting the row after the header merge, with citations beyond the first overflowing one
  per row below the record (other columns blank on those rows).
- **A folder of many such `.xlsx` files** — all outcomes belonging to the *same* PICO/clinical question
  (same population, intervention, comparator). Every `.xlsx` directly inside the folder becomes one
  outcome in the combined output, processed in filename-sorted order. Files whose names start with `~$`
  or `.` (Excel lock files, hidden files) are skipped automatically.
- **The PICO in words** — population, intervention, and comparator as plain text, supplied via CLI flags
  (the source Excel never states these; they only appear, informally, in the filename).

The converter validates the layout as it parses (header columns found by keyword, not hardcoded letters)
and fails with an actionable message — naming the file and the cell it couldn't parse — on anything that
doesn't match the confirmed shape, rather than silently emitting a malformed row.

## Running the converter

```
python3 scripts/sof_to_gdt.py <xlsx-file-or-folder> \
  --population "..." --intervention "..." --comparator "..." \
  [--title "..."] [--sof-title "..."] [--outcome-name "..."] \
  [--mid-small PCT] [--mid-moderate PCT] [--mid-large PCT] \
  [--favorable-direction reduction|increase] [--no-pls] \
  -o <output.json>
```

- `<xlsx-file-or-folder>` — one outcome's `.xlsx`, or a folder of many. A single file still produces a
  fully valid one-outcome JSON-LD (not an error case).
- `--population` / `--intervention` / `--comparator` — required; free text. These become
  `question.healthProblemOrPopulation.name.value`, `question.intervention.name`, and
  `question.comparison.name`.
- `--title` / `--sof-title` — optional. If omitted, a generic PICO-question-style title is generated from
  the three fields above (e.g. `"Should <intervention> vs. <comparator> be used for <population>?"`).
- `--outcome-name` — override the filename-derived display name for a **single-file** run; not valid with
  a folder input (a folder always needs one name per file).
- `--mid-small` / `--mid-moderate` / `--mid-large` — the trivial→small, small→moderate, and
  moderate→large boundaries (as a **relative % change**) used to classify effect magnitude for the
  generated plain-language sentences and the Direction-of-benefit recommendation. Default `5 / 20 / 40`.
  This is a documented, non-authoritative fallback (GRADE ties magnitude to an outcome-specific
  minimally-important-difference, which this CLI has no per-outcome slot for) — see
  `references/plain_language_conventions.md`. One shared threshold triple applies to every outcome in the run.
- `--favorable-direction` — which direction of the *event* rate is desirable, for the Direction-of-benefit
  recommendation. Default `reduction` — correct for this skill's v1 scope (OS/DFS/PFS/RFS-style
  time-to-event outcomes, where the event is death/progression/recurrence and a lower rate is good). Set to
  `increase` for the rare outcome where that's flipped. One shared value per run, not per-outcome — a
  documented limitation, same as the MID thresholds above.
- `--no-pls` — skip plain-language summary + Direction-of-benefit generation entirely (both the JSON
  `explanation` entries and the companion checklist). Generation is **on by default**.
- `-o` / `--output` — the combined JSON-LD's output path (required).

**Outputs, always both written together (unless `--no-pls`):**
- `<output.json>` — the combined GDT JSON-LD: one PICO, one `question.outcome` entry and one paired
  `evidenceSummary` entry per input file, same order, cross-referenced by `forOutcome.@id`.
- `<output-stem>_post_import_checklist.md` — one section per outcome, in the same order: the expected
  intervention-arm rate (for confirming, not guessing, what MAGICapp's own calculation should produce), the
  recommended Direction-of-benefit selection, and the plain-language sentence to paste in. Any outcome whose
  direction of effect the null-crossing rule could not resolve is marked `` `[NEEDS HUMAN REVIEW]` ``.

## What gets generated, what gets left null

- **Fully derived from the source cells:** the relative-effect type + point estimate + 95% CI (HR/RR/OR,
  parsed generically — an unrecognized prefix still converts, using the literal text as the type, with a
  printed warning rather than a hard failure), the signed absolute risk difference, the control-arm risk
  (converted to GDT's per-100 convention), the overall GRADE certainty label, and the study count (counted
  from the citation rows, cross-checked against the "N citations" text and reconciled with a warning on a
  mismatch rather than failing).
- **Computed, for HR/RR/OR outcomes:** the absolute-effect confidence interval
  (`effectSummary.absoluteEffect[0].confidenceIntervalFrom/To`) — using the standard relative-to-absolute
  risk transform, live-verified against MAGICapp's own "Calculate estimates" output (see "The three things
  MAGICapp won't set on import" below and `references/schema_mapping.md` for the formula and how it was
  confirmed). Left null for an unrecognized relative-effect prefix, same as before.
- **Defaulted to the safest generic value** because the source doesn't state it: study design (always
  "randomised trials"), and `controlRisk`'s own `@type` label (always `LowControlRisk` — confirmed
  cosmetic/arbitrary in the target schema, not a real judgment the converter is making).
- **Left null, on purpose — never a fabricated number:** per-arm patient counts (`patientGroup` N for
  both arms) and the four GRADE domain sub-ratings (risk of bias / inconsistency / indirectness /
  imprecision). None of these are derivable from this Excel format; inventing plausible-looking numbers for
  them would be worse than leaving them blank.
- **Not attempted at all:** structured bibliography/reference entries. The citation strings in the
  source's "Citations" column are free text with no confirmed target shape in this schema, so they inform
  only the `numberOfStudies` count — they are not written into any `reference`/`bibliography` field.

The full field-by-field mapping — every source cell, every constant, every `@type` literal the converter
emits, and the reasoning behind each null — is in `references/schema_mapping.md`. Read it before treating
the JSON output as complete; several of its `@type` values are extrapolated from the one confirmed
HR/DichotomousData sample and flagged there as unconfirmed for RR/OR outcomes.

## The three things MAGICapp won't set on import — live-verified, not assumed

A JSON-LD file from this converter was actually imported into a real MAGICapp guideline via the beta "Import
PICO using a GDT Gradepro file" feature to check what does and doesn't come through. Population,
intervention, comparator, outcome name, relative effect + CI, control-arm risk, and certainty all imported
correctly. Three things did not, and — confirmed by searching a genuine GRADEpro GDT export for any
auto-calculation or direction-related field (zero hits) — **cannot** currently be set via the JSON-LD file
at all, because GRADEpro's own schema has no term for any of them:

1. **The intervention-arm absolute rate** renders as a blank cell until you click **"Calculate estimates"**
   (or check "Auto-calculated") in that outcome's edit panel, under "Expected difference and result with
   intervention." This is a MAGICapp UI action that runs client-side from the control risk + relative
   effect — both of which *do* import correctly — so the click is fast and its result is verifiable against
   the checklist's expected value, not a guess.
2. **"Direction of benefit"** (Intervention favourable / Comparator favourable / No important difference /
   High uncertainty) is a MAGICapp-only field with no GRADEpro equivalent at all. The checklist tells you
   which value this skill's classification recommends for each outcome.
3. **The plain-language summary** field — MAGICapp's own help documentation independently confirms its GDT
   importer drops this regardless of what the source file contains (see `references/schema_mapping.md` §6).

All three are handled the same way: this skill computes the right answer and puts it in the companion
checklist, so working through it per outcome after import is a **fast confirm, not a blind fill-in**. See
`references/schema_mapping.md` for the reverse-engineered absolute-effect-CI formula and exactly how it was
verified.

## Plain-language summaries and Direction of benefit

The source Excel has no plain-language column, but GRADE evidence communication expects one, so this
skill generates it — deterministically, no LLM call, following the certainty→verb table and
CI-crosses-null decision rule from `references/plain_language_conventions.md` (itself distilled from GRADE
guidelines 26 / Santesso et al. 2020 and Cochrane Handbook Ch. 15). The **same decision tree** also drives
the Direction-of-benefit recommendation, so the two can never disagree with each other (e.g. a "may reduce,
but may also increase" hedge always pairs with "High uncertainty," never with a confident "Intervention
favourable").

Delivery, for both:
1. **Best-effort embedded in the JSON-LD** — the plain-language sentence is appended to the top-level
   `explanation[]` array, one item per outcome, carrying a non-standard `forOutcome` cross-reference back to
   that outcome's `@id`. This is **not a confirmed native slot** (see `references/schema_mapping.md` §6) —
   treat it as a courtesy, not a guarantee MAGICapp will surface it. Direction of benefit has no JSON slot
   attempted at all, for the same reason (no field exists to put it in).
2. **Always written to the companion `_post_import_checklist.md` file** — this is the reliable path for
   both.

Any outcome whose 95% CI crosses the null with an *important* effect plausible in **both** directions gets
a hedged plain-language sentence (per Cochrane Handbook §15.6.4's "mention both possibilities" rule),
"High uncertainty" for Direction of benefit, and a `[NEEDS HUMAN REVIEW]` flag in the checklist — always
read those before pasting them in.

## After conversion: importing into MAGICapp

In the guideline, go to the **Evidence tab → Add PICO → "Import PICO using a GDT Gradepro file"**. This is
explicitly a **beta** feature, and MAGICapp's own help article says to check the imported content
afterward — which matters more than usual here: work through `_post_import_checklist.md` for every outcome
(Calculate estimates, Direction of benefit, paste the plain-language sentence), and separately check the
fields this converter leaves null or default (arm sizes, study design, GRADE domain ratings — see
`references/schema_mapping.md`). Diagnostic-accuracy PICOs aren't supported by this import path at all —
not a concern here, since this skill only emits dichotomous/time-to-event outcomes (see the "Scope (v1)"
note at the top of `references/schema_mapping.md`). If the import itself fails, MAGICapp's help article
points to `support@magicevidence.org` or the in-app Contact Support feature — outside what this skill can
debug.

## Scaling the rigor

There's no multi-agent extract/verify pipeline here — the conversion itself is one deterministic script,
so rigor here means review depth, not agent count:
- **A single outcome:** skim the output JSON's one `evidenceSummary` entry against the source cells, and
  read its checklist entry.
- **A full PICO (a folder of outcomes):** read every entry flagged `[NEEDS HUMAN REVIEW]` in the checklist
  first — those are the CI-crosses-null, direction-undetermined cases GRADE itself says need a judgment
  call, not a formula. Sanity-check whether the default `--mid-small/--mid-moderate/--mid-large` bands
  (5/20/40% relative change) are reasonable for the specific outcomes in this PICO, since they are a
  documented non-authoritative fallback, not a real minimally-important-difference — and confirm
  `--favorable-direction` matches the outcomes' actual valence if any aren't the standard
  death/progression/recurrence-type event. After importing into MAGICapp, work through the checklist once
  per outcome (Calculate estimates, Direction of benefit, plain-language paste), then separately check the
  fields the converter left null or default.

## Files in this skill
- `scripts/sof_to_gdt.py` — the converter CLI: parses one or many SoF `.xlsx` files, builds the combined
  GDT JSON-LD (including the computed absolute-effect CI), generates plain-language summaries + Direction
  of benefit, and writes both output files.
- `references/schema_mapping.md` — field-by-field table: source Excel cell → target JSON-LD path, every
  constant/default the converter uses, exactly which fields are left null and why, the absolute-effect-CI
  transform formula and how it was live-verified, and the full account of what MAGICapp's beta importer
  does and doesn't set.
- `references/plain_language_conventions.md` — the GRADE plain-language summary + Direction-of-benefit
  rules the converter implements: the certainty→verb table, the magnitude-classification rule, the
  CI-crosses-null decision table, and worked (fictional) examples.
- `EVALUATION.md` — what's been checked (functional runs, an independent field-by-field recheck, and a
  real MAGICapp import) and what hasn't.
