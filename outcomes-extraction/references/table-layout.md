# Outcome table layout

All three outcome tables (OS, DFS, RFS) share an **identical column structure**. Columns A–F are
pre-seeded study metadata; the 19 data fields live in **G–Y**, each tagged in the header with a
`(ID: NNNN)` identifier.

## Map by field ID, NOT column letter
The `*_to_extract.xlsx` and the `*_extraction_examples.xlsx` can order the G–Y fields **differently**
(e.g. the OS example file lists them in reverse vs. the to_extract file). The `(ID: NNNN)` tag — and the
human-readable header label — are the stable identity of each field. Always resolve fields by parsing the
header role (the label text with the `(ID: ...)` stripped), so column-order differences never matter.
`scripts/assemble.py` and `scripts/qc.py` already do this.

## The 19 data fields (role → meaning)

| Header label | Role | Meaning |
|---|---|---|
| Trial Name | `trial_name` | Short trial/acronym (e.g. "SOFT", "BIG 1-98"); `NA` if none |
| NCT | `nct` | Registry ID as printed (NCT…, UMIN…, ISRCTN…); `NA` if none |
| PMID | `pmid` | PubMed ID |
| O/F | `of` | **O**riginal vs **F**ollow-up publication (see conventions.md) |
| (0 selected) | `zero` | A multi-select placeholder — always `0` |
| Arms | `arms` | **Total number of arms in the trial** (same on every row of a study) |
| TE | `te` | Treatment effect = **hazard ratio**, treatment vs control |
| Lower CI | `lower_ci` | 95% CI lower bound |
| Upper CI | `upper_ci` | 95% CI upper bound |
| Treatment | `treatment` | Name of the experimental/treatment arm |
| Control | `control` | Name of the standard/control arm |
| Survival in Treatment | `surv_t` | Event-free rate (%) in treatment arm, at the landmark |
| Survival in Control | `surv_c` | Event-free rate (%) in control arm, at the landmark |
| Et | `et` | Events in treatment arm (deaths for OS; DFS events; recurrences for RFS) |
| Nt | `nt` | N in treatment arm (randomised / ITT) |
| Ec | `ec` | Events in control arm |
| Nc | `nc` | N in control arm |
| Median survival in treatment | `med_t` | Median survival, treatment (usually `NA`) |
| Median survival in control | `med_c` | Median survival, control (usually `NA`) |

## Per-table field IDs (for reference / verification)
The role is the same across tables; only the numeric ID differs. Inspect the actual file to confirm —
these are the IDs observed in the ASCO adjuvant-ET project:

- **OS:** TrialName 3223, NCT 3224, PMID 3225, O/F 3226, (0 selected) 3227, Arms 3228, TE 3230,
  LowerCI 3231, UpperCI 3232, Treatment 3234, Control 3235, SurvT 3236, SurvC 3237, Et 3238, Nt 3239,
  Ec 3240, Nc 3241, MedT 3286, MedC 3287.
- **DFS:** 3243, 3244, 3245, 3246, 3247, 3248, 3250, 3251, 3252, 3254, 3255, 3256, 3257, 3258, 3259,
  3260, 3261, 3449, 3450 (same order).
- **RFS:** 3263, 3264, 3265, 3266, 3267, 3268, 3270, 3271, 3272, 3274, 3275, 3276, 3277, 3278, 3279,
  3280, 3281, 3282, 3283 (same order).

Do not hardcode these — resolve by header role. They're listed only so you can recognize the fields.

## Data types — everything in G–Y is TEXT
In the example files **every G–Y cell is stored as a text string** (PMID `'25318924'`, Et `'71'`,
Arms `'2'`, HR `'0.82'`); only col A (Paper ID) is numeric. This is the convention that makes the upload
robust: because the columns are TEXT, the literal **`NA`** is a valid value everywhere, so any unreported
field is simply `NA`. Write all data values as strings and never leave a data cell blank.

## Identifiers
- **Trial Name / NCT** — read from the paper (NCT often in the abstract/registration line); fall back to
  a project map for consistency with the example file's naming.
- **PMID** — most reliable via the PubMed MCP `convert_article_ids` (DOI→PMID); back-fill from the
  example file or read it off the paper. (idconv misses some DOIs — cross-check.)
- These go in `study_info` in the assemble config (see workflow.md), one entry per paper.
