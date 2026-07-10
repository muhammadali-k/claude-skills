# Profile: observational studies (cohort, case-control, cross-sectional)

Applies to: prospective and retrospective cohorts, case-control studies, cross-sectional analyses, and database/registry/real-world-evidence studies (claims, EHR, cancer registries, pharmacoepidemiology). This profile owns registry/RWE *comparative* analyses; `other-clinical.md` points here for them.

Follow the shared workflow in `../method.md`; this profile defines what to scrutinize when the study is observational and how to weight edits versus comments.

## What to scrutinize

### Confounding and adjustment strategy
- Distinguish measured confounding (addressable by adjustment) from unmeasured/residual confounding (addressable only by design, sensitivity analysis, or humility in the conclusions). If the abstract claims a treatment effect from registry data with no acknowledgment of residual confounding, comment.
- Check the adjustment method: multivariable regression, propensity score matching, weighting (IPTW), or stratification. For propensity methods, look for covariate balance reporting (standardized mean differences) and what happens to unmatched patients.
- Ask how covariates were chosen. A DAG-justified or prespecified set is stronger than "all variables with p < 0.10 on univariable analysis" (a red flag; comment on it). Watch for adjustment sets that include mediators (biases the total effect toward the null) or colliders (induces spurious association) -- adjusting for a post-exposure variable is the classic error.
- Positivity: were there exposure groups or strata where one treatment was essentially never given? Extreme weights or thin cells suggest the comparison is not answerable in that population.

### Bias catalog -- name the specific bias
- Selection bias: who entered the cohort or the case-control sampling frame, and does entry depend on both exposure and outcome? Prevalent-user cohorts and survivor cohorts are common offenders.
- Immortal-time bias: the classic pharmacoepidemiology trap. If exposure is defined by something that happens after time zero (e.g., "received drug within 6 months"), the exposed group has guaranteed survival time. Check that person-time before exposure is not credited to the exposed group.
- Lead-time and length bias in any screening or early-detection comparison; survival measured from diagnosis will flatter the screened group.
- Detection/surveillance bias: does the exposed group get more imaging, labs, or visits, mechanically inflating outcome ascertainment?
- Information bias and misclassification: is it differential (biases in either direction) or non-differential (usually toward the null, but not guaranteed for polytomous exposures)? For claims data, ask whether codes were validated.
- Recall bias in case-control designs with self-reported exposure; reverse causation whenever the exposure could be a consequence of preclinical disease (confounding by indication is its cousin -- sicker patients get treated differently).
- Loss to follow-up: how much, whether differential by exposure, and how it was handled.

### Design and exposure definition
- Prefer new-user, active-comparator designs over prevalent-user or non-user comparisons; if the study compares users to non-users, comment on confounding by indication and healthy-user bias.
- Look for target-trial emulation framing: is there a well-defined time zero at which eligibility, exposure assignment, and follow-up all start? Misaligned time zero is where immortal time and selection bias enter.
- Check exposure and outcome ascertainment validity: lookback windows, exposure lag/latency, induction periods, and whether outcome definitions were validated in the data source.
- Competing risks: for non-fatal outcomes in populations with substantial mortality, ask whether death was treated as a competing event (Fine-Gray or cause-specific hazards) or improperly censored.

### Causal language discipline
- This is the highest-yield check. Associational data must not carry causal verbs: "caused", "reduced", "prevented", "improved survival", "led to". Edit to "was associated with" and preserve the direction and magnitude.
- Titles and conclusions are the worst offenders; a hedged methods section does not license a causal conclusion. Flag "effect of X on Y" framing for observational exposure contrasts.
- Strength of association, consistency, and dose-response support causal inference but do not establish it; if the authors invoke them as proof, comment.

### Effect estimates
- Confirm the measure matches the design: OR for case-control (and check the rare-disease assumption if it is interpreted as RR), HR for time-to-event cohorts, PR/OR for cross-sectional. ORs from common outcomes overstate RRs -- flag when interpreted interchangeably.
- Both crude and adjusted estimates should be reported or at least the adjusted one with the covariate list; large crude-to-adjusted shifts signal strong confounding and deserve a comment.
- Every estimate needs a 95% CI; interpret the interval, not just the point estimate or the p-value.
- Ask whether the estimate answers the causal question posed: an association among survivors at 5 years does not answer "does starting drug X reduce mortality?"
- For strong claims, look for sensitivity to unmeasured confounding -- an E-value, negative-control outcome, or quantitative bias analysis. If a modest HR (e.g., 0.85) anchors a strong conclusion, note that a weak unmeasured confounder could explain it.

### Missing data and generalizability
- How was missingness handled: complete-case (assumes MCAR; check how many were dropped), multiple imputation (check what was in the imputation model), or missing-indicator (generally biased)? Silent complete-case analysis with >10-15% exclusion deserves a comment.
- Source population and applicability: single-center, one insurer, one country, or one era limits generalizability; conclusions should not extrapolate beyond the sampled population.
- For registry/claims studies, ask what the database cannot see (over-the-counter drugs, labs, performance status, out-of-network care) and whether that blind spot is a plausible confounder.

## Reporting-standard anchors

- STROBE for cohort, case-control, and cross-sectional studies; STROBE for Abstracts for conference abstracts (design in title, eligibility, exposure/outcome definitions, adjusted estimates with CIs, key limitation).
- RECORD (and RECORD-PE for pharmacoepidemiology) for routinely collected health data (code lists, validation, data linkage, cleaning); STaRT-RWE for structured real-world-evidence study parameters.
- STROBE-MR if the study is a Mendelian randomization analysis (instrument validity, pleiotropy checks).
- E-value and quantitative bias analysis conventions for sensitivity to unmeasured confounding.
- Target-trial emulation framework (Hernan/Robins) as the benchmark for time-zero alignment and eligibility in database studies.

## Edit vs. comment for this profile

- Edit directly (tracked change): causal verbs on associational findings ("reduced" -> "was associated with lower"), OR described as "risk" for a common outcome, missing "adjusted" qualifier before an adjusted estimate, design mislabeled in the title, grammar and abbreviation fixes.
- Comment (do not silently rewrite): suspected immortal-time bias or time-zero misalignment, questionable adjustment sets (possible mediator/collider), absent confounders you would expect, competing-risks handling, missing-data method, requests for E-value or sensitivity analyses, generalizability limits. These need the authors' knowledge of the data; pose them as questions with the specific bias named.
- When a conclusion overreaches, pair a tracked edit of the sentence with a comment explaining why the softer claim is the defensible one.

## Verify-before-asserting hot spots

- Before flagging immortal-time bias, re-read the exposure definition and follow-up start; confirm exposure classification actually precedes or spans time zero incorrectly.
- Before calling an estimate "unadjusted", check the table footnotes and methods for the covariate list -- abstracts often omit "adjusted" while the model is adjusted.
- Check that the OR/HR direction matches the prose (protective vs harmful) and that the CI printed actually excludes or includes 1 as the text claims.
- Confirm the design label: a "prospective cohort" assembled from retrospective chart review is retrospective; a case-control study reporting "incidence" is misreporting.
- Verify counts: cases plus controls, cohort N versus analyzed N after exclusions, and person-time consistency with reported rates before asserting a discrepancy.
- Do not assert that a specific confounder was unmeasured until you have checked the covariate list, supplements, and data-source description.
