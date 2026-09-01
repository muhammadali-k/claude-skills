---
name: risk-of-bias
description: >-
  Perform risk-of-bias assessments of clinical-trial and non-randomized-study
  publications using the official Cochrane tools — RoB 2 (randomized trials) and
  ROBINS-I (non-randomised studies of interventions). Reads the publication
  (uploaded PDF/full text or a DOI/PMID), answers every signalling question with a
  supporting quote, then runs a deterministic, rule-based program that transcribes
  the official domain-level algorithm flowcharts and the overall-judgement rules to
  produce per-domain and overall risk-of-bias judgements. Can render robvis-style
  traffic-light and weighted-summary plots on demand. Use whenever someone asks to
  assess risk of bias / study quality / RoB, apply RoB 2 or ROBINS-I, grade trials
  for a systematic review or meta-analysis, or make a traffic-light / robvis plot.
---

# Risk-of-bias assessment (RoB 2 + ROBINS-I)

This skill performs risk-of-bias (RoB) assessments the way a careful reviewer does,
split into three explicit stages so the reasoning is auditable and the aggregation is
reproducible:

1. **Read** the publication and **answer every signalling question** — a judgement task
   done by you (the agent), recording an answer *and a supporting quote with location*
   for each question.
2. **Domain-level rule program** — deterministic Python (`kernel.py`) that transcribes
   the official Cochrane domain algorithm flowcharts and maps the signalling-question
   answers to each domain judgement. No LLM guesswork in this step.
3. **Overall-assessment program** — deterministic Python that aggregates the domain
   judgements into the overall study/result judgement per the official rules.

An optional fourth stage renders **robvis-style traffic-light and weighted-summary
plots**.

The official tool sheets are **bundled** in `assets/` and read locally — the skill never
calls an external service to get the questions or the algorithm.

## Which tool?

| Study design | Tool | Domains | Judgement scale |
|---|---|---|---|
| Randomized controlled trial (parallel-group) | **RoB 2** | D1–D5 | low / some concerns / high |
| Non-randomised study of an intervention (cohort, case-control, quasi-random…) | **ROBINS-I** | D1–D7 | low / moderate / serious / critical / no information |

Pick the tool by the design of the study being assessed. In a review with both, assess
RCTs with RoB 2 and NRSI with ROBINS-I and keep them on separate traffic-light plots.

## Key principle: assess per *result*, not per *study*

Both tools assess the risk of bias in a **specific result (outcome)**, not the study as a
whole. Blinding, missing-data and analysis concerns often differ by outcome (e.g. a
blinded central imaging read vs a patient-reported symptom score in the same trial).
Assess each outcome (or outcome class) you will use in the synthesis. For RoB 2 also fix
the **effect of interest**: `assignment` (intention-to-treat) or `adhering` (per-protocol)
— this selects the D2 variant.

## Calibration — default to the algorithm; downgrade only on strong, domain-specific evidence

Two rules, held together:

1. **Answer each signalling question faithfully from the text and let the crib-sheet
   algorithm (`kernel.py`) decide the domain and overall judgement.** You do **not** need a
   strong reason to record a *low-risk* answer — a clean, unremarkable description is enough
   (this matches the original crib sheet and the completed examples). Do not invent concerns.

2. You **do** need a strong, domain-specific, defensible reason before answering a signalling
   question in the direction that pushes a domain above Low. **Most well-conducted trials are
   low risk of bias.** Do not raise "Some concerns"/"High" out of generic caution: open-label
   design, industry funding, a subgroup/secondary publication, or an abstract-only source are
   **not**, by themselves, reasons to downgrade. Downgrade only when a specific domain
   mechanism is actually present and evidenced.

Domain triggers that DO justify going above Low (RoB 2):
- **D1** — no/opaque randomization or allocation concealment, or baseline imbalances that
  suggest a randomization problem.
