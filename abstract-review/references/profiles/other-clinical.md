# Profile: other clinical designs (diagnostic, prediction, case reports, health economics)

Applies to: diagnostic test accuracy studies, prognostic and clinical prediction models, case reports and case series, and health-economic evaluations. (Real-world evidence / registry *comparative* analyses are an observational design — use `observational.md`.)

Follow the shared workflow in `../method.md`; this profile defines what to scrutinize for four other clinical design families. Identify which one the abstract or manuscript belongs to first, then apply the matching subsection. If the paper mixes designs (e.g., a prediction model validated in a registry cohort), apply every subsection that fits and read `observational.md` too.

## What to scrutinize

### Diagnostic accuracy studies

- Demand the full accuracy panel: sensitivity, specificity, PPV, NPV, likelihood ratios, and AUC where a threshold-free summary is claimed. Flag any abstract reporting sensitivity alone or AUC alone as incomplete.
- Check the reference standard: is it a true gold standard, applied to all participants, and independent of the index test? Partial verification (only index-positive patients get the reference test) and incorporation bias (index test forms part of the reference standard) both inflate accuracy — comment when the workflow is unclear.
- Scrutinize the spectrum: case-control designs comparing severe cases against healthy controls overstate accuracy (spectrum bias). Prefer consecutive or random sampling from the intended-use population.
- PPV and NPV are prevalence-dependent. If the study prevalence differs from the target setting, comment that predictive values do not transport; sensitivity/specificity or LRs should carry the claim.
- Verify blinding: index-test readers blinded to reference results and vice versa. Absence is a QUADAS-2 bias signal — name it.
- Check that indeterminate/uninterpretable results and their handling (excluded vs counted) are reported; exclusion inflates accuracy.

### Prognostic and clinical prediction models

*(Regression / statistical models are covered here; for machine-learning or deep-learning models also apply `ai-ml.md`.)*

- Discrimination is not enough. A C-statistic without calibration (calibration slope, intercept, or plot) is half a validation — comment whenever calibration is missing from a performance claim.
- Interrogate overfitting: how many candidate predictors against how many events (events-per-variable)? Fewer than ~10 events per candidate predictor without penalization (LASSO, ridge) warrants a comment on optimism.
- Distinguish internal validation (bootstrap, cross-validation — corrects optimism in the same data) from external validation (new patients, new setting). A model described as "validated" on a random split of the same dataset is internally validated at best; edit the wording.
- Check handling of missing predictor data: complete-case analysis biases and shrinks the sample; multiple imputation should be described. Also ask whether predictors are available at the moment of intended use.
- If a risk threshold or clinical-utility claim is made, look for decision-curve or net-benefit analysis before letting "clinically useful" stand.

### Case reports and case series

- These are descriptive. Edit or comment on any incidence, prevalence, efficacy, or comparative-effectiveness language — a series without a denominator supports none of it.
- For adverse-event attributions, look for a structured causality assessment (Naranjo scale or WHO-UMC criteria). "Likely caused by" without one is an assertion, not an assessment — comment.
- Check for dechallenge/rechallenge information, temporal plausibility, and alternative explanations when a drug-event link is claimed.
- Flag generalizability overreach: "this suggests patients with X should receive Y" from n=3 needs softening to hypothesis-generating language.
- Verify that patient consent for publication is stated (or IRB waiver); its absence is a mandatory comment for identifiable cases.

### Health-economic evaluations

- Pin down the analytic perspective (healthcare payer, societal, hospital) and check that included costs match it — a "societal perspective" that omits productivity losses is mislabeled.
- Check the time horizon against the disease course: lifetime horizons for chronic disease, and comment if a short horizon truncates costs or QALYs asymmetrically between arms.
- Identify the model type (decision tree, Markov cohort, discrete-event simulation, partitioned survival) and whether it fits the disease structure; Markov models need stated cycle length and half-cycle correction.
- Scrutinize the ICER: is it compared against a stated willingness-to-pay threshold, and is dominance/extended dominance handled correctly? "Cost-effective" without a threshold is unanchored — comment.
- Verify discounting of both costs and effects (typically 3-3.5 percent annually) and that the rate is stated.
- Require both deterministic (one-way, tornado) and probabilistic sensitivity analysis (cost-effectiveness acceptability curve). A base-case ICER alone is fragile.
- Funding source and sponsor role are load-bearing here; industry-funded evaluations without an independence statement warrant a comment.

## Reporting-standard anchors

- Diagnostic accuracy: STARD 2015 for reporting; QUADAS-2 domains (patient selection, index test, reference standard, flow and timing) for bias language.
- Prediction models: TRIPOD (or TRIPOD+AI for machine-learning models) — anchor comments to its items on validation type, performance measures, and missing data. (Registry/RWE reporting standards live in `observational.md`.)
- Case reports: CARE checklist, including the consent item.
- Health economics: CHEERS 2022 — perspective, horizon, discounting, and sensitivity-analysis items map directly to the scrutiny points above.

## Edit vs. comment for this profile

- Edit directly (tracked change): causal verbs unsupported by design ("reduces" to "was associated with"), "validated" to "internally validated" when only same-data validation exists, "diagnostic accuracy" claims restated with the correct metric names, "cost-effective" softened when no threshold is given, and efficacy language stripped from case series.
- Comment (do not silently rewrite): missing calibration or sensitivity/specificity companions, suspected verification or spectrum bias, absent causality assessment, unstated perspective or discount rate, missing consent statement, and any place where the fix requires data the authors have and you do not.
- When a claim could be correct but the supporting number is absent, comment with the specific missing item ("add the calibration slope", "state the WTP threshold") rather than a general request for "more detail".

## Verify-before-asserting hot spots

- Recompute PPV/NPV from the reported sensitivity, specificity, and prevalence before asserting an inconsistency; small rounding differences are not findings.
- Check whether an "external validation" cohort truly differs in place or time from the derivation cohort before flagging it as internal — read the cohort description, not just the label.
- Verify the ICER arithmetic (incremental cost divided by incremental effect) against the reported arm-level values before calling it wrong.
- Do not assert a QUADAS-2 or TRIPOD violation from silence alone in an abstract; word-limited abstracts omit detail — phrase these as requests to confirm, and reserve firm bias assertions for the full manuscript.
