# Orchestration: jobs, schemas, prompts, configs

The deliverable's trustworthiness comes from the **two-independent-reviewer + senior-adjudicator**
design: per paper, Reviewer A and Reviewer B extract concurrently on **different models**, neither
seeing the other; concordance is computed **in code as a recorded metric, not a gate**; then a
**senior reviewer on a pinned strong model re-reads every source in full and re-derives every value**,
including the ones both reviewers agreed on. Anything the senior cannot settle from source goes to
`unresolved[]` for a **human**. Papers run concurrently and pipelined via the Workflow tool using
`assets/extract_outcomes.js`.

Workflow scripts cannot read files, so you pass everything through `args`. The agents they spawn CAN read
files (PDFs via the Read tool, with a page range for >10-page files; `.docx` pre-converted to txt).

## Template families — every job must declare one
`pwma`, `nma`, `pwma_subgroup` (layouts in `table-layout.md`). The family decides the row rule
(overall population vs one row per subgroup level) and how counts are written. `scaffold.py` detects
it from each file's header and stamps it on every `needed` item. **Never let a job item go out
without a `family`** — the reviewers need it to know whether they are extracting the ITT population
or a subgroup, and the senior needs it to check the counts.

## The node vocabulary — one path, declared once
Every job list carries a **`vocabulary`** path: the project's `*_node_vocabulary.json`. Pass the jobs
wrapped in the config object so it has somewhere to live:

```json
{ "vocabulary": "/abs/Extraction/periopRCC_node_vocabulary.json",
  "models": { "a": "opus", "b": "sonnet", "senior": "opus" },
  "jobs": [ ... ] }
```

Both reviewers and the senior are given that path and **read the file first**. `netmeta` joins arms by
string equality, so `NIVO + IPI` and `NIVO+IPI` are two nodes and the sheet gives no sign of it —
labels are looked up, never composed. Rules (full text in `node-vocabulary.md`): UPPERCASE 3–5-char
agent labels; combinations joined by a bare `+` with **no spaces**; component order taken from the
vocabulary's `combinations` list rather than derived; **one** pooled comparator label (default `NOADJ`)
with the actual control recorded separately; dose/duration/setting variants hyphen-suffixed and part of
the node identity. A label an agent cannot resolve is a **FLAG, never a guess**.

Omitting `vocabulary` is allowed but the script warns: the run then emits whatever wording each agent
read off the page, and the mismatch is only caught later by `qc.py --vocabulary`, if at all.

## jobs.json — one entry per UNIQUE paper
**`scripts/scaffold.py` generates this file** (plus `assemble_config.json` and `add_rows_config.json`)
as a skeleton from the template files + sources dir: it matches source files to each study by
author+year and pre-fills the needed `(table, family, comparison, subgroup)` tuples from the
pre-seeded rows. You then fill `design` (anchor numbers from the abstract) and the
`treatment`/`control` defaults, and verify the flagged file matches. The structure (fill the rest by
hand if you skip the scaffolder):

```json
[
  {
    "paper_id": 1483,
    "trial": "IMmotion010",
    "pmid": "36099926",
    "nct": "NCT03024996",
    "files": ["/abs/2022_Pal_Lancet.pdf", "/abs/2022_Pal_Lancet_suppl.pdf"],
    "design": "Adjuvant atezolizumab vs placebo, resected RCC at increased risk. 2 arms, ITT 390/388. DFS HR 0.93 (0.75-1.15). Anchors help you LOCATE values - still confirm in the text.",
    "needed": [
      {"table":"PWMA","family":"pwma","comparison":"Primary",
       "treatment":"ATEZO","control":"NOADJ",
       "note":"Overall ITT DFS HR/CI, events/N per arm, landmark DFS rate."},

      {"table":"NMA","family":"nma","comparison":"Primary",
       "treatment":"ATEZO","control":"NOADJ",
       "note":"T1=ATEZO, T2=NOADJ (actual control: placebo). Same ITT numbers as the PWMA row."},

      {"table":"SUB","family":"pwma_subgroup","comparison":"Primary",
       "subgroup":"Risk group: M1 NED",
       "treatment":"ATEZO","control":"NOADJ",
       "note":"M1-NED stratum only. If not reported for this stratum, extraction_possible=No + all NA."},
      {"table":"SUB","family":"pwma_subgroup","comparison":"Primary",
       "subgroup":"Risk group: High",
       "treatment":"ATEZO","control":"NOADJ","note":""}
    ]
  }
]
```
- `comparison` is the **exact col-F (or col-H, on subgroup sheets) label** of the pre-seeded /
  to-be-added row — the agent echoes it back so assembly can place the result.
