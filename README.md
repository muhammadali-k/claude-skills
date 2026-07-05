# Claude Skills

Personal collection of [Claude Code skills](https://code.claude.com/docs/en/skills) for clinical evidence-synthesis work (systematic reviews, living guidelines, GRADE/PICO abstraction).

## Skills

| Skill | What it does |
|---|---|
| [`itable-extraction`](itable-extraction/) | Extracts data from clinical-trial / systematic-review publications into a structured "i-table" via a multi-agent extract → verify → assemble → validate pipeline. Handles per-arm columns, derives value formats from example rows, attaches per-value provenance, and produces an upload-ready file. |
| [`outcomes-extraction`](outcomes-extraction/) | Extracts time-to-event outcomes (OS, DFS/PFS, RFS) and response outcomes (ORR, pCR) from trial publications into per-comparison outcome tables — hazard ratio + 95% CI, events/N per arm, landmark rates — with provenance. |
| [`study-question-tagging`](study-question-tagging/) | Assigns included studies to the clinical questions (CQs) of a guideline or systematic review by reading the actual publications, and emits one filtered spreadsheet per question. |

Each skill folder contains a `SKILL.md` (trigger description + instructions), plus supporting `references/`, `scripts/`, `assets/`, and `evals/`.

## Installation

Copy (or symlink) a skill folder into `~/.claude/skills/`:

```bash
cp -R itable-extraction ~/.claude/skills/
```

Claude Code picks it up automatically; invoke it by describing a matching task or via the `Skill` tool.
