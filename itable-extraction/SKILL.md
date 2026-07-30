---
name: itable-extraction
description: >-
  Extract data from clinical-trial / systematic-review publications into a structured "i-table"
  via a multi-agent pipeline that mimics the two-reviewer process of a real systematic review:
  two independent reviewers extract, a senior reviewer re-derives every value and adjudicates,
  then assemble → validate. Use whenever
  the user has an extraction template or column list — usually an Excel/CSV "input sheet" with study
  rows pre-seeded with metadata — plus source publications (full-text PDFs and supplements) and needs
  the table filled. Covers systematic reviews, living guidelines, evidence synthesis, GRADE/PICO
  abstraction, and RCT data extraction. Trigger even on loose phrasings ("extract these studies into
  my table", "pull the data from these papers into the iTable", "populate the extraction sheet",
  "abstract these trials"), and even when no example rows or Excel template are present. Handles
  per-arm columns, derives value formats and per-column data types from any example rows, attaches
  per-value provenance, and produces an upload-ready file. Not for writing the review manuscript
  itself — this is for getting data out of papers and into cells.
---

# i-table extraction

## What this does and why it works this way

You are filling a structured evidence table ("i-table") from primary source publications. The hard
parts are not typing values into cells — they are (1) reading dense trial PDFs and supplements
correctly, (2) keeping every value traceable to its source, (3) matching the *exact* format and data
type each column expects, and (4) not fabricating data that the sources don't report. A single pass by
one agent tends to hallucinate plausible-but-wrong numbers and silently mis-map arms.

So the pipeline mimics **the two-reviewer process of a real systematic review**: two reviewers extract
the same study **independently**, neither seeing the other's work, and a **senior reviewer** then
re-derives every value from source and adjudicates. This is not the same as extract-then-check. A
verifier shown the first agent's answer anchors on it and rubber-stamps plausible errors; two reviewers
who commit independently produce genuinely separate readings, and their agreement or disagreement is
information you would not otherwise have.

**Concordance between the two reviewers is recorded, not trusted.** It measures how legible a value was
in the source, not whether it is correct — two readers can make the same mistake for the same reason,
and models sharing a base model make correlated errors. So the senior re-derives *every* value,
including the agreed ones, and the run reports how often it had to override both reviewers. That number
is the honest estimate of what a two-reviewer-only design would have gotten wrong. Every value records
where it came from.

This skill is anchored in clinical evidence tables (it understands trial arms, endpoints like OS/DFS/RFS,
baseline characteristic tables, and PICO structure) but is **template-agnostic** — it learns the column
set, value conventions, and data types from whatever template and example rows you provide.

## Inputs you will receive

- **An input sheet** (the deliverable to fill). Usually an `.xlsx` with multi-row/merged headers and
  rows pre-seeded with each study's identifying metadata (author, year, title, DOI/PMID). Sometimes a
  CSV or a plain list of columns. This is the source of truth for *which columns exist and in what order*.
- **A folder of source publications** — full-text PDFs plus supplements (`_suppl`, `_Sup`, `.docx`),
  one set per study.
- **Optional: example filled rows** (e.g. an `itable_example_extractions.xlsx`). When present they are
  gold: they reveal value formats, the missing-value convention, per-column data types, and serve as
  calibration. They are often absent on new projects — that's fine, fall back to column descriptions
  and confirm conventions with the user.

If anything essential is missing or ambiguous (which column means what, which file belongs to which
study), **ask** rather than guess. Mis-extraction is expensive to unwind.

## The pipeline (six phases)

Work in a `_work/` directory next to the input sheet so intermediate artifacts are inspectable and the
job is resumable. Use the bundled scripts — they encode logic that is easy to get subtly wrong.

### Phase 1 — Parse the template into a column schema
Run `scripts/parse_template.py` to turn the template (and example, if any) into machine-readable specs:

```
python scripts/parse_template.py --template <input_sheet> [--example <example.xlsx>] --out-dir _work
```

