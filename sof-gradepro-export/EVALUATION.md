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

## Known gap found during verification

The source Excel's intervention-arm absolute rate (e.g. "420 per 1000", fictional) is parsed and used only as an
internal sanity check (does the arm with the lower/higher rate match the direction the relative-effect
point estimate implies); it is never written into the output JSON, because GDT's own schema has no field
for it — `absoluteEffect[0].@type` is `"AutoCalculatedAbsoluteEffect"`, meaning MAGICapp/GDT recomputes
the intervention arm's risk from `controlRisk` + `relativeEffect` rather than storing it directly. Not a
bug; documented in `references/schema_mapping.md` so it doesn't look like a silent data-loss defect on a
later read.

## What hasn't been verified

- The converter has only been run against **dichotomous / time-to-event** outcomes (the only type
  confirmed in both the source Excel format and the one real GDT sample this skill was built against).
  Continuous or non-poolable/narrative outcomes are out of scope for v1 — see the "Scope (v1)" note at the
  top of `references/schema_mapping.md`.
- The JSON-LD output has **not been confirmed to actually import cleanly through MAGICapp's live beta
  importer** — field shapes are modeled on one real GDT export sample plus MAGICapp's public API schema,
  not round-tripped through an actual import. Several `@type` literals for RR/OR outcomes (as opposed to
  the confirmed HR case) are extrapolated, not directly observed. Treat the first real import as the real
  test, and expect to file a bug/adjust the converter if MAGICapp rejects something.

## Scaling the rigor

For a one-off single outcome, the functional-run-only level of checking above is enough — skim the output
against the source cells. For a full PICO (a folder of many outcomes) being imported into a real,
published guideline, re-run the independent field-by-field recheck against a sample of the actual outcomes
before trusting the batch, and read every `[NEEDS HUMAN REVIEW]`-flagged plain-language sentence — those
are exactly the cases GRADE says need a human judgment call, not a formula.