- **D2** — substantial non-protocol deviations that affected the outcome, or a non-ITT
  (as-treated/per-protocol) analysis used for the effect of *assignment*. An **open-label
  trial is not itself a D2 concern** for the effect of assignment: with awareness of
  assignment (2.1/2.2 = Yes) but no deviations arising from the trial context (2.3 = No)
  and an appropriate ITT analysis (2.6 = Yes), D2 is **Low**.
- **D3** — meaningful outcome data missing **and** missingness plausibly depends on the true
  outcome. Near-complete follow-up for OS/DFS/RFS ⇒ Low.
- **D4** — the outcome is **subjective and assessed by unblinded assessors** in a way that
  could differ by arm. Objective outcomes — death (OS), and DFS/RFS/PFS by blinded independent
  central review or a documented protocol definition — stay Low even in open-label trials.
  Grade 3+/grade 5 treatment-related AEs are treated as objective here.
- **D5** — the reported result was selected from multiple measurements/analyses, or the
  analysis was not pre-specified. A *pre-specified* subgroup is not a D5 problem.

**Anchor:** well-conducted phase-3 adjuvant/perioperative RCTs reporting OS/DFS/RFS and grade
3+/5 TRAEs are Low risk on every domain (see the completed reviewer examples). Reproduce that
baseline unless a domain trigger above is genuinely met.

## Workflow

### 1. Ingest the publication(s)
- **Uploaded PDF / full text**: read it with `read_file`; for multi-section documents load
  the `pdf-explore` skill. Include supplements/protocols when provided.
- **DOI / PMID**: fetch full text with the `fetch_article_fulltext` tool (open-access via
  PMC/Unpaywall) or the PubMed connector. If only an abstract is retrievable, say so — a
  RoB assessment from an abstract alone is unreliable and many signalling questions will be
  `NI`.

### 2. Scope the assessment
State the study design → tool, the outcome/result(s) to assess, and (RoB 2) the effect of
interest. Get a fillable scaffold:

```python
tmpl = answer_template("rob2", effect="assignment")   # or "adhering"; or answer_template("robins-i")
```

### 3. Answer the signalling questions (the reading step)
For each domain, answer every reached signalling question using the **bundled wording**
(`get_signalling_questions(tool, domain, effect)` or `question_text(...)`). Allowed answers:
`Y`, `PY`, `PN`, `N`, `NI` (no information), `NA` (not applicable). For **each** answer,
record a one-line `rationale` and paste the **verbatim supporting quote with its location**
(section / page / table) into `evidence` — this is what makes the assessment defensible.

```python
ans = {
  "D1": {"answers": {"1.1":"Y","1.2":"Y","1.3":"N"},
         "rationale": "Central IWRS allocation; baseline imbalances compatible with chance.",
         "evidence": "\"...interactive web response system (2:1)...\" — Methods, p.e74."},
  "D2": {"answers": {"2.1":"Y","2.2":"Y","2.3":"N","2.6":"Y"}},   # open-label, ITT
  "D3": {"answers": {"3.1":"N","3.2":"N","3.3":"Y","3.4":"N"}},
  "D4": {"answers": {"4.1":"N","4.2":"N","4.3":"N"}},
  "D5": {"answers": {"5.1":"Y","5.2":"N","5.3":"N"}},
}
```
Only answer the questions that are *reached* on the flowchart path; leave downstream
questions unset (they default to `NA`).

### 4. Compute domain + overall judgements (the rule programs)
```python
res = assess_rob2(ans, effect="assignment", meta={"trial":"SIMPLIFY-2","citation":"...","outcome":"SVR35 wk24"})
# res["domain_judgements"] -> {'D1':'low','D2':'some concerns',...}
# res["overall"]           -> 'some concerns'
```
For ROBINS-I use `assess_robins_i(ans, meta=...)`. Every domain result also carries
`rule_suggested` (the algorithm output) so any override is visible.

