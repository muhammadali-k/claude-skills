# Phase 4 — multi-agent extract + verify

The deliverable's trustworthiness comes from **independent verification**. For each study run two agents:
an **extractor** that reads the sources and emits values with provenance, then a **verifier** that
re-derives every value from the same sources and reconciles. Studies run concurrently and pipelined
(verify a study as soon as its extract finishes) using the Workflow tool.

Use the bundled `assets/extract_workflow.js`. It is parameterized entirely through `args` (workflow
scripts cannot read files, but the agents they spawn can). You build `args` from earlier phases and pass
it to the Workflow tool.

## What you pass as `args`
```json
{
  "guidePath": "_work/field_guide.md",
  "conventionsPath": "_work/conventions.md",
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

## Agent tooling
Each agent reads `guidePath` and `conventionsPath` (Read tool), then the source documents. For PDFs use
`pdftotext -layout` (fast, preserves table columns) and PyMuPDF for page-aware tables; use the **Read
tool on specific pages** for values that live in figures or that don't extract cleanly (KM-curve rates,
complex baseline tables). For `.docx` supplements, unzip `word/document.xml` and strip tags. Agents must
not use any source outside `files`.

## Extractor output schema (force via the Workflow `schema` option)
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

## Verifier output schema
```json
{
  "type": "object", "additionalProperties": false,
  "properties": {
    "verdicts": {"type": "array", "items": {
      "type": "object", "additionalProperties": false,
      "properties": {"col": {"type": "string"}, "agree": {"type": "boolean"},
        "corrected_value": {"type": ["string","null"]}, "note": {"type": "string"}},
      "required": ["col", "agree", "corrected_value", "note"]}},
    "missing_cells": {"type": "array", "items": {"$ref": "#/cell"}},  // values the extractor missed
    "overall_note": {"type": "string"}
  },
  "required": ["verdicts", "missing_cells", "overall_note"]
}
```

## Reconciliation (done in the workflow script)
- Start from the extractor's cells.
- For each verdict where `agree=false` and `corrected_value` is set → replace the value; append the
  verifier note to `source`.
- Add `missing_cells` the extractor didn't have.
- Keep `flags`, the `overall_note`, and a `reconcile_changes` log.
The script returns `{ studies: [ { id, arm_mapping, cells, flags, verify_note, reconcile_changes } ] }`.
Save that to `_work/extraction_results.json` (the workflow result is in the task output file; extract the
`result` object and write it out). Assembly reads this file.

## Prompts (the spirit, not verbatim)
- **Extractor:** "Extract trial data for ONE publication into the i-table schema. Read the conventions and
  the column map. Read ONLY these source files. Determine the arm mapping (proposed: …; confirm/flag).
  For every value you can support, emit {col, value, source-with-snippet}. Omit anything not reported.
  Calibrate against <calibration row> if provided. Be exhaustive; never fabricate; flag judgment calls."
- **Verifier:** "Independently verify another extractor's output for this study. Re-derive each value
  yourself from the SAME sources — don't trust the extractor. Mark each cell agree/disagree (+corrected
  value). Add values it missed (especially baseline tables, efficacy rates, adverse events). Comment on
  arm-mapping correctness and population/timepoint caveats."

## Adapting rigor
Default is one extractor + one verifier per study. For a contested or high-stakes table, add a second
verifier with a different lens (e.g. one checks efficacy/safety numbers, one checks baseline/denominators)
and reconcile by majority. For a quick single-study fill, a lone extractor pass is acceptable if you say so.
