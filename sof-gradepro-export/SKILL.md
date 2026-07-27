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
  plain-language summary sentence per outcome (certainty-keyed verb, magnitude classification, the
  null-crossing hedge), since the source Excel has no such column, and always writes a companion file for
  manual pasting, since MAGICapp's importer is confirmed to drop plain-language content. Parses HR/RR/OR
  and both risk-difference directions generically. Not for extracting data out of trial PDFs — that's
  itable-extraction/outcomes-extraction; this skill starts downstream, from an already-produced SoF export.
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
into one combined GDT JSON-LD document, and — because GRADE evidence tables are expected to carry a
plain-language interpretation and this export format has no such column — synthesizes one deterministically,
using the certainty→verb and magnitude-classification conventions from `references/plain_language_conventions.md`.
No field is invented that the source doesn't support: where the target schema wants something this Excel
format cannot honestly provide (arm sizes, GRADE domain sub-ratings, the confidence interval on the
absolute effect), the converter leaves it null rather than guessing a plausible-looking number. Every one
of those gaps is catalogued in `references/schema_mapping.md` — read it before treating the output as
complete.

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
  [--mid-small PCT] [--mid-moderate PCT] [--mid-large PCT] [--no-pls] \
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
  generated plain-language sentences. Default `5 / 20 / 40`. This is a documented, non-authoritative
  fallback (GRADE ties magnitude to an outcome-specific minimally-important-difference, which this CLI has
  no per-outcome slot for) — see `references/plain_language_conventions.md`. One shared threshold triple
  applies to every outcome in the run.
- `--no-pls` — skip plain-language summary generation entirely (both the JSON `explanation` entries and
  the companion file). Generation is **on by default**.
- `-o` / `--output` — the combined JSON-LD's output path (required).

**Outputs, always both written together (unless `--no-pls`):**
- `<output.json>` — the combined GDT JSON-LD: one PICO, one `question.outcome` entry and one paired
  `evidenceSummary` entry per input file, same order, cross-referenced by `forOutcome.@id`.
- `<output-stem>_plain_language_summaries.md` — one section per outcome, in the same order, with any
  outcome whose direction of effect the null-crossing rule could not resolve marked
  `` `[NEEDS HUMAN REVIEW]` ``.

## What gets generated, what gets left null

- **Fully derived from the source cells:** the relative-effect type + point estimate + 95% CI (HR/RR/OR,
  parsed generically — an unrecognized prefix still converts, using the literal text as the type, with a
  printed warning rather than a hard failure), the signed absolute risk difference, the control-arm risk
  (converted to GDT's per-100 convention), the overall GRADE certainty label, and the study count (counted
  from the citation rows, cross-checked against the "N citations" text and reconciled with a warning on a
  mismatch rather than failing).
- **Defaulted to the safest generic value** because the source doesn't state it: study design (always
  "randomised trials"), and `controlRisk`'s own `@type` label (always `LowControlRisk` — confirmed
  cosmetic/arbitrary in the target schema, not a real judgment the converter is making).
- **Left null, on purpose — never a fabricated number:** per-arm patient counts (`patientGroup` N for
  both arms), the four GRADE domain sub-ratings (risk of bias / inconsistency / indirectness /
  imprecision), and the absolute effect's own confidence interval. None of these are derivable from this
  Excel format; inventing plausible-looking numbers for them would be worse than leaving them blank. The
  absolute-effect CI in particular is a deliberate design decision, not an oversight — see
  `references/schema_mapping.md` for exactly why it can't be back-computed from the three numbers Excel
  does give you.
- **Not attempted at all:** structured bibliography/reference entries. The citation strings in the
  source's "Citations" column are free text with no confirmed target shape in this schema, so they inform
  only the `numberOfStudies` count — they are not written into any `reference`/`bibliography` field.

The full field-by-field mapping — every source cell, every constant, every `@type` literal the converter
emits, and the reasoning behind each null — is in `references/schema_mapping.md`. Read it before treating
the JSON output as complete; several of its `@type` values are extrapolated from the one confirmed
HR/DichotomousData sample and flagged there as unconfirmed for RR/OR outcomes.