- `subgroup` is **required on `pwma_subgroup` items** and is the exact col-F label. Row identity on
  that sheet is (paper_id, comparison, subgroup); a re-worded label orphans the row.
- **List one item per required subgroup level.** The number of levels **varies by study** — take it
  from the sheet (scaffold does), never from a fixed list.
- `treatment`/`control` are *defaults* and **must be canonical node labels from the vocabulary**
  (`ATEZO`, `NIVO+IPI`, `SOR-1Y`, `NOADJ`) — not the paper's prose. They are what the agent echoes back
  into the sheet, so a prose default is a prose node. The agent still confirms/flips them against the
  paper. On `nma`, treatment = T1 and control = T2 (the active comparator). A control that is an
  **active regimen** (add-on design) takes that regimen's label, not `NOADJ`.
- `files` are absolute paths; include supplements. Convert `.docx` first: `textutil -convert txt`.

## Passing jobs to the workflow
`extract_outcomes.js` accepts either the bare jobs array or
`{ vocabulary: '/abs/..._node_vocabulary.json', jobs: [...], models: { a: 'opus', b: 'sonnet',
senior: 'opus' } }` as the Workflow `args` (the bare-array form stays supported and simply has no
vocabulary, which the script warns about). For a
large job list (or to make the run resumable), bake it into a copy of the script instead — replace
`const cfg = ...` input with the JSON — and run that file via `scriptPath`. Save the workflow's
returned `{papers:[...], run_metrics:{...}}` to `_work/extraction_results.json` (it's in the task
output file — parse out the `result` object), and report `run_metrics` to the user.

## Per-paper result schema (the workflow validates this)
Each paper returns: `paper_id, trial_name, nct, pmid, of_recommendation ("O"|"F"), results[], paper_flags[]`.
Each item in `results[]`:
```
table (echo the requested key), family, comparison (echo), subgroup (echo; "NA" on main sheets),
extraction_possible ("Yes"|"No"|"NA"; "NA" on main sheets),
endpoint_used, treatment_name, control_name, hr, ci_lower, ci_upper,
surv_treatment, surv_control, surv_timepoint, median_treatment, median_control,
et, nt, ec, nc, flags[], provenance[{field, source, snippet}]
```
**`et`/`nt`/`ec`/`nc` always carry the PWMA meaning** — events-treatment, N-treatment, events-control,
N-control — *in every family, including `nma`*. `assemble.py` performs the NMA relabelling
(events → `Ec T?`, N → `Et T?`) once, at write time. No agent ever holds two conventions.

**`treatment_name`/`control_name` are canonical node labels** from the vocabulary, not prose. The script
shape-checks every one it gets back and reports `non_canonical_labels` in `run_metrics`; membership in
the vocabulary is checked authoritatively later by `qc.py --vocabulary`, which fails the run.

The **senior** returns the same object plus `adjudications[]` (one entry per field where any of the
three differ, with `value_a`, `value_b`, `senior_value`, `agreed_with` ∈ A/B/both/neither, `reason`),
`unresolved[]` (`table`, `comparison`, `subgroup`, `field`, `why` — for a **human**, with the cell
left `NA`), and `confidence`. Assembly uses the senior's `results[]`.

## Agent prompts (the spirit)
- **Reviewer A / Reviewer B** (identical brief, different models, run concurrently, neither sees the
  other): "Extract OUTCOME data for ONE publication, independently. Read ONLY these files. You are
  told the TEMPLATE FAMILY for each required row — `pwma`/`nma` rows are the **overall ITT
  population**; `pwma_subgroup` rows are **that named subgroup level only**. For each required item:
  set the endpoint, HR as treatment-vs-control (invert + flag if reversed), landmark event-free
  rates, events/N per arm using the PWMA key meaning, medians (usually NA). On subgroup rows answer
  `extraction_possible` honestly and NA the row when it is `No`. Emit per-field provenance with
  snippets; `NA` anything unreported; flag every judgment call. Also judge O/F. **Read the node
  vocabulary first and set `treatment_name`/`control_name` to canonical labels from it — never the
  paper's wording; a label you cannot resolve is a FLAG, never a guess.**"
