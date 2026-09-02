# Claude Skills

Personal collection of [Claude skills](https://code.claude.com/docs/en/skills) — for Claude Code and claude.ai — covering clinical evidence-synthesis work, academic writing/presenting, and residency-application tooling.

## Clinical evidence synthesis

| Skill | What it does |
|---|---|
| [`itable-extraction`](itable-extraction/) | Extracts data from clinical-trial / systematic-review publications into a structured "i-table" via a multi-agent extract → verify → assemble → validate pipeline. Handles per-arm columns, derives value formats from example rows, attaches per-value provenance, and produces an upload-ready file. |
| [`outcomes-extraction`](outcomes-extraction/) | Extracts time-to-event outcomes (OS, DFS/PFS, RFS) and response outcomes (ORR, pCR) from trial publications into per-comparison outcome tables — hazard ratio + 95% CI, events/N per arm, landmark rates — with provenance. |
| [`study-question-tagging`](study-question-tagging/) | Assigns included studies to the clinical questions (CQs) of a guideline or systematic review by reading the actual publications, and emits one filtered spreadsheet per question. |
| [`guideline-lit-review`](guideline-lit-review/) | Drafts the narrative literature-review prose for a clinical-practice-guideline question directly from its populated Summary-of-Findings / GRADE tables, inserting the text into the existing .docx (ASCO house style) without altering the tables. |
| [`sof-gradepro-export`](sof-gradepro-export/) | Converts per-outcome Summary-of-Findings Excel exports (one file per outcome, or a folder for one PICO) into a single combined GRADEpro GDT JSON-LD file for MAGICapp's beta PICO import — live-verified against a real import. Computes the absolute-effect confidence interval, and generates a GRADE-conventions plain-language summary and recommended "Direction of benefit" per outcome, writing all three to a post-import checklist since MAGICapp's beta importer can't be made to set them via the JSON-LD file itself. |
| [`lisr-pdf-downloader`](lisr-pdf-downloader/) | Retrieves full-text PDFs and supplements for systematic-review screening rounds (open-access resolution, identifier matching, browser-download playbook, round-by-round status tracking). |
| [`treatment-group-namer`](treatment-group-namer/) | Maps individual treatment comparisons (drug-level regimens) to their treatment-group drug-class labels for the two-level "Treatment Group then Individual Treatment" hierarchy in living-guideline evidence modules — a deterministic string transformation backed by an editable drug-to-class map, preserving arm order and structure. |

## Literature monitoring

| Skill | What it does |
|---|---|
| [`studies-fetch`](studies-fetch/) | Daily cross-sectional literature digest for hematology, oncology, and medical AI. Queries ~44 high-impact journals via the PubMed E-utilities API (stdlib Python, no key), drops any study already shown on a previous day (persistent seen-PMID store + rolling window), and produces a ranked, grouped markdown digest (Heme / Onc / Medical AI) with one-line relevance notes. Journal list is a simple editable JSON with a `check` command to validate abbreviations. |

## Academic writing & presenting

| Skill | What it does |
|---|---|
| [`academic-pptx`](academic-pptx/) | Builds academic-style PowerPoint decks (journal clubs, grand rounds, lectures, conference talks) with restrained publication-quality design — role-based color palette, message-based slide titles, natural speaker notes — on top of the pptx skill. |
| [`manuscript-srma`](manuscript-srma/) | Drafts, edits, and rubric-evaluates systematic-review / meta-analysis / NMA manuscripts (including living and interactive reviews) with journal-specific adapters, GRADE/PRISMA conventions, and a strict never-fabricate placeholder rule. |
| [`abstract-review`](abstract-review/) | Peer-reviews a research abstract/manuscript `.docx` — emitting real Word tracked changes + threaded comments under a named reviewer, tailored by a research-type profile (evidence synthesis, RCT, observational, other-clinical, AI/ML/LLM). Does fresh reviews and re-reviews of a revision against the prior round's comments; a proven, self-validating OOXML engine (`scripts/docx_review.py`) keeps the tracked changes/comments Word-clean. The review sibling of `manuscript-srma`. |
| [`manuscript-writing`](manuscript-writing/) | Drafts, organizes, and revises my own manuscripts and conference abstracts in my personal academic voice — across all my research types (clinical/epi cohort, AI/LLM-methods, and SR/MA/NMA). Distilled from ~23 of my real submitted papers into a voice signature, phrase bank, section-by-section playbook, statistical-reporting fingerprints (the inline effect triple, the compact `(coef; p)` pair, the absolute per-1000 translation), and a skeleton-first/tables-first organization workflow with an end-of-draft copyedit pass for my recurring slips. The voice + organization companion to `manuscript-srma` (which owns SR/MA reporting mechanics); not for marking up someone else's `.docx` — that's `abstract-review`. |

## Residency application

| Skill | What it does |
|---|---|
| [`im-open-houses`](im-open-houses/) | Daily watcher for **virtual open houses / info sessions of Internal Medicine residency programs**: web-discovers newly posted events, de-duplicates against a committed state file so each event is reported exactly once, tags every event against my tiered 568-program list (tier, ★ priority, visa, grad-year-cutoff risk), and delivers an 8 AM (America/Phoenix) digest by email + Google Calendar from a cloud routine running Opus 4.8. On request (`/im-open-houses signup 1,3`) registers me for chosen events via the browser using a local-only profile (IDs never committed). `ROUTINE.md` documents the exact routine config. |
| [`new-im-programs`](new-im-programs/) | Tracks **newly ACGME-accredited categorical Internal Medicine residency programs** from the authoritative ACGME ADS public data system (browser-assisted, robots-respectful) — classifies each as apply-now-first-class / apply-now-still-new / pre-accreditation watchlist by original accreditation date, diffs against the last run to flag what's new, and renders a sortable/filterable HTML tracker. The discovery front-end to `residency-program-finder`. Live-validated (64 programs on 2026-08-29). |
| [`residency-program-finder`](residency-program-finder/) | Searches and verifies internal-medicine residency programs for IMG applicants — roster-confirmed affinity counts, visa/signal/tier tracking, Residency Explorer integration — and renders a verified program list as an Excel workbook and a self-contained interactive HTML apply list. |
| [`eras-authors`](eras-authors/) | Reformats a pasted publication author list into ERAS's `Lastname` + initials, comma-separated format (e.g. `Cameron Blake Smith` → `Smith CB`), and flags Muhammad Ali Khan's own entry as `Khan MA` so it can be selected and bolded with ERAS's "B" button after pasting. |

## Claude model & workflow tooling

| Skill | What it does |
|---|---|
| [`fable5-working-style`](fable5-working-style/) | Teaches a session how Claude Fable 5 thinks and how it differs from Claude Opus 4.8 — behavioral profile, API/effort differences, safety-classifier notes — plus a playbook for making Opus 4.8 adopt Fable-5-style patterns (delegation thresholds, fresh-context verification, memory use, scoped search-first, calibrated autonomy), with research-workflow applications and Fable-quirk countermeasure snippets. |
| [`route`](route/) | On-demand two-model build loop (`/route`) with a fixed chain of command: the Claude session (Fable 5 / Opus 4.8) plans and orchestrates — always the boss, always the adversarial reviewer; every delegated build reroutes to OpenAI's GPT-5.6 Sol in Ultra Mode via headless `codex exec` (instead of Claude subagents), falling back to an Opus 4.8 subagent worker only when Sol is unavailable (usage limit hit, auth outage, model id dead). Loops build → review → fix until the boss approves; covers any buildable task, not just code. Every CLI invocation live-verified against codex-cli 0.144.x, with the non-obvious traps handled: `codex exec resume` sandbox/workdir re-assertion, exit-0-on-error success checks, session-id capture from stderr, model-id fallback chain, usage-limit/auth-failure detection and mid-loop worker takeover, dirty-tree change attribution, non-git file-snapshot review, out-of-tree write sweeps on the unsandboxed Opus path, and never-mutate-real-data review rules. Hardened from the Actionable AI "/route Setup Guide". |

## Third-party

| Skill | What it does |
|---|---|
| [`council`](council/) | Convenes seven debating expert personas (Adversary, Strategist, Scientist, Visionary, Engineer, Philosopher, Humanist) to stress-test a decision, then delivers a structured verdict with confidence, risks, next steps, and a minority report. Adapted from [Claude Council](https://github.com/itshussainsprojects/Claude-Council-Skill) by Hussain Ali (MIT). Not my own work — kept here for convenience. |

## Notes on completeness

- `academic-pptx` and `manuscript-srma` ship as standalone `SKILL.md` files. Both reference supporting `references/` / `scripts/` / `assets/` files that no longer exist on local disk (only the SKILL.md survived the claude.ai upload); the instructions are self-contained enough to work, but the full bundles would need to be re-exported from claude.ai if they still exist there.
- `residency-program-finder`'s example JSON in `scripts/README.md` uses placeholder applicant data.

## Installation

**Claude Code:** copy a skill folder into `~/.claude/skills/`:

```bash
cp -R itable-extraction ~/.claude/skills/
```

**claude.ai:** zip the folder (or use skill-creator's packager) and upload it under Settings → Capabilities → Skills.
