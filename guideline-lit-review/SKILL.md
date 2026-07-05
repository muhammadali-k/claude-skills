---
name: guideline-lit-review
description: >-
  Draft the narrative literature-review prose for a clinical practice guideline
  question directly from its Summary of Findings (SoF) / GRADE evidence tables.
  Use whenever a guideline literature-review document (e.g., an ASCO
  living-guideline "Clinical Question" .docx) already contains populated SoF
  tables — hazard ratios, 95% CIs, certainty of evidence, trial names — but needs
  the accompanying text: an opening trial-count summary plus numbered subsections
  (X.1, X.2, …) contextualizing each comparison. Trigger for phrasings like "write
  the literature review section," "draft CQ##," "contextualize these findings,"
  "turn these SoF tables into narrative," or "follow the shared format," even when
  the user does not say "skill" and only attaches a document and a clinical
  question stem. Builds on the docx skill: preserves the existing tables exactly,
  inserts the missing narrative, reformats table subtitles, and adds the
  control-arm footnote.
---

# Guideline literature-review drafter

## What this skill does

ASCO living-guideline literature reviews are organized one **Clinical Question (CQ)** per document. Each CQ document arrives with the **Summary of Findings (SoF) tables already populated** — every comparison has a row per outcome with the relative effect (HR and 95% CI), absolute risk estimates, certainty of evidence, and the trial(s) used. What is missing is the **narrative prose** that a reader sees before the tables: a one-sentence summary of how many trials were found, followed by numbered subsections (X.1, X.2, …) that state each comparison's result in words.

This skill writes that prose **from the tables**, in the established house style, and inserts it into the existing document without disturbing the tables. The output is a `.docx` that matches the format of the other CQ sections (CQ7, CQ16, CQ19, etc.) exactly.

**The governing principle is fidelity.** Every number, trial name, certainty rating, and direction of effect in the narrative must come from the SoF table in the document. Never import outside trial data, never recompute or "correct" a value, and never add a comparison the table does not contain. If the table is silent on something, the narrative is silent on it.

## Before you start: read the docx skill

This skill builds on the **docx** skill (`/mnt/skills/public/docx/SKILL.md`). Read it first — you will unpack the existing `.docx`, edit its XML, and repack it. Do **not** regenerate the document from scratch with docx-js; that would lose the formatting and risk altering the tables. Always edit the real file.

## Workflow

1. **Read the inputs.** Extract the CQ document's current text (`pandoc <file>.docx -o current.md`) so you can see the question stem, the existing table subtitles, the SoF data, and any footnotes. If the user also attached a *format reference* (a sibling CQ section like LR_CQ7), read it too — it is the source of truth for house style if anything here is ambiguous.

2. **Parse each SoF table** into a small mental (or written) structure per comparison: the comparison label, the intervention and comparator, and for each outcome the HR, 95% CI, certainty rating, and trial name(s). See `references/house-style.md` for exactly which fields drive which part of the sentence.

3. **Decide phrasing and ordering** using the rules below and in `references/house-style.md`.

4. **Unpack** the document: `python /mnt/skills/public/docx/scripts/office/unpack.py <file>.docx unpacked/`.

5. **Insert the narrative** by targeted `str_replace` edits on `unpacked/word/document.xml`: the opening summary paragraph, the numbered subsection paragraphs, the italic+underline table subtitles, and a control-arm footnote under each table. Use the exact XML patterns in `references/xml-patterns.md`. If comparisons must be **reordered** and the tables are not already in the target order, write the narrative in the final intended order first, then run `scripts/reorder_comparison_blocks.py` to move the table blocks to match (the model supplies the permutation; the script does the mechanical move). Keep narrative insertion and subtitle reformatting as **separate** edits — never let the narrative edit consume a subtitle.

6. **Repack and validate**: `python /mnt/skills/public/docx/scripts/office/pack.py unpacked/ <file>_final.docx --original <file>.docx`. Then `pandoc <file>_final.docx -o check.md` and read it back to confirm the narrative reads correctly and the tables are untouched.

7. **Deliver** the `.docx` to the outputs directory and present it. Then give a short bulleted summary of what was added (opening sentence, which subsections, subtitle reformatting, footnotes) — the user reviews these deltas.

## House style — the essentials

The full templates, worked examples, and edge cases live in `references/house-style.md`. **Read that file before drafting** — these are only the headline rules.

### Opening summary sentence

State how many trials the systematic review identified for this CQ and the population, mirroring the question stem. Count **distinct trials**, not comparisons or outcomes.

> *Seven randomized trials assessing adjuvant chemotherapy in patients with stage I-III hormone receptor-positive, HER2-negative breast cancer were identified by the systematic review.*