### 5. (Optional) verifier pass / overrides
To mirror an assessor + verifier workflow, a second reviewer can override a domain by
supplying `"judgement"` in that domain's dict (e.g. record a ROBINS-I `"critical"`, which is
never auto-assigned). The kernel keeps both `rule_suggested` and the final `judgement` and
sets `overridden=True`. Overriding a RoB 2 domain does **not** silently change the overall —
`rob2_overall` recomputes from the finals; pass `high_if_multiple_some_concerns=True` to
encode the "multiple some-concerns → high" judgement.

### 6. (Optional) traffic-light and summary plots
```python
import pandas as pd
df = results_to_traffic_light_df([res1, res2, ...], tool="rob2")   # or build a DataFrame / CSV
fig = traffic_light_plot(df, tool="rob2", title="RoB 2", save_path="rob2_traffic_light.png")
bar = weighted_bar_plot(df, tool="rob2", save_path="rob2_summary.png")   # weights=<sample sizes> optional
```
`traffic_light_plot` also accepts a list of `assess_*` result dicts directly. Save figures
with `save_artifacts` and embed them for the user.

### 7. Export
Recommended machine-readable outputs (matching a typical review's convention):
`*_traffic_light.csv` (trial, D1…, OVERALL), a per-domain table (trial, domain,
judgement, rule_suggested, rationale, evidence), and a full JSON of the `assess_*` dicts.

## Project mode: filling reviewer templates (e.g. Living Perioperative RCC)

When the deliverable is a pre-built reviewer workbook (`rob_reviewer_1.xlsx` /
`rob_reviewer_2.xlsx`) rather than free-form output, fill it with `template_io.py` and
**never restructure it**. The layout is one worksheet per outcome (`outcome_id`) and one
pre-seeded row per study (`paper_id`); form_data + RoB 2 signalling columns
`d1q1…d5q3` (each followed by a `description` column), per-domain `direction_of_bias` +
`assessor_judgement`, and overall `assessor_judgement` + `overall_description`.

Hard constraints (the host system re-imports these files by their embedded IDs):
- **Do not add or rename worksheets, columns, or header rows, and do not create new studies.**
  A new sheet/column/row has no IDs and will fail re-upload. Write only into existing data
  rows of existing sheets.
- Preserve the data-validation dropdowns (openpyxl load→save preserves them; `template_io`
  relies on this — verify the validation count is unchanged after writing).
- Assess only the outcomes that are **resolved** for a study (per the project's study→outcome
  matrix); leave every other seeded row untouched.
- **Vocabulary must match the dropdowns** — answers `Yes` / `Probably Yes` / `Probably No` /
  `No` / `No Information`, and `NA` for questions the flowchart does not reach; judgements
  `Low risk` / `Some concerns` / `High risk`; direction `Favours experimental` /
  `Favours comparator` / `No direction`.
- **Match the completed examples:** fill the signalling answers, the five per-domain
  `assessor_judgement` cells and the overall `assessor_judgement`; leave every `description`
  cell and `direction_of_bias` blank unless the user asks otherwise.
- RoB 2 answers are **trial-level**: within one trial they apply to all of its resolved
  outcomes (survival + TRAE are objective). Assess each trial once, then replicate across its
  resolved-outcome rows and across the trial's other publications (paper_ids).

**Dual-reviewer + adjudicator** (the standard way to run this): two reviewers assess each
trial **independently** from full text + supplements — one fills `rob_reviewer_1.xlsx`, the
other `rob_reviewer_2.xlsx`; a third **adjudicator** reconciles any per-domain disagreement,
writes the reconciled judgement to both files, and reports the disagreements. Any
intermediate/consensus workbook is a per-run convenience — delete it afterwards if only the
two reviewer files are wanted. **Do not** make sheet/file deletion a skill default.

`template_io.py` API (loaded alongside `kernel.py`):
- `write_study(xlsx_path, paper_id, {sheet_name: assess_rob2_result, …}, comparator=, experimental=, effect='assignment', out_path=None)` — fill one study's resolved-outcome rows in one workbook, in place, preserving everything else. `sheet`→result may instead be a dict `{'result':…, 'comparator':…, 'experimental':…, 'effect':…, 'overall_description':…}` to override per sheet.
- `write_assessment_ws(ws, paper_id, result, …)` — write one result into one open worksheet (`create_row_if_missing=False` by default, so it never fabricates rows).
- `assessment_to_template_values(result, comparator=, experimental=, effect=)` — canonical → template-vocabulary renderer.
- `build_column_map(ws)` — rebuilds the column map from the header block (robust to shifts).
- `read_row(ws, paper_id)` / `list_seeded_studies(xlsx_path, sheet='OS')` — read a filled row back to canonical form / enumerate seeded studies.

## `kernel.py` API

Auto-loaded when this skill loads. Functions:

- `normalize_answer(x)` / `normalize_judgement(x)` — canonicalize answers / judgements.
- `get_signalling_questions(tool, domain=None, effect='assignment')` — bundled question set.
- `answer_template(tool, effect='assignment')` — blank fillable scaffold (step 2).
- `question_text(tool, domain, sq_id, effect='assignment')` — one question's wording.
- `rob2_domain_judgement(domain, answers, effect='assignment')` — one RoB 2 domain (D1–D5).
- `rob2_overall(domain_judgements, high_if_multiple_some_concerns=False)`.
- `robins_i_domain_judgement(domain, answers)` — one ROBINS-I domain (D1–D7); **suggested**.
- `robins_i_overall(domain_judgements)` — worst-domain rule.
- `assess_rob2(answers_by_domain, effect='assignment', high_if_multiple_some_concerns=False, meta=None)`.
- `assess_robins_i(answers_by_domain, meta=None)`.
- `results_to_traffic_light_df(results, tool='rob2')`.
- `traffic_light_plot(data, tool='rob2', ...)` / `weighted_bar_plot(data, tool='rob2', ...)`.
- `load_tool(tool)` — the raw bundled tool definition.

## Bundled assets (`assets/`)
- `rob2_tool.json` — RoB 2 domains, signalling questions, response options, overall rule
  (the operative "sheet" the engine reads; transcribed from the official RoB 2 crib sheet
  for parallel trials).
- `robins_i_tool.json` — ROBINS-I 7 domains, signalling questions, scale, overall rule.
- `robins_i_reference.md` — RoB 2 & ROBINS-I judgement rules, ROBINS-I Table 2, and citations.
- `ROBINS-I_BMJ_2016_fulltext.txt` — official ROBINS-I paper (reference).
- `RoB2_cribsheet_parallel_trial.pdf` — official RoB 2 crib sheet (algorithm source). Shipped
  in the Git repository copy of this skill; in the in-app copy the crib-sheet content is fully
  encoded in `rob2_tool.json` + `kernel.py`.

## Important notes
- **RoB 2 domain judgements are fully algorithmic** (deterministic flowcharts from the crib
  sheet). **ROBINS-I domain judgements are guided, not algorithmic** — `robins_i_domain_judgement`
  returns the tool's recommended mapping as a *suggestion* to confirm or override with expert
  judgement; ROBINS-I `critical` is reserved for the assessor. The ROBINS-I *overall* rule
  (worst-domain) **is** deterministic and fully specified.
- Do not fabricate signalling-question answers. If the text does not support an answer, use
  `NI` and let the algorithm carry the uncertainty into the judgement.
- Keep the effect of interest and the outcome fixed and stated for every RoB 2 result.

## Citations
- RoB 2: Sterne JAC, Savović J, Page MJ, et al. *BMJ* 2019;366:l4898.
- ROBINS-I: Sterne JAC, Hernán MA, Reeves BC, et al. *BMJ* 2016;355:i4919 (tool from riskofbias.info, CC BY-NC).
