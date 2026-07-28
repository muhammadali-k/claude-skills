# Evaluation

No `evals/evals.json` yet (unlike `itable-extraction`/`outcomes-extraction`, which run a scored
with-skill-vs-baseline harness) — this is a single deterministic script, not a multi-agent pipeline, so
the highest-value check is direct verification of the script's output against hand-derived expected
values, not a prompt-grading harness. That verification is what's recorded below; a proper `evals.json` is
a reasonable future addition if this skill sees heavier use.

## What was verified

1. **Functional run** — single-file and folder-mode runs against real-shaped fixtures, confirming: exit
   code 0 on well-formed input, valid JSON output, both output files always written together, and clear
   `SystemExit` messages (naming the file and the unparseable cell) on malformed input.
2. **Independent field-by-field recheck** — a second, independent pass re-derived the expected converted
   values directly from a source spreadsheet's raw cells (without trusting the first pass's description of
   it) and compared every field against the script's actual output: relative-effect type/point/CI bounds,
   the signed absolute risk difference, `controlRisk.value`'s per-1000→per-100 conversion, the certainty
   label, and the study count. No sign errors, no swapped arms, no swapped CI bounds, no denominator
   confusion between `controlRisk` (per 100) and `absoluteEffect` (per 1000) were found.
3. **Plain-language wording spot-check** — the certainty→verb mapping and the CI-crosses-null hedging
   logic were checked against Cochrane Handbook Table 15.6.b / GRADE guidelines 26 (Santesso et al. 2020)
   directly, including the case where a wide CI makes direction of effect genuinely undetermined (the
   `[NEEDS HUMAN REVIEW]` flag) — confirmed the generator's "may … but may also …" phrasing in that case is
   the GRADE-conformant choice, not a certainty-mismatch bug, because direction itself (not just magnitude)
   is what's in question.
4. **Repo-safety sweep** — every committed file was searched for real trial data, real file paths, and
   real identifiers before commit; none found. Only fictional worked examples (invented drug/outcome names
   and numbers) appear anywhere in this skill's documentation and code comments.
5. **A real MAGICapp import** — the converter's JSON-LD output was actually uploaded through the beta
   "Import PICO using a GDT Gradepro file" feature into a real guideline (not just checked against
   documentation/schema). Population, intervention, comparator, outcome name, relative effect + CI,
   control-arm risk, and certainty all imported correctly. This live test is what surfaced the three items
   in "Known gaps" below, and what the absolute-effect-CI transform formula (§`schema_mapping.md`) was
   reverse-engineered and confirmed against — MAGICapp's own "Calculate estimates" button reproduced this
   script's independently-computed numbers almost exactly (matching to the expected rounding of the
   transform formula).

## Known gaps found during verification — all three confirmed by the live import, not just reasoned about

1. **Intervention-arm absolute rate** always renders blank in MAGICapp's outcome table immediately after
   import — confirmed live, not assumed. It requires one click on "Calculate estimates" per outcome (see
   SKILL.md). The source Excel's own stated value is parsed and surfaced in the post-import checklist so
   that click can be a confirm-the-number step, not a blind one.
2. **Direction of benefit** is never set by import (confirmed absent from a real GRADEpro GDT export
   entirely — there's no field for it in that schema, not something this skill failed to populate). A
   recommended value is computed and put in the checklist for manual selection.
3. **Plain-language summary** — confirmed both by MAGICapp's own help documentation and by the live import
   itself that this field is left blank regardless of what the JSON-LD contains.

None of these are bugs to fix by guessing harder — they're genuine platform-level gaps in what the beta
GDT-import path can currently set, documented in `references/schema_mapping.md` alongside exactly how each
was confirmed.

## What hasn't been verified

- The converter has only been run against **dichotomous / time-to-event** outcomes (the only type
  confirmed in both the source Excel format and the one real GDT sample this skill was built against).
  Continuous or non-poolable/narrative outcomes are out of scope for v1 — see the "Scope (v1)" note at the
  top of `references/schema_mapping.md`.
- The live import test used an **HR-type outcome**. The absolute-effect-CI transform's RR and OR branches
  (`relative_to_risk()` in `scripts/sof_to_gdt.py`) use the standard, textbook risk-ratio/odds-ratio
  formulas and were checked against hand-derived arithmetic, but — unlike the HR branch — were not
  independently cross-checked against a live MAGICapp "Calculate estimates" run for an RR or OR outcome.
  Treat the first real RR/OR import as the real test for those two.
- Several `@type` literals for RR/OR relative effects (as opposed to the confirmed HR case) are still
  extrapolated, not directly observed in a real sample.

## Scaling the rigor

For a one-off single outcome, the functional-run-only level of checking above is enough — skim the output
against the source cells. For a full PICO (a folder of many outcomes) being imported into a real,
published guideline, re-run the independent field-by-field recheck against a sample of the actual outcomes
before trusting the batch, and read every `[NEEDS HUMAN REVIEW]`-flagged plain-language sentence — those
are exactly the cases GRADE says need a human judgment call, not a formula.
