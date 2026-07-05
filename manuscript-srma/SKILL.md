---
name: manuscript-srma
description: Write, edit, or evaluate evidence-synthesis manuscripts — systematic reviews (with or without meta-analysis), pairwise meta-analyses, and network meta-analyses, including living and interactive reviews. Use this whenever someone is drafting, revising, structuring, or quality-checking any part of a systematic review, meta-analysis, or network meta-analysis paper, for example writing or editing an Introduction, Methods, Results, or Discussion; building a GRADE summary-of-findings section, a PRISMA or PRISMA-NMA methods passage, or a structured abstract; adapting a manuscript to a target journal such as European Urology, JAMA, or Mayo Clinic Proceedings; or assessing a draft against reporting standards. Trigger this even when the user only says things like "help me write up my systematic review", "draft my meta-analysis methods", or "review my network meta-analysis manuscript" without naming a specific section, and even if they do not use the word skill.
license: Proprietary
---

# Manuscript-SRMA: evidence-synthesis manuscripts

This skill drafts, edits, and evaluates manuscripts for **systematic reviews and meta-analyses**, in the style of a living-evidence research program (living interactive systematic reviews built on the LIvE synthesis framework). The same paper may be a **systematic review only** (structured synthesis, no pooling), a **systematic review + pairwise meta-analysis**, or a **systematic review + network meta-analysis** — and may or may not be *living* and/or *interactive*. The applicable guidance changes with the project type, so **scope the project before writing**.

## Three modes

- **Write** — draft a section (or a whole manuscript). Always run the scoping intake first.
- **Edit** — revise an existing draft toward the house style; tighten claims; enforce the reporting conventions below.
- **Evaluate** — score a draft against the rubric; report Pass / Partial / Fail with reasons and a prioritized fix list.

Identify the mode from the request, then follow the matching workflow near the end of this file.

---

## Scope the project first (mandatory in Write mode)

Before drafting, establish the project's shape. **Ask Q1, Q5, and Q6 explicitly** unless the conversation already answers them. Infer Q2–Q4 from context and **state the assumptions you made** rather than interrogating the user — for a small, well-specified request (e.g., "write a systematic review introduction") proceed with sensible defaults and a one-line note of what you assumed, exactly as a careful co-author would.

- **Q1 — Project type (ask).** Systematic review only / + pairwise meta-analysis / + network meta-analysis / + both. This sets the applicability tags below.
- **Q2 — Living and interactive (default both on).** Living review with a recurring auto-search? Companion interactive "living-evidence" website?
- **Q3 — Report stage.** Initial report or living update of a prior report? If update, get the prior citation and what is new.
- **Q4 — Target journal.** European Urology / JAMA family / Mayo Clinic Proceedings / other. Loads the journal adapter; fixes the reporting standard (PRISMA 2020 for SR/MA; PRISMA-NMA for NMA).
- **Q5 — Available inputs (ask).** Which inputs does the user have? See the input checklist in `references/sections.md` (§ "Required inputs"). For every missing input, **insert a placeholder — never fabricate** (see below).
- **Q6 — Sections to write (ask).** Whole manuscript or a named subset. Write **only** what is requested.

**Project type → tags:** SR-only enables `[SR-only]`; + pairwise enables `[MA]`; + network enables `[MA]` and `[NMA]`.

### Review-type applicability tags

Guidance throughout the reference files is tagged. Apply only what matches the scoped project:

- **[ALL]** — systematic review, pairwise, and network.
- **[MA]** — any meta-analysis (pairwise and/or network); **skip for SR-only**.
- **[NMA]** — network meta-analysis only.
- **[SR-only]** — substitute behaviour when there is no pooling (structured / SWiM-style synthesis).

---

## The placeholder rule — never fabricate a missing input

When an input is missing, write the heading and whatever text the available inputs support, then mark the gap with an unmissable, greppable token. Do not invent numbers, citations, dates, or claims.

```
### Network meta-analysis
⟦PLACEHOLDER — NMA results: provide league tables, P-scores/SUCRA, and per-outcome
contributing-study counts to complete this subsection.⟧
```

Inline gaps use the same token: *"As of ⟦PLACEHOLDER — search cut-off date⟧, the review includes ⟦PLACEHOLDER — N⟧ studies."* At the end of any drafted section, **list the placeholders** so the user sees exactly what is outstanding. `scripts/find_placeholders.py` lists every remaining token in a file.

---

## Non-negotiables (always in force)

These hold across modes and project types; they are what reviewers check and what keeps the corpus consistent.