If the comparisons are stratified (e.g., overall population and by menopausal status, or by biomarker), add a short second clause noting that, as in CQ19.

### Numbered subsections

One numbered item (X.1, X.2, …) per comparison, matching the CQ number. Each reports, in this order: the intervention, whether it **was / was not associated with a statistically significant improvement** in the outcome, the comparator, then a parenthetical with the trial name(s), the outcome abbreviation, the HR with 95% CI in **square brackets**, and the certainty of evidence.

> *7.1. Sequential epirubicin/cyclophosphamide followed by paclitaxel was associated with a statistically significant improvement in OS compared with concurrent epirubicin, cyclophosphamide, and paclitaxel (AGO; OS, HR, 0.72 [95% CI, 0.60 to 0.87]; high certainty of evidence).*

When a comparison reports several outcomes, write one sentence per outcome within the same numbered item, then close with a sentence explaining the certainty rating if a downgrade note is present in the table (see CQ16/CQ19 examples).

### Significant vs not — read the CI, not your expectations

- CI **excludes** the null (HR upper bound < 1 for a protective effect, or lower bound > 1 for harm) → "**was** associated with a statistically significant improvement."
- CI **crosses** 1 → "**was not** associated with a statistically significant improvement."

Never label a result significant or non-significant from intuition about the drug. The bracket decides.

### Single trial vs meta-analysis

Read the **Trial Used** column for that row:

- **One trial** → name it directly: *"(PROfound; …)"* and use plain verb phrasing ("olaparib was associated with…").
- **Two or more trials** → the row is a pooled estimate; lead with *"meta-analysis showed that …"* and list all trial names in the parenthetical: *"(D-CARE, ABCSG-18; …)."*

### Ordering of subsections

Order the numbered subsections to **lead with the strongest evidence**:

1. First, comparisons with a **statistically significant** result.
2. Within that, and within the non-significant group, sort by **certainty of evidence**: high → moderate → low → very low.

This mirrors CQ7, which led with the AGO trial (the only significant OS benefit) and then descended through moderate- and low-certainty comparisons. When the document's tables are not already in this order, write the narrative in the target order and use `scripts/reorder_comparison_blocks.py` to move the table blocks to match, then renumber the subtitles top-to-bottom (see `references/xml-patterns.md`). **Caveat:** if the document's tables are already laid out in a fixed numerical order that the user clearly wants preserved (the subtitles are pre-numbered X.1, X.2, … and renumbering would desync them from the tables), keep the existing order and match each narrative item to its table. When in doubt, ask. Stratified subgroups of a single comparison (overall → premenopausal → postmenopausal, as in CQ19) stay in their natural clinical order, not re-sorted.

### Table subtitle reformatting

The input tables usually carry a **bold** subtitle. Convert each to **italic + underline**, prefixed with the subsection number, matching the other CQ sections:

- Input: **`Denosumab versus Placebo (Premenopausal)`** (bold)
- Output: *`19.2 Denosumab versus Placebo (Premenopausal)`* (italic, underlined)

### Control-arm footnote

Under **each** SoF table, add the footnote (10 pt, superscript dagger marker style as in CQ7/16/19):

> † Calculated using event rate in the control/comparator arm.

Preserve any certainty/imprecision footnote already present (e.g., the "^a^ Very serious imprecision…" note) — add the dagger footnote alongside it, do not replace it.

## Data fidelity rules (do not skip)

- **Only use data in the attached document.** No outside HRs, no remembered trial results, no "the real monarchE number is…". If a value looks wrong, flag it to the user rather than silently changing it.
- **Transcribe brackets exactly.** `HR, 0.68 [95% CI, 0.40 to 1.13]` — same digits, same order, "to" not a dash, inside square brackets.
- **Do not invent outcomes or comparisons.** If the table only reports DFS, the narrative only discusses DFS.
- **Match trial names to the Trial Used column verbatim** (including spelling/casing as the document uses, e.g., "OlympIA" vs "Olympia" — match the source).
- **Keep the prose human and flowing**, in complete sentences, no filler. Concise, declarative, past tense, third person.

## References

- `references/house-style.md` — full phrasing templates, three complete worked examples (CQ7, CQ16, CQ19), and edge cases (mixed-significance comparisons, stratified subgroups, multi-outcome rows, certainty-downgrade sentences). **Read before drafting.**
- `references/xml-patterns.md` — copy-paste XML for the opening paragraph, numbered subsection paragraphs, italic+underline subtitles, control-arm footnote, and spacer paragraphs, plus the unpack/edit/repack command sequence.
