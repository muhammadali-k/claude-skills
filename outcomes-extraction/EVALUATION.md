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

## Test cases
`evals/evals.json` has four realistic prompts: (1) full three-table pipeline, (2) multi-arm row
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
- Confirm shared control arms show identical events/N across a trial's comparison rows.
- Read the provenance `Flags_and_Changes` sheet end-to-end — that's where arm flips, endpoint
  substitutions, figure-reads, and descriptive-only HRs surface for human sign-off.
