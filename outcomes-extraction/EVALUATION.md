# Evaluation notes — outcomes-extraction

## Provenance of this skill
Distilled from a complete, user-validated run of the OS/DFS/RFS extraction on the ASCO adjuvant-ET living
review (15 papers; 43 comparison rows across the three tables). Every convention here was confirmed with
the user during that run: HR = treatment-vs-control (invert + flag if reversed); endpoint match with
flagged RFS fallback (RFS→RFI→BCFI→distant); longest-landmark event-free rates (100−incidence if needed);
O/F = original vs follow-up; multi-arm = one row per reported comparison; **Arms = total trial arm count**;
all G–Y cells TEXT so `NA` is always valid.

## Toolchain validation
The bundled scripts were validated by reproducing the approved deliverables: running
`add_rows.py → assemble.py → qc.py` (generalized, config-driven) on clean copies of the original templates
produced output **byte-identical** to the hand-finished, user-approved OS/DFS/RFS files (12 / 14 / 17
rows; 0 empty cells; 0 HR-sanity violations; 144 provenance entries; 210 flags/changes).

## Refinement (iteration 3) — three template families
Extended from the single OS/DFS/RFS layout to three families, after inspecting the actual
Living-Periop-RCC templates with openpyxl:
- **`pwma`** (`pwma_template.xlsx`, A–Y, IDs 3069–3089) — also covers the legacy `*_to_extract.xlsx`.
- **`nma`** (`nma_template.xlsx`, A–X, IDs 21972–21993) — no "(0 selected)"; `Regimen T1/T2`,
  `Measure`, `Survival T1/T2`, `Ec T1/Et T1/Ec T2/Et T2`.
- **`pwma_subgroup`** (`pwma_subgroup_template.xlsx`, A–AA, IDs 9432–9452) — inserts `Subgroup` (F)
  and `Extraction Possible` (G), shifting every data field two letters right.

Two things this iteration is really about:
1. **The Ec/Et divergence.** `Et` is an event COUNT in `pwma` and a PARTICIPANT TOTAL in `nma`. The
   fix is structural, not just documentary: `scripts/families.py` holds the one label→role table and
   uses unambiguous internal names (`events_t`/`n_t`/`events_c`/`n_c`), the result JSON keeps PWMA
   semantics in every family, `assemble.py` relabels for NMA once at write time, and `qc.py` (plus a
   tripwire in the workflow script) flags any row where an event count exceeds its denominator.
2. **The row rule is now conditional on family.** SKILL.md Phase 2 previously said, in bold, "overall
   population only, never a row per subgroup" — correct for the main sheets, and exactly wrong for
   the subgroup template whose purpose is one row per (study × comparison × level). Phase 2 and
   conventions.md now state both rules side by side and say they must never mix.

Toolchain re-validated on copies of the three real templates: family auto-detection (24/25/27 cols),
NMA `T1`/`T2` label disambiguation via the row-2 group banner, scaffolding of family-stamped jobs,
`add_rows.py` inserting a **variable** number of subgroup rows per study (and skipping ones that
already exist), assemble writing PWMA counts into NMA `Ec/Et` correctly, and `qc.py` firing on a
deliberately swapped NMA row. The workflow script's concordance/metric logic was exercised against a
stubbed runtime: subgroup rows key distinctly, and the two-reviewer + senior architecture is unchanged.

## Test cases
`evals/evals.json` has six realistic prompts (5 and 6 cover the NMA Ec/Et semantics and the
variable-length subgroup sheet); the first four are: (1) full three-table pipeline, (2) multi-arm row
verification/repair, (3) a quick single-study fill, (4) scaffolding the per-project job/config setup.
Assertions are objective (HR within CI, Arms = total arm count, RFS substitutions flagged, no fabrication
for outcome-less trials, provenance present, jobs/configs scaffolded with flagged file matches).

## Refinement (iteration 2)
Added `scripts/scaffold.py` — matches source PDFs to studies by author+year and emits `jobs.json` +
`assemble_config.json` + `add_rows_config.json` skeletons (with the needed comparison tuples auto-collected
from the pre-seeded rows), absorbing the error-prone per-project plumbing. Validated on the 15-study ASCO
batch: matched all 15 and flagged the two genuinely ambiguous cases (a filename/publication-year mismatch;
a supplement-only match where the main text is named by submission year). SKILL.md Phase 3 now leads with it.

## Suggested manual checks when running on a new batch
- Spot-check 2–3 HRs against the source PDFs (direction + value).
- **Open one filled NMA row next to its PWMA twin** and confirm the same trial's treatment-arm event
  count and N appear in `Ec T1`/`Et T1` and `Et`/`Nt` respectively — i.e. the counts were relabelled,
  not swapped. `qc.py` only catches a swap when it makes events exceed N; a swap between two similar
  numbers survives the arithmetic check and needs an eye.
- Confirm shared control arms show identical events/N across a trial's comparison rows.
- On the subgroup sheet, read the `Extraction Possible = No` rows: they should be the strata the
  papers genuinely don't report, and they are a result the analyst needs, not a to-do list.
- Read the provenance `Flags_and_Changes` sheet end-to-end — that's where arm flips, endpoint
  substitutions, figure-reads, and descriptive-only HRs surface for human sign-off.