## Plain-language summaries

The source Excel has no plain-language column, but GRADE evidence communication expects one, so this
skill generates it — deterministically, no LLM call, following the certainty→verb table and
CI-crosses-null decision rule from `references/plain_language_conventions.md` (itself distilled from GRADE
guidelines 26 / Santesso et al. 2020 and Cochrane Handbook Ch. 15). Both delivery paths run by default:

1. **Best-effort embedded in the JSON-LD** — appended to the top-level `explanation[]` array, one item
   per outcome, carrying a non-standard `forOutcome` cross-reference back to that outcome's `@id`. This is
   **not a confirmed native slot** — the real GDT sample this skill was built against has exactly one
   PICO-level `explanation` item that nothing else references, and no documented per-outcome
   plain-language field exists in GRADEpro's own export schema. Treat this as a courtesy, not a guarantee
   MAGICapp will surface it.
2. **Always written to the companion `_plain_language_summaries.md` file** — this is the reliable path.
   MAGICapp's own help documentation confirms its GDT importer drops plain-language content regardless of
   where GRADEpro's export puts it, so plan on pasting these sentences into each outcome's own "Plain
   language summary" field in MAGICapp by hand after import.

Any outcome whose 95% CI crosses the null with an *important* effect plausible in **both** directions gets
a hedged sentence stating the direction is genuinely undetermined (per Cochrane Handbook §15.6.4's "mention
both possibilities" rule) and is flagged `[NEEDS HUMAN REVIEW]` in the companion file — always read those
before pasting them in.

## After conversion: importing into MAGICapp

In the guideline, go to the **Evidence tab → Add PICO → "Import PICO using a GDT Gradepro file"**. This is
explicitly a **beta** feature, and MAGICapp's own help article says to check the imported content
afterward — which matters more than usual here, because several fields this converter had to leave null or
default (arm sizes, GRADE domain ratings, absolute-effect CI, study design, and the plain-language summary
itself, which the importer drops entirely) will land in MAGICapp looking blank or generic and need a
manual pass. Diagnostic-accuracy PICOs aren't supported by this import path at all — not a concern here,
since this skill only emits dichotomous/time-to-event outcomes (see the "Scope (v1)" note at the top of
`references/schema_mapping.md`). If the import itself fails, MAGICapp's help article
points to `support@magicevidence.org` or the in-app Contact Support feature — outside what this skill can
debug.

## Scaling the rigor

There's no multi-agent extract/verify pipeline here — the conversion itself is one deterministic script,
so rigor here means review depth, not agent count:
- **A single outcome:** skim the output JSON's one `evidenceSummary` entry against the source cells, and
  read its plain-language sentence.
- **A full PICO (a folder of outcomes):** read every sentence flagged `[NEEDS HUMAN REVIEW]` in the
  companion file first — those are the CI-crosses-null, direction-undetermined cases GRADE itself says
  need a judgment call, not a formula. Sanity-check whether the default `--mid-small/--mid-moderate/--mid-large`
  bands (5/20/40% relative change) are reasonable for the specific outcomes in this PICO, since they are a
  documented non-authoritative fallback, not a real minimally-important-difference. After importing into
  MAGICapp, walk every outcome once to fill in the fields the converter left null and paste in its
  plain-language sentence.

## Files in this skill
- `scripts/sof_to_gdt.py` — the converter CLI: parses one or many SoF `.xlsx` files, builds the combined
  GDT JSON-LD, generates plain-language summaries, and writes both output files.
- `references/schema_mapping.md` — field-by-field table: source Excel cell → target JSON-LD path, every
  constant/default the converter uses, and exactly which fields are left null and why.
- `references/plain_language_conventions.md` — the GRADE plain-language summary rules the converter
  implements: the certainty→verb table, the magnitude-classification rule, the CI-crosses-null decision
  table, and worked (fictional) examples.
