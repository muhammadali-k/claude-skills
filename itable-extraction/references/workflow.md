# Phase 4 — two independent reviewers + senior adjudication

The deliverable's trustworthiness comes from **mimicking the two-reviewer process of a real systematic
review**, not from a single verification pass. Per study:

1. **Reviewer A** and **Reviewer B** extract concurrently and independently from the same sources, with
   the identical brief. Neither sees the other's output, ever. They run on **different models**.
2. **Concordance** is computed in the workflow script — plain code, no agent — and recorded as a metric.
   It does not gate anything.
3. **The senior reviewer** re-reads every source in full from scratch, re-derives every value including
   the agreed ones, and adjudicates. Its cells are what get assembled.

Studies run concurrently and pipelined (a study's senior pass starts as soon as its two reviewers
finish) using the Workflow tool with `assets/extract_workflow.js`.

## Why independence, and why the senior still re-derives everything

A verifier that is shown the first agent's answer *before* forming its own anchors on it. It reads to
confirm, finds the quoted snippet, and agrees — including when the first agent read the wrong table.
Two reviewers who commit independently produce genuinely separate readings, so their disagreement
locates the hard values.

But agreement is weak evidence. It measures how **legible** a value was, not whether it is **correct**:
two readers make the same mistake for the same reason (an ambiguous column header, a footnote both
missed, a figure both misread), and two models sharing a base model make correlated errors. That is why
the senior re-derives every value rather than only the disputed ones, and why the run reports how often
the senior overrode **both** reviewers. That count is the honest estimate of what a two-reviewer-only
design would have gotten wrong on this material.

## What you pass as `args`
```json
{
  "guidePath": "_work/field_guide.md",
  "conventionsPath": "_work/conventions.md",
  "models": { "a": "opus", "b": "sonnet", "senior": "opus" },
  "studies": [
    {
      "id": "64279",
      "label": "DATA trial (extended adjuvant AI)",
      "files": ["/abs/path/main.pdf", "/abs/path/suppl.pdf"],
      "arm_proposal": "T1 = 6-yr anastrozole (extended); Control = 3-yr anastrozole (standard).",
      "calibration": "_work/calibration_12292.json"   // optional, same-trial example row
    }
  ]
}
```
`studies[*].files` are absolute paths from `sources_map.json`. `arm_proposal` comes from your reading of
the template + paper. `calibration` is optional and only set when an example row exists for that trial.

**`models` is optional and defaults to `{a:'opus', b:'sonnet', senior:'opus'}`.** Two rules govern it:

- **A and B must differ.** Two instances of one model agree too easily, which inflates concordance and
  hides exactly the errors the design exists to catch. If you only have one model available, say so in
  the handover — the concordance number then means much less.
- **The senior is pinned, not inherited.** Adjudication means reading verbatim clinical-trial text and
  quoting it back. A model with heavier response filtering may decline or soften that, and a senior that
  hedges is worse than useless because everything downstream trusts it. Pin it to a strong model.

## Agent tooling
Each agent reads `guidePath` and `conventionsPath` (Read tool), then the source documents. For PDFs use
`pdftotext -layout` (fast, preserves table columns) and PyMuPDF for page-aware tables; use the **Read
tool on specific pages** for values that live in figures or that don't extract cleanly (KM-curve rates,
complex baseline tables). For `.docx` supplements, unzip `word/document.xml` and strip tags. Agents must
not use any source outside `files`.

## Reviewer output schema (identical for A and B — they are peers, not roles)
```json
{
  "type": "object", "additionalProperties": false,
  "properties": {
    "id": {"type": "string"},
    "n_arms": {"type": "integer"},
    "arm_mapping": {"type": "object"},               // role -> arm label, e.g. {"treatment_1": "...", "control": "..."}
    "cells": {"type": "array", "items": {
      "type": "object", "additionalProperties": false,
      "properties": {"col": {"type": "string"}, "value": {"type": "string"}, "source": {"type": "string"}},
      "required": ["col", "value", "source"]}},
    "flags": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["id", "n_arms", "arm_mapping", "cells", "flags"]
}
```
Emit a cell only for values supported by the sources; everything omitted becomes the column's missing
marker at assembly. Always fill the identifying / characteristic columns you can (ids, arm names, totals,
follow-up, endpoints).

