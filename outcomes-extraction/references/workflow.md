# Orchestration: jobs, schemas, prompts, configs

The deliverable's trustworthiness comes from **independent verification**: per paper, an extractor emits
values with provenance, then a verifier re-derives every value from the same sources and reconciles.
Papers run concurrently and pipelined via the Workflow tool using `assets/extract_outcomes.js`.

Workflow scripts cannot read files, so you pass everything through `args`. The agents they spawn CAN read
files (PDFs via the Read tool, with a page range for >10-page files; `.docx` pre-converted to txt).

## jobs.json — one entry per UNIQUE paper
**`scripts/scaffold.py` generates this file** (plus `assemble_config.json` and `add_rows_config.json`) as a
skeleton from the to_extract files + sources dir: it matches source files to each study by author+year and
pre-fills the needed `(table, comparison)` tuples from the pre-seeded rows. You then fill `design` (anchor
numbers from the abstract) and the `treatment`/`control` defaults, and verify the flagged file matches.
The structure (fill the rest by hand if you skip the scaffolder):

```json
[
  {
    "paper_id": 33451,
    "trial": "SOFT (8-year)",
    "pmid": "29863451",
    "nct": "NCT00066690",
    "files": ["/abs/2018_Francis_NEJM.pdf", "/abs/2018_Francis_NEJM_suppl.pdf"],
    "design": "Premenopausal HR+. 3 arms: tamoxifen alone, tamoxifen+OFS, exemestane+OFS. Primary = T+OFS vs T-alone. 8y DFS 78.9/83.2/85.9; 8y OS 91.5/93.3/92.1. Anchors help you LOCATE values - still confirm in the text.",
    "needed": [
      {"table":"OS","comparison":"Primary","treatment":"Tamoxifen plus ovarian function suppression","control":"Tamoxifen alone","note":"T+OFS vs T-alone OS HR/CI, deaths/N, 8y OS rate."},
      {"table":"OS","comparison":"Exemestane + ovarian suppression vs Tamoxifen alone","treatment":"Exemestane plus ovarian function suppression","control":"Tamoxifen alone","note":"E+OFS vs T-alone."},
      {"table":"DFS","comparison":"Primary","treatment":"Tamoxifen plus ovarian function suppression","control":"Tamoxifen alone","note":"..."},
      {"table":"RFS","comparison":"Primary","treatment":"Tamoxifen plus ovarian function suppression","control":"Tamoxifen alone","note":"Recurrence-specific endpoint (BCFI); use closest + flag."}
    ]
  }
]
```
- `comparison` is the **exact col-F label** of the pre-seeded (or to-be-added) row — the agent echoes it
  back so assembly can place the result. For multi-arm trials, list every comparison the paper reports.
- `treatment`/`control` are *defaults*; the agent confirms/flips against the paper.
- `files` are absolute paths; include supplements. Convert `.docx` first: `textutil -convert txt`.

## Passing jobs to the workflow
`extract_outcomes.js` reads `const jobs = args`. Pass the jobs array as the Workflow `args`. For a large
job list (or to make the run resumable), bake it into a copy of the script instead — replace
`const jobs = args;` with `const jobs = <the JSON>;` and run that file via `scriptPath`. Save the
workflow's returned `{papers:[...]}` to `_work/extraction_results.json` (it's in the task output file —
parse out the `result` object).

## Per-paper result schema (the workflow validates this)
Each paper returns: `paper_id, trial_name, nct, pmid, of_recommendation ("O"|"F"), results[], paper_flags[]`.
Each item in `results[]`:
```
table ("OS"|"DFS"|"RFS"), comparison (echo the requested label), endpoint_used,
treatment_name, control_name, hr, ci_lower, ci_upper,
surv_treatment, surv_control, surv_timepoint, median_treatment, median_control,
et, nt, ec, nc, flags[], provenance[{field, source, snippet}]
```
All values are strings; unreported → `"NA"`. The **verifier** returns the same object (reconciled, with
final values it can prove) plus `disagreements[]` (every field it changed, with reason) and a
`confidence` note. Assembly uses the verifier's object.

