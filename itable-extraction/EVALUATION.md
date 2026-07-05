# Evaluation — itable-extraction (iteration 1)

Three test cases, each run **with the skill** vs a **baseline** (no skill). Per-assertion pass rate.

| Test case | with-skill | baseline | What the skill changed |
|---|---|---|---|
| **Extract two trials** (ASTRRA + B-42 from PDFs) | **6/6** | 4/6 | Baseline **inverted the ASTRRA arm assignment** (tamoxifen-alone placed as Treatment) and produced **6 numeric + 2 letters-only data-type violations** that would block import. With the skill: both arm mappings correct, file validated clean (0 violations), PMIDs verified against PubMed (caught and corrected a hallucinated one), per-value provenance. |
| **Fix upload validation** (type errors → import-ready) | **5/5** | 4/5 | Baseline over-classified 35 columns as numeric (true count: 10) and blanked `NA` in ~25 text columns; left the PubMed-ID column empty. With the skill: exactly 39 cells changed, 9 real PMIDs resolved, and **~40% faster** (225s vs 380s). |
| **No-example new project** (CSV column list + 3 papers) | **5/5** | 4/5 | Both recognized the no-example case and asked good clarifying questions; only the skill produced **structured per-value provenance** and ran the full validated pipeline. |

## Aggregate

| | with-skill | baseline |
|---|---|---|
| Mean pass rate | **1.00** | 0.76 |
| Mean wall-clock | 343 s | 303 s |
| Mean tokens | 119 k | 91 k |

**Delta: +0.24 pass rate**, +40 s, +28 k tokens.

## Honest caveats
- **Conservative comparison.** The baselines ran *with* the project's auto-memory (which already encodes
  the arm rule and column-type rules); the with-skill runs had that memory moved aside. A cold baseline
  (no skill, no memory) would score lower.
- **Cost/rigor tradeoff.** On the two extraction tasks the skill spends more time/tokens on its full
  parse → match → extract → independent-verify → assemble → validate pipeline and provenance. It buys
  correctness, type-validity, and auditability. On the validation-only task it was *faster* than baseline.
- The "raises clarifying questions" assertion passed in both configurations for the no-example test —
  it does not strongly differentiate the skill.

Model: the session's default model. Runs per configuration: 1.