- **Senior:** "STEP 1 — re-open and read EVERY source file IN FULL, from scratch, **before** looking
  at either draft; render and read KM curves and forest plots, many HRs/CIs exist only as images.
  STEP 2 — derive EVERY required value yourself, including ones both reviewers agreed on; agreement
  means a value was legible, not that it is correct. STEP 3 — only then compare against the two
  drafts and log an adjudication for every field where any of the three differ. Do NOT split the
  difference; anything you cannot prove from source goes to `unresolved[]` for a human with the value
  left `NA`. Check events ≤ N in every row before returning. **Adjudicating the arm labels is part of
  the job:** re-check every `treatment_name`/`control_name` against the vocabulary — exact canonical
  string, `+` with no spaces, component order as the `combinations` list has it, the single pooled
  comparator label unless the control is an active regimen, the right variant suffix. A reviewer's
  prose wording is an error to correct, not a value to carry through; a label neither the vocabulary
  nor its aliases resolve goes to `unresolved[]`."

Use `effort: 'high'` for all three — these reads are dense (KM curves, forest plots, supplementary tables).

## Adapting rigor
Default = two independent reviewers + senior adjudication per paper. **Concordance is a recorded
metric and never a gate** — the senior re-derives everything regardless. If the Workflow tool isn't
available, run the same three roles inline, one paper at a time, preserving independence: produce A's
full answer, then B's *without consulting A*, then adjudicate from source. For a quick single-paper
fill you may collapse to one reviewer + a source-checking senior — but say so.

## Targeted re-reads
When you add a comparison or subgroup row after the main run, or need one value the first pass missed
(e.g. a forest-plot HR for one risk stratum), spawn a single focused agent for just that value rather
than re-running everything — give it the file paths, the exact table/family/comparison/subgroup, and
an anchor to cross-check (e.g. the sibling level's known events/N, or the overall-population row).
Append the result object to `extraction_results.json`.

## assemble.py config (`_work/assemble_config.json`)
```json
{
  "results": "_work/extraction_results.json",
  "today": "2026-07-28",
  "files": {
    "PWMA": {"path": "/abs/PWMA/pwma_template.xlsx", "family": "pwma"},
    "NMA":  {"path": "/abs/NMA/nma_template.xlsx",  "family": "nma"},
    "SUB":  {"path": "/abs/PWMA/pwma_subgroup_template.xlsx", "family": "pwma_subgroup"}
  },
  "study_info": {
    "1483": {"trial_name":"IMmotion010","nct":"NCT03024996","pmid":"36099926","arms":"2"},
    "1523": {"trial_name":"ASSURE","nct":"NCT00326898","pmid":"26969090","arms":"3"}
  }
}
```
`files` also accepts the legacy `"KEY": "/abs/path.xlsx"` form; the declared `family` is informational
— every script re-detects it from the file's own header. `study_info` keys are paper IDs (strings);
`arms` = the trial's TOTAL arm count. `pmid`/`trial_name`/`nct` here override the agent values (use
the most authoritative source). Run:
`python scripts/assemble.py --config _work/assemble_config.json`.

## add_rows.py config (`_work/add_rows_config.json`) — for rows missing from the template
```json
{
  "files": {"NMA": {"path":"/abs/NMA/nma_template.xlsx","family":"nma"},
            "SUB": {"path":"/abs/PWMA/pwma_subgroup_template.xlsx","family":"pwma_subgroup"}},
  "new_rows": {
    "NMA": {"1523": ["Sorafenib"]},
    "SUB": {"1553": [{"comparison": "Primary",
                      "subgroups": ["Risk group: High", "Risk group: M0 High"]}],
            "1515": [{"comparison": "3 year Sorafenib", "subgroup": "Risk group: M1 NED"}]}
  }
}
```
Main sheets take a list of comparison labels. **Subgroup sheets take `{comparison, subgroups[]}`
objects, so each study gets its own, variable, number of new rows** — that is the whole point; there
is no fixed level count. It copies the study's pre-seeded metadata (Paper ID, Author, Title, Publish
Date, Publication ID), sets the key columns, inserts each row after the matching study/comparison
block so levels stay contiguous, leaves "Extraction Possible" blank for the extraction to answer, and
clears the data fields for assemble to fill. Rows that already exist are reported and skipped. Add the
matching result objects to `extraction_results.json` first, then run
`python scripts/add_rows.py --config _work/add_rows_config.json`, then re-run assemble.
