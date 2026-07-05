# Evaluation — study-question-tagging

Validated with the skill-creator eval harness against a real fixture: the ASCO stage I–III HR+/HER2−
adjuvant endocrine therapy project (panel manuscript with 6 adjuvant-ET clinical questions + 15 included
RCTs + their reference PDFs). Two test cases, each run **with the skill** and as a **no-skill baseline**;
graded against the validated ground-truth assignment matrix.

## Test cases
1. **full-tagging-6-questions** (end-to-end) — extract the adjuvant-ET questions from the manuscript, tag
   the 15 studies, emit one Excel per question. Assertions: ~6 files; premenopausal-treatment, postmenopausal-
   treatment, and duration ID-sets exact; population gatekeeper respected; source columns preserved; the
   timing question empty.
2. **classify-premeno-vs-duration** (focused) — which studies answer the premenopausal-treatment question
   vs the duration question (a discriminating case, no manuscript scaffold). Assertions: both lists exact;
   the OFS-duration trial tagged to duration only; gatekeeper respected.

## Result (final, iteration 3)

| Test | With skill | Baseline (no skill) |
|------|:---:|:---:|
| full-tagging-6-questions | 7/7 | 7/7 |
| classify-premeno-vs-duration | **4/4** | 2/4 |
| **Mean pass rate** | **1.00** | **0.75** (Δ +0.25) |

- **Eval 1 ties at 7/7** because this manuscript embeds per-question GRADE comparison tables that name the
  trials, so a strong baseline can follow them. The skill's added value there is consistency, the
  deterministic formatting-preserving file build, and the study↔PDF matcher — not accuracy on this fixture.
  It would separate more on a guideline that does **not** pre-name trials per question.
- **Eval 2 is where the skill wins (4/4 vs 2/4):** without the manuscript's tables, the baseline mis-tags a
  duration trial (ovarian-suppression 2y vs 3+y) into the premenopausal-**treatment** list. The skill's
  "tag by the randomized contrast, not the population" rule routes it to duration only.

## Iteration history (what the harness caught)
- **iter 1:** both configs 2/4 on eval 2 — both mis-tagged the OFS-duration trial as a treatment-choice study.
- **iter 2:** first fix ("tag by what's randomized") fixed eval 2 but **overcorrected** — it stripped the
  extended-AI trials out of the postmenopausal-treatment question (eval 1 → 5/7).
- **iter 3:** refined the rule to distinguish *extend/continue/intensify therapy* (a treatment strategy →
  multi-assign to treatment **and** duration) from a *within-regimen component-length tweak* (duration only),
  and to defer to the guideline's own per-question evidence comparisons. Result: eval 1 7/7 **and** eval 2 4/4.

Harness, fixtures, and per-run grading live in the `study-question-tagging-workspace/` sibling directory
(not committed: the fixture PDFs are large and licensed).
