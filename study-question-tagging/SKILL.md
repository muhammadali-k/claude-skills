---
name: study-question-tagging
description: >-
  Assign/tag included studies to the clinical questions of a guideline or systematic review — decide
  which trials answer which question and emit one filtered spreadsheet per question. Use whenever someone
  has (1) a guideline or manuscript that poses clinical questions (PICO/CQ-numbered "what treatment for…",
  "how long…", "which patients…" questions), (2) an included-studies sheet (one row per study, with IDs
  and usually abstracts), and (3) reference publications (full-text PDFs + supplements), and wants the
  studies mapped onto the questions. Trigger on phrasings like "assign these studies to each guideline
  question", "tag studies to clinical questions", "which studies answer this CQ", "redo the literature for
  these questions based on the included studies", "build a per-question evidence list", or "split the
  included studies by clinical question" — even when they don't name a file type. This is the
  question-tagging sibling of itable-extraction (data into cells) and outcomes-extraction (effect
  estimates): reach for THIS one when the deliverable is per-question study lists, not filled data tables.
  Reads the actual publications to judge fit, asks only when an assignment is genuinely ambiguous, and
  produces one spreadsheet per question filtered to the studies that answer it.
---

# Study → guideline-question tagging

## What this does and why it works this way

You are mapping a set of included studies onto a guideline's clinical questions: deciding, for each
question, which trials actually *answer* it, and emitting one spreadsheet per question containing just
those studies. This is the "which evidence belongs where" step that precedes writing a guideline's
literature-review sections.

The mechanics are trivial; the judgment is not. Whether a given trial answers a given question depends on
its population, its randomized comparison, and the specific decision the question asks — and a single
careless pass tends to over-include (every endocrine trial reports adverse events, so a naive matcher
dumps them all under the "adverse effects" question) or mis-assign on population. So the work is built
around **reading the source to establish each study's population/design/comparison**, **judging fit
against explicit per-question criteria**, and **independent classify-then-adjudicate** so the calls are
consistent and the close ones are surfaced rather than buried.

The skill is **template-agnostic**: it learns the questions from whatever guideline you provide and the
columns from whatever studies sheet you provide. It is meant to be reused across guidelines.

## Inputs you will receive

- **A guideline / manuscript document** (usually `.docx`, sometimes PDF) that poses the clinical
  questions, often with recommendations, a draft literature review, and GRADE evidence tables. The
  questions live here.
- **An included-studies sheet** (`.xlsx`) — one row per study with an ID column and, almost always, an
  abstract column. This is the source of truth for *which studies exist and what columns the output keeps*.
- **A folder of reference publications** — full-text PDFs plus supplements (`_suppl`, `_Sup`, `.docx`),
  one set per study.

If which questions are in scope, which file belongs to which study, or how a borderline study should be
classified is unclear, **ask** — but only for things that are genuinely ambiguous and would change the
output. When the fit is clear, proceed without interrupting.

## The deliverable

**One spreadsheet per in-scope clinical question**, each a copy of the included-studies sheet filtered to
the studies that answer that question — same columns, same formatting. A question with no answering study
becomes a header-only file (an honest "no included study answers this"). That is the entire handover; the
assignment matrix and other artifacts stay in `_work/` as scaffolding, not deliverables.

## The pipeline (work in a `_work/` dir next to the studies sheet)

Use the bundled scripts — they encode parsing/preservation logic that is easy to get subtly wrong.

### Phase 1 — Extract the clinical questions
`python scripts/inspect_guideline.py <doc.docx>` for an outline + table inventory + question guesses;
then read the questions **verbatim** (`--dump-paras _work/paras.txt` and Read the span, or `--tables`).
Capture each in-scope question's key, exact text, and scope (population / intervention / decision type).
Confirm scope with the user if the guideline covers more than they want.

### Phase 2 — Load studies and match to publication files
`python scripts/inspect_studies.py <studies.xlsx> --refs <ref_dir> --out _work/study_index.json`.
Detects the ID and abstract columns; fuzzy-matches each study to its files. **Resolve every no-match /
multi-match before classifying.**

### Phase 3 — Compose the assignment rules
Write the explicit rules for this project: each question's gatekeeper(s), the direct-evidence bar, the
multi-assignment policy, and any scope calls the user confirmed. This short text is passed verbatim to
the agents so every study is judged identically.

