# Orchestration: from inputs to per-question files

Work in a `_work/` directory next to the studies sheet so intermediate artifacts (the study index, the
assignment matrix) are inspectable and the job is resumable. The only handover deliverables are the
per-question Excel files; everything in `_work/` is scaffolding.

## Phase 1 — Extract the clinical questions from the guideline

Run `scripts/inspect_guideline.py <doc.docx>` to get an outline, a table inventory, and heuristic
question guesses. Then read the questions **verbatim** — dump the body with
`--dump-paras _work/guideline_paras.txt` and Read the relevant span, or `--tables` for the
question/recommendation tables. For each in-scope question capture: a stable **key** (e.g. `CQ10`, or
the guideline's own numbering), the **verbatim text**, and its **scope** (population/intervention/
decision type). If the guideline has sections beyond the user's interest, confirm which questions are in
scope before proceeding (see method §6). Many guidelines also include a draft literature review or GRADE
comparison tables naming specific trials — useful cross-checks, but the assignment is decided by what
each study actually is, not by a possibly-outdated draft.

## Phase 2 — Load studies and match each to its publication files

Run `scripts/inspect_studies.py <studies.xlsx> --refs <ref_dir> --out _work/study_index.json`. It detects
the ID column and abstract column, lists studies, and fuzzy-matches each to reference files by
surname+year parsed from filenames. **Resolve every no-match / multi-match before classifying** — a wrong
file→study pairing poisons that study's tag. The `study_index.json` (id, fields, abstract, matched_files)
feeds the classifier.

## Phase 3 — Compose the assignment rules

Write the explicit rules for this project (method §8): the per-question gatekeepers, the direct-evidence
bar, multi-assignment policy, and any scope decisions the user has confirmed. Keep this as a short text
block — it is passed verbatim to the agents so every study is judged identically.

## Phase 4 — Classify each study, then adjudicate (the core)

Run `assets/classify_studies.js` with the **Workflow** tool, passing `args`:

```json
{
  "questions": [
    { "key": "CQ10", "text": "<verbatim question>", "scope": "premenopausal; which ET regimen" }
  ],
  "rules": "<the rules text from Phase 3>",
  "studies": [
    { "id": "12301", "label": "TEXT+SOFT (Pagani 2023)",
      "abstract": "<from study_index.json>",
      "files": ["/abs/path/main.pdf", "/abs/path/suppl.pdf"] }
  ]
}
```

Per study, a **classifier** agent reads the abstract (opening the PDFs only when fit is ambiguous, per
method §5) and returns its population/design/comparison/primary-endpoint plus the question keys it
answers with one-line rationales. An **adjudicator** then compiles the final `matrix` (`{key: [ids]}`),
applies the rules consistently, and lists `judgmentCalls`. Save the returned object to
`_work/classification.json`.

**If the Workflow tool isn't available** (e.g. you are yourself a sub-agent, or the set is tiny): do the
same two roles inline. Tag each study from its abstract, open the PDF for the ambiguous ones, then make
one consolidated pass applying the rules across all studies. The mechanism doesn't matter; the
abstract-first + consistent-rules + flag-the-close-calls discipline is what makes the result trustworthy.

## Phase 5 — Surface judgment calls, then finalize the matrix

Review `adjudication.judgmentCalls`. For genuine, output-changing ambiguities (method §6), ask the user a
short batched question with your recommendation for each; for everything clear, proceed. Then write the
final matrix to `_work/matrix.json` in the rich form:

```json
{
  "questions": [
    { "key": "CQ10", "slug": "premenopausal_ET_treatment", "title": "Premenopausal ET treatment",
      "study_ids": ["12301", "30503", "33451", "62760", "63131"] },
    { "key": "CQ13", "slug": "timing_of_ET_initiation", "study_ids": [] }
  ]
}
```

Pick a short, descriptive `slug` per question; the output filename is `<key>_<slug>.xlsx`. Include every
in-scope question, even those with an empty `study_ids` (method §7).

## Phase 6 — Build the files and QC

```
python scripts/build_question_files.py --source <studies.xlsx> --matrix _work/matrix.json --out-dir <deliverable_dir>
python scripts/qc.py                  --source <studies.xlsx> --matrix _work/matrix.json --out-dir <deliverable_dir>
```

`build_question_files.py` copies the source workbook per question and deletes non-assigned rows, so header
styling, column widths, and frozen panes are preserved exactly; empty questions become header-only files.
`qc.py` confirms each file's columns match the source and its rows are exactly the matrix's IDs, and
reports any source study that landed in no file (usually an error to investigate). If `--sheet` or the ID
column aren't auto-detected, pass `--sheet NAME` / `--id-col LETTER_OR_HEADER` to both scripts.

## Phase 7 — Hand off

Give the user the per-question files and a short summary: the count per question, every flagged judgment
call and how it was resolved, any empty questions, and any study assigned to no question. Surface the
close calls — don't bury them. If an assignment contradicts the guideline's existing draft (e.g. a
question the draft called "no evidence" now has a qualifying trial), say so, because the manuscript text
will need updating.

## Notes
- `.docx` supplements: convert with `textutil -convert txt file.docx` (macOS) before reading, or unzip
  `word/document.xml` and strip tags.
- DOI→PMID and other ID lookups, if needed, via the PubMed MCP — but assignment relies only on the
  provided sources, not external full texts.
- Re-running on an updated study set: drop the new rows into the studies sheet, add them to `args.studies`,
  re-run Phases 4–6. The rules text is the contract that keeps updates consistent with the original pass.