- **Numbers must reconcile.** Every figure in the text matches the tables/figures and the abstract. After a living update, re-check this especially.
- **Don't fabricate.** Missing data → placeholder, never an invented value or citation.
- **Hedge sparse/indirect evidence** ("may", "potentially", "appears to"). **[NMA]** Never state a ranking as a head-to-head conclusion.
- **GRADE for every patient-important outcome.** **[MA]** Report relative *and* absolute effects (per 1000) in the summary-of-findings; **[NMA]** rate network estimates additionally on incoherence and intransitivity.
- **[NMA] Ranking caveat.** Interpret P-scores/SUCRA only in congruence with the pairwise estimates.
- **Reconciliation with prior reviews** is a defining feature — include the reconciliation figure/table.
- **[NMA] League-table colour semantics:** green = benefit (light NS, dark significant), red = harm (light NS, dark significant).
- **Platform tone by journal.** Foreground the interactive website for European Urology / Mayo Clinic Proceedings; downplay it for JAMA and disclose it is not peer-reviewed where required. Omit platform mentions entirely if the project is not interactive.
- **Housekeeping:** OSF registration; correct reporting standard; credit the medical librarian; define abbreviations at first use and in every legend.

---

## Genre DNA (condensed)

A one-time comprehensive search becomes a recurring auto-search feeding a semi-automated, human-in-the-loop pipeline (ML RCT filter → two-reviewer screening/extraction → auto-updated PRISMA). Direct (pairwise) evidence is reported alongside indirect/mixed evidence **[NMA]**; certainty is graded; effects are shown in absolute and relative terms **[MA]**; results are reconciled against prior reviews and (if interactive) rendered as interactive tables, league tables, network/forest/ranking plots, evidence maps, and dynamic summary-of-findings tables. The whole apparatus serves shared decision-making.

## Initial report vs living update

- **Initial:** introduce and motivate the framework; describe the full pipeline and all methods (in text + supplement); reconcile against all prior reviews.
- **Update:** abbreviate Methods and defer to the initial report — *"Detailed methods were published with the initial report and are provided in the Supplementary material [cite]."* State precisely what is new (trials, follow-up, subgroups) and whether the picture is consistent; call out any reversal of a prior conclusion explicitly.

Full detail: `references/sections.md` (§ "Initial vs update").

---

## Mode workflows

### Write
1. Run the scoping intake above; record project type, toggles, stage, journal, available inputs, and requested sections.
2. Read **`references/sections.md`** for the section(s) requested. Additionally read **`references/methods-stats.md`** when drafting Methods or any analysis text; **`references/boilerplate.md`** for reusable, pre-cited sentences; and **`references/journals/<target>.md`** for the abstract schema, required boxes, and contributions/disclosure format. Load only what the task needs.
3. Draft **only the requested section(s)**, applying the tags for the project type. Insert placeholders for missing inputs and list them at the end. Match the target journal's structure.

### Edit
1. Identify project type and target journal (ask only if unclear).
2. Read **`references/sections.md`** and, as relevant, **`references/methods-stats.md`** and **`references/boilerplate.md`**.
3. Revise toward the house style and enforce the non-negotiables. Where a number is missing or cannot be verified, flag it or insert a placeholder — do not supply an invented value. Preserve the author's voice; explain substantive changes briefly.

### Evaluate
1. Determine the project type first (read the draft's title/methods); this selects which rubric items apply.
2. Read **`references/evaluation-rubric.md`**. Apply **only** the items whose tag matches — never penalize an SR-only paper for lacking a league table, or a pairwise paper for lacking incoherence assessment.
3. Optionally run `scripts/find_placeholders.py` (outstanding gaps) and `scripts/extract_estimates.py` (pull reported estimates/counts for a consistency check against tables).
4. Report each applicable item as Pass / Partial / Fail with a one-line reason; mark Critical-item failures as blockers; end with a short, prioritized fix list.

---

## Reference map

| Need | Read |
|---|---|
| How to write a specific section (Title → Conclusions), tables/figures, platform write-up, initial-vs-update detail, required-inputs checklist | `references/sections.md` |
| Analysis conventions (pairwise / NMA / SR-only), model choice, rankings, GRADE, the absolute-risk-difference formula, canonical citations | `references/methods-stats.md` |
| Reusable, pre-cited sentences (reporting opener, living search, screening pipeline, model-choice justification, ranking caveat, GRADE footnote, limitations) | `references/boilerplate.md` |
| Journal-specific abstract schema, boxes, supplement depth, contributions/disclosures, reference style | `references/journals/european-urology.md`, `references/journals/jama.md`, `references/journals/mayo-clinic-proceedings.md` |
| The QC checklist and common reviewer pitfalls (evaluate mode) | `references/evaluation-rubric.md` |
| Blank templates to fill | `assets/study_characteristics_table_template.md`, `assets/sof_table_template.md` |
| Find leftover placeholders / extract reported estimates | `scripts/find_placeholders.py`, `scripts/extract_estimates.py` |