## Agent prompts (the spirit)
- **Extractor:** "Extract OUTCOME data for ONE publication. Read `references/conventions.md` rules
  (restated inline). Read ONLY these files. For each required (table, comparison): set the endpoint
  (match name; RFS→RFI→BCFI fallback + flag), HR as treatment-vs-control (invert + flag if reversed),
  landmark event-free rates (longest; 100−incidence if needed), events/N per arm, medians (usually NA).
  Emit per-field provenance with snippets; `NA` anything unreported; flag every judgment call. Also judge
  O/F (original vs follow-up)."
- **Verifier:** "Independently RE-OPEN and RE-READ every source PDF AND supplement IN FULL, from scratch —
  read all of them again, every page; do NOT rely on the extractor's snippets, a partial read, or prior
  context. Consult all the PDFs again even if it costs more tokens. RE-DERIVE every value. Many HRs/CIs are
  only inside KM-curve or forest-plot IMAGES (and supplementary figures) — render/OCR the figures rather
  than trusting a text dump. Fix HR direction, arm mapping, wrong landmark/denominator, wrong endpoint.
  Fill values it missed (including CIs hidden in figures or supplements). A CI with no point estimate is a
  mis-filed survival-RATE CI — correct it. Keep `NA` only where genuinely unreported after reading
  everything. Return the final reconciled paper object + `disagreements[]` + confidence."

Use `effort: 'high'` for both — these reads are dense (KM curves, forest plots, supplementary tables).

## Adapting rigor
Default = one extractor + one verifier per paper. For a contested/high-stakes paper, add a second
verifier with a different lens (one checks HR/CI + direction, one checks events/N + denominators) and
reconcile by agreement. For a quick single-paper fill, a lone extractor pass is fine if you say so.

## Targeted re-reads
When you add a multi-arm comparison row after the main run, or need one value the first pass missed
(e.g. a forest-plot HR for a second arm), spawn a single focused agent for just that value rather than
re-running everything — give it the file paths, the exact endpoint/comparison, and an anchor to
cross-check (e.g. the sibling comparison's known events/N). Append the result object to
`extraction_results.json`.

## assemble.py config (`_work/assemble_config.json`)
```json
{
  "results": "_work/extraction_results.json",
  "today": "2026-06-20",
  "files": {"OS":"/abs/OS/os_to_extract.xlsx","DFS":"/abs/DFS/pfs_to_extract.xlsx","RFS":"/abs/RFS/rfs_to_extract.xlsx"},
  "study_info": {
    "33451": {"trial_name":"SOFT","nct":"NCT00066690","pmid":"29863451","arms":"3"},
    "12269": {"trial_name":"FATA-GIM3","nct":"NCT00541086","pmid":"29501363","arms":"6"}
  }
}
```
`study_info` keys are paper IDs (strings); `arms` = the trial's TOTAL arm count. `pmid`/`trial_name`/`nct`
here override the agent values (use the most authoritative source). Run:
`python scripts/assemble.py --config _work/assemble_config.json`.

## add_rows.py config (`_work/add_rows_config.json`) — for multi-arm rows missing from the template
```json
{
  "files": {"DFS":"/abs/DFS/pfs_to_extract.xlsx","RFS":"/abs/RFS/rfs_to_extract.xlsx"},
  "new_rows": {
    "DFS": {"12269": ["Exemestane vs. Anastrozole","Letrozole vs. Anastrozole"]},
    "RFS": {"33451": ["Exemestane + ovarian suppression vs Tamoxifen alone"], "63131": ["Exemstane+OFS"]}
  }
}
```
It copies A–F metadata from the study's existing row, inserts the new rows **contiguously** after that
study's last row (grouped, matching the example layout), clears G–Y, and leaves them for assemble to fill
(so add the matching result objects to `extraction_results.json` first, with `comparison` = the new
label). Run: `python scripts/add_rows.py --config _work/add_rows_config.json`, then re-run assemble.