## Senior output schema
Same shape as a reviewer, plus:
```json
{
  "adjudications": {"type": "array", "items": {
    "type": "object", "additionalProperties": false,
    "properties": {"col": {"type": "string"}, "value_a": {"type": "string"}, "value_b": {"type": "string"},
      "senior_value": {"type": "string"},
      "agreed_with": {"type": "string", "enum": ["A", "B", "both", "neither"]},
      "reason": {"type": "string"}},
    "required": ["col", "value_a", "value_b", "senior_value", "agreed_with", "reason"]}},
  "unresolved": {"type": "array", "items": {
    "type": "object", "additionalProperties": false,
    "properties": {"col": {"type": "string"}, "why": {"type": "string"}},
    "required": ["col", "why"]}},
  "confidence": {"type": "string"}
}
```
`agreed_with: "neither"` is the metric that matters — it counts values a two-reviewer-only design would
have gotten wrong. Use `"(omitted)"` as the value for a cell a reviewer did not emit.

## Concordance (computed in the script, not by an agent)
Cell-by-cell over the union of both reviewers' `cols`. Values are normalised before comparison: trimmed,
numerics parsed so `0.80` and `0.8` match, and `""` / `NA` / `N/A` / `NR` / `not reported` collapsed to a
single missing token. **A cell one reviewer emitted and the other omitted counts as discordant** — one of
them read a value the other declared absent, which is a real disagreement, not a formatting artifact.
Arm mapping and arm count are compared separately and reported separately.

## Prompts (the spirit, not verbatim)
- **Reviewer (both, identical):** "You are a meticulous systematic-review data extractor and an
  INDEPENDENT REVIEWER. Another reviewer is extracting this same publication separately; you will never
  see their work and they will never see yours. Do not guess what they would say or hedge toward a safe
  answer — report exactly what YOU can prove from these sources. Read the conventions and column map.
  Read ONLY these files. Determine the arm mapping (proposed: …; confirm/flag). For every value you can
  support, emit {col, value, source-with-snippet}. Omit anything not reported. Never fabricate; flag
  every judgment call."
- **Senior:** "You are the SENIOR REVIEWER. Two reviewers extracted this study independently. Your job is
  NOT to pick a winner. STEP 1: read the conventions, the column map, and every source IN FULL, from
  scratch, BEFORE looking at either draft; render and read figures. STEP 2: derive every value yourself,
  including ones both reviewers agreed on — agreement means a value was easy to read, not that it is
  correct. STEP 3: only then compare against the two drafts and log an adjudication wherever any of the
  three differ. Include values BOTH reviewers missed. Do not split the difference. Anything you cannot
  settle from these sources goes to unresolved[] for a human, with the cell omitted — an honest
  unresolved entry is a correct outcome, a fabricated resolution is the worst one."

Use `effort: 'high'` for all three — these reads are dense (KM curves, forest plots, supplementary
tables).

## Resolve the arm mapping first
If the two reviewers disagree on `arm_mapping` or `n_arms`, that is not one cell wrong — it re-slots
every per-arm value in the study. The senior prompt calls this out explicitly and the script surfaces it
as a separate line in the concordance report. Settle it before reading any per-arm number.

## What the script returns
```
{ studies: [ { id, label, n_arms, arm_mapping, cells, flags, confidence,
               adjudications, unresolved, concordance, reviewer_a, reviewer_b } ],
  run_metrics: { fields, concordant, discordant, concordance_rate,
                 adjudications, senior_overrode_both, unresolved } }
```
Save it to `_work/extraction_results.json` (the workflow result is in the task output file; extract the
`result` object and write it out). Assembly reads this file and uses the **senior's** `cells`.
`reviewer_a` and `reviewer_b` are retained so a disputed value can be re-litigated later without re-running.

**Report `run_metrics` to the user** alongside the filled sheet — concordance rate, `senior_overrode_both`,
and the unresolved count. A fill-rate on its own tells them how full the table is, not how right it is.

## Adapting rigor
Default is two reviewers + senior per study. For a quick single-study fill a lone extractor pass is
acceptable if you say so explicitly in the handover. Do **not** economise by having the senior look only
at discordant cells — that converts the design back into extract-then-check and reintroduces the
anchoring problem, while leaving the correlated-error case entirely unguarded.