It produces `column_schema.json` (every column → its full header path, and detected granularity such as
per-arm sub-columns), `field_guide.md` (a human-readable column→meaning map you'll hand to the agents),
and — if an example was given — `col_types.json` (each column's data type: number / letters / text) and
`calibration_<id>.json` (an example row to anchor conventions). Read `field_guide.md` and skim
`column_schema.json`; if any column's meaning is unclear, ask the user. See
`references/data_types.md` for how types are derived and why it matters for upload.

### Phase 2 — Establish extraction conventions
Open `references/conventions.md` — it is the extractor brief (value formats, the arm-assignment rule,
the missing-value convention, the endpoint→row mapping). If an example file exists, reconcile the brief
with what the example actually does (formats, how it marks missing data) and note any project-specific
rules. If no example exists, walk the key conventions with the user so the output matches their house
style. Write the finalized brief to `_work/conventions.md` — the agents will read it.

### Phase 3 — Match each source publication to its row
Run `scripts/match_sources.py --sheet <input_sheet> --sources-dir <folder> --out _work/sources_map.json`.
It matches files to the pre-seeded rows by author/year/title/DOI/PMID, groups each main text with its
supplements, and flags anything ambiguous. **Review the mapping** and resolve flagged rows with the
user before extracting — a wrong file→row match poisons an entire row.

### Phase 4 — Two independent reviewers + senior adjudication (the core)
This is where the quality comes from. Three roles per study, run with the Workflow tool using the
bundled `assets/extract_workflow.js` and passing your study list + paths via `args`:

- **Reviewer A and Reviewer B** extract the study **concurrently and independently**, from the same
  sources, with the identical brief. Neither is told what the other found; neither ever sees the other's
  output. They run on **different models** so their failure modes differ — two instances of one model
  agree too easily. Each emits per-field values with provenance.
- **Concordance** is computed **in code, not by an agent** — cell by cell, with numeric normalisation.
  A cell one reviewer emitted and the other omitted counts as a disagreement, because one of them read a
  value the other declared absent. It is recorded as a metric and does **not** gate anything.
- **The senior reviewer** reads the conventions, the column map, and **every source in full, from
  scratch, before looking at either draft**, then re-derives **every value — including the ones both
  reviewers agreed on** — and logs an adjudication wherever any of the three differ. Its cells are what
  get assembled. It is also responsible for values *both* reviewers missed; adjudicating is not the whole
  job, being exhaustive is part of it.

The senior is pinned to a strong model (Opus by default) rather than inheriting the session model.
Adjudication means reading verbatim clinical trial text and quoting it back; a model with heavier
response filtering may decline or soften that, and a senior that hedges is worse than useless because
everything downstream trusts it.

Resolve the **arm mapping first** when reviewers disagree on it — it re-slots every per-arm value in the
study, so a disagreement there is not one cell wrong, it is the whole row wrong.

Two rules the senior must not break. It must **not split the difference** between reviewers — it either
proves a value from source or declares it unresolved. And anything it genuinely cannot settle goes to
`unresolved[]` for a **human**, with the cell omitted rather than guessed. An honest unresolved entry is
a correct outcome; a fabricated resolution is the worst one.

Key principles (don't skip): sources-only (never infer values not in the provided documents — mark
missing instead); every non-missing value carries a page/table/figure citation + verbatim snippet;
confirm the arm mapping per study; flag every judgment call. When an example row exists for the same
trial/template, tell the agents to calibrate against it.

Full orchestration, prompts, JSON schemas, and the model-assignment config are in
`references/workflow.md` — read it before launching. **Report `run_metrics` to the user**: concordance
rate, how often the senior overrode both reviewers, and the unresolved count.

If the Workflow tool (or sub-agents) is unavailable in your context, run the same three roles yourself
inline per study — but preserve the independence: produce reviewer A's full answer, then produce
reviewer B's answer *without consulting A*, then adjudicate from source. The orchestration mechanism
doesn't matter; independent commitment before comparison is what makes concordance meaningful, and
re-derivation from source is what makes the output trustworthy.

### Phase 5 — Assemble into the sheet
Run `scripts/assemble.py --results _work/extraction_results.json --template <input_sheet>
--schema _work/column_schema.json [--col-types _work/col_types.json] --in-place` (or `--out <new.xlsx>`
when only a column list was given — it will generate the workbook). It backs up the original, writes
each value into the right cell, fills missing cells using the convention the column's *type* requires
(text → the missing marker e.g. `NA`; number → blank or `0` per the example), preserves merged headers,
and emits a long-format CSV plus a provenance workbook (`*_provenance.xlsx`: per-value sources, arm
mappings, flags, summary).

### Phase 6 — Validate data types + QC
Two checks, both important:
- `scripts/validate_types.py --sheet <filled_sheet> --col-types _work/col_types.json --fix` — enforces
  each column's data type so the file imports cleanly into the target system. This catches the classic
  failures: a literal `NA` in a numeric column, or digits/symbols in a letters-only column (e.g. arm
  names like "Tamoxifen + OFS", hyphenated authors). It rewrites offending cells per the rules in
  `references/data_types.md` and reports a clean/violation count. If there is no example to derive types
  from, this step asks the user for the target system's column types or is skipped.
- `scripts/qc.py --sheet <filled_sheet> --results _work/extraction_results.json --schema
  _work/column_schema.json` — round-trips the written values against the reconciled data, confirms no
  data cell is empty, checks structure (column count, merged headers), and prints fill-rates + all
  flagged judgment calls for the user to review.

Then hand the user the filled sheet, the provenance file, and a short summary of fill-rates and flagged
decisions (arm mappings, figure-read values, denominator choices). Surface judgment calls — don't bury them.

## Node labels are a controlled vocabulary, not free text

The arm-name columns in an i-table are not decorative. They are read downstream, they end up as node
labels in a network meta-analysis, and **`netmeta` joins arms by string equality**. "Nivolumab +
Ipilimumab" and "Nivolumab plus iplimumab" are two nodes, not one. The network then either reports as
disconnected — the lucky case, because you find out — or stays connected while an edge silently
disappears, or splits one regimen's evidence across two underpowered nodes and inverts the ranking.
Nothing in the sheet looks wrong. It surfaces as a wrong league table.

**The i-table is usually where this starts,** because its arm columns are filled by a different pass
from the outcomes sheets. In the reference project the two disagreed for the *same trials*:
`Atezolezumab` against `Atezolizumab`, `Everolimus` against `Everoilmus`, and CheckMate 914's single
combination arm written four different ways across two files, three of them misspelled.

The rules, in full in `references/node-vocabulary.md`:

1. **Agent labels UPPERCASE, 3–5 characters, no punctuation** — `SUN SOR PAZO AXI EVE PEM NIVO IPI
   ATEZO BELZ GIREN DURVA TREME`. Short enough that a league table fits on a page.
2. **Combinations join with a bare `+`, no spaces** — `NIVO+IPI`. Never `NIVO + IPI`, never
   `NIVO plus IPI`, never `Nivo+Ipi`. Whitespace is forbidden outright rather than normalised,
   because a trailing or non-breaking space is **visually identical** in a spreadsheet cell.
3. **Component order is fixed by the vocabulary's list, not derived.** "Backbone first" and
   "alphabetical" disagree, and two people applying a rule resolve it differently.
4. **The pooled comparator is ONE label** (default `NOADJ`) whatever the trial used; what it actually
   was goes in a separate field. A trial whose control is an **active** regimen — an add-on design —
   gets that regimen's label instead, because it genuinely is a different node.
5. **Dose, duration and setting variants are hyphen-suffixed** — `SOR-1Y`, `PAZO-600`, `NIVO-PERI` —
   and the suffix is part of the node identity, so merging two variants is a deliberate act.

Each project supplies its own `*_node_vocabulary.json`; the skill supplies the rules and the validator.
Load it in **Phase 2** alongside the conventions, and enforce it in **Phase 6**:

```bash
python scripts/nodes.py <project>_node_vocabulary.json            # print it
python scripts/nodes.py <project>_node_vocabulary.json "NIVO + IPI"   # resolve specific labels
python scripts/qc.py --sheet filled.xlsx ... --vocabulary <project>_node_vocabulary.json
```

`qc.py` **fails the run** on any rejection. Rejections carry a diagnosis and a suggested fix, not just
a complaint. If no vocabulary is passed, `qc.py` says so loudly rather than passing silently — an
unvalidated arm column is a network failure waiting to happen.

`scripts/nodes.py` is **byte-identical** to the copy in `outcomes-extraction`. That is deliberate: two
skills writing labels into the same downstream analysis must not be able to disagree about what a valid
label is, and two subtly different validators would be a worse bug than none.

## Scaling the rigor
Two independent reviewers + senior adjudication + provenance is the default, because it materially
reduces wrong values and because the senior-override count tells you how much you should trust the
cheaper configurations. For a one-off single study or a quick sanity fill you may collapse to a single
extractor pass + spot-check — but say so explicitly, and say it in the handover, not just to yourself.
For large jobs the Workflow tool pipelines studies concurrently; that's the normal mode.

**What to do with the metrics.** If the senior rarely overrides both reviewers on a given project's
template and source type, concordance is tracking truth there and you have evidence for lightening the
senior pass on future updates. If it overrides both often, the opposite — and the two-reviewer-only
design would have been quietly wrong. Record the number each run so a living review can watch it move
rather than assuming it.

## Files in this skill
- `scripts/parse_template.py` — template + example → column schema, field guide, data types, calibration
- `scripts/match_sources.py` — auto-match source files to pre-seeded rows
- `scripts/assemble.py` — write results into the sheet (in place or generate), fill missing, emit provenance
- `scripts/validate_types.py` — enforce per-column data types for clean upload
- `scripts/qc.py` — round-trip + structure + fill-rate + flags + node-label validation (`--vocabulary`)
- `scripts/nodes.py` — controlled node vocabulary loader + validator (identical to the outcomes-extraction copy)
- `assets/extract_workflow.js` — the two-reviewer + senior-adjudicator Workflow script (via `args`)
- `references/workflow.md` — multi-agent orchestration: agent prompts, JSON schemas, model assignment
- `references/conventions.md` — extractor brief: value formats, arm rule, missing values, endpoint→row map
- `references/data_types.md` — upload data-type validation: how to derive types and fix violations
- `references/node-vocabulary.md` — the node-label rules and why string equality makes them non-negotiable