### Phase 4 — Classify, then adjudicate
Run `assets/classify_studies.js` with the **Workflow** tool, passing `{questions, rules, studies}` via
`args` (see `references/workflow.md` for the exact shape). One classifier per study reads the abstract —
opening the PDF only when fit is ambiguous — and returns population/design/comparison + the questions it
answers; an adjudicator compiles the matrix and lists judgment calls. Save to `_work/classification.json`.
If the Workflow tool isn't available, run the two roles inline (same discipline).

### Phase 5 — Surface judgment calls, finalize the matrix
Ask the user about genuine, output-changing ambiguities (batched, with a recommendation each); proceed on
the clear ones. Write `_work/matrix.json` (rich form: per-question `key`, `slug`, `study_ids`), including
empty questions.

### Phase 6 — Build the files and QC
```
python scripts/build_question_files.py --source <studies.xlsx> --matrix _work/matrix.json --out-dir <out>
python scripts/qc.py                  --source <studies.xlsx> --matrix _work/matrix.json --out-dir <out>
```
Build copies the workbook per question and deletes non-assigned rows (formatting preserved; empty →
header-only). QC confirms columns match and rows equal the matrix, and flags any study in no file.

### Phase 7 — Hand off
Give the user the per-question files and a short summary: count per question, every flagged call and its
resolution, empty questions, and any unassigned study. If an assignment contradicts the guideline's draft
(e.g. a question the draft called "no evidence" now has a qualifying trial), say so — the text needs updating.

## The method that makes assignments defensible

Full detail in **`references/method.md`** — read it before classifying. The essentials:

- **Read each question as a decision** and derive its inclusion criteria (population, intervention/
  comparison, decision type: select / which-treatment / duration / timing / adherence).
- **Tag by what the trial randomizes, not by the population it enrolled** (the most common mis-tag). A
  "which treatment" question is answered by a contrast between *different* treatments, OR by an
  extend/continue/intensify-vs-not choice — extended/intensified therapy is itself a treatment strategy,
  so multi-assign those trials to *both* the treatment question and the duration question. But a trial
  whose arms share one regimen and differ only in the *length of a component* answers the duration (or
  timing) question, not "which treatment," even when the population fits. When the guideline lists its
  per-question evidence comparisons (recommendation text / GRADE tables), use those as the authority.
- **Direct-evidence standard:** include a study only when its randomized contrast bears on that decision.
  *Reporting* an outcome ≠ *answering* the question — don't let incidental data (e.g. routine adverse-event
  reporting) sweep every trial into a question. If the project deems a class in-scope, make the rule
  explicit and apply it to all studies.
- **Multi-assignment:** a study goes under every question it directly answers; never under one it doesn't.
- **Gatekeepers first:** population (and line/biomarker/setting) hard-exclude — a premenopausal-only trial
  cannot answer a postmenopausal question. Apply these first.
- **Abstracts first, full text for the ambiguous:** abstracts usually settle the tag; open PDFs for
  borderline population, unclear effect-bearing arm, treatment-vs-duration overlap, or adherence relevance.
- **Ask only when it's genuinely the user's call** (boundary cases, scope, file mismatches, near-miss
  inclusions); otherwise proceed. **Empty questions are a valid result** — don't manufacture a fit.

## Scaling
Classify-then-adjudicate with abstract-first reading is the default and is cheap (most tags come from the
sheet's abstracts). For a handful of studies you may classify inline; for many, the Workflow tool runs
classifiers concurrently. Say which mode you used.

## Files in this skill
- `scripts/inspect_guideline.py` — outline / tables / question-guesses / paragraph dump for any `.docx` guideline
- `scripts/inspect_studies.py` — dump the studies sheet (ID + abstract detection) and match studies to reference files
- `scripts/build_question_files.py` — build one filtered Excel per question from `matrix.json` (formatting preserved)
- `scripts/qc.py` — verify each file's columns/rows vs source + matrix; report coverage gaps
- `assets/classify_studies.js` — the classify→adjudicate Workflow (parameterized via `args`)
- `references/method.md` — how to judge which study answers which question (read before classifying)
- `references/workflow.md` — orchestration: matching, `args`/matrix schemas, build + QC, re-runs
