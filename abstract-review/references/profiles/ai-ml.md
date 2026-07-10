# Profile: AI / ML / generative-AI / LLM papers

Applies to: machine learning methods papers, applied/clinical AI studies, and generative-AI / large-language-model papers and abstracts, whether the venue is an ML conference or a clinical journal.

Follow the shared workflow in `../method.md`; this profile defines what to scrutinize for AI/ML and generative-AI/LLM work specifically.

## What to scrutinize

### Data and split hygiene
- Demand an explicit train/validation/test separation. If a single split is described, ask how hyperparameters were tuned without touching the test set.
- Hunt for data leakage in all its forms: target leakage (features that encode the label), temporal leakage (training on data from after the prediction time), patient- or entity-level leakage (records from the same patient/user split across train and test), and preprocessing leakage (normalization, imputation, or feature selection fit on the full dataset before splitting).
- Check for near-duplicates between training and evaluation data, especially with scraped or pooled datasets.
- For LLMs, ask about benchmark contamination: was the evaluation benchmark plausibly in the pretraining corpus? Comment if the paper claims strong benchmark results on a closed model with no contamination check.

### Evaluation validity
- Match the metric to the task. Flag raw accuracy under class imbalance and ask for F1, AUROC, and especially AUPRC when positives are rare; flag BLEU/ROUGE presented as the sole evidence of generation quality without human evaluation.
- Distinguish in-distribution held-out performance from external or prospective validation; comment when generalization claims rest only on the former.
- Ask for subgroup and fairness breakdowns (site, sex, race/ethnicity, device, language) whenever the model will be applied to people.
- Be alert to benchmark saturation and gaming: a 0.3-point gain on a saturated leaderboard is not a contribution by itself.

### Baselines and ablations
- Baselines must be fair and tuned, not strawmen: same data, same tuning budget, current versions. Comment when the strongest published baseline is missing.
- Require ablations that isolate the claimed contribution; if three things changed at once, the paper has not shown which one mattered.
- Prefer compute- and parameter-matched comparisons; a bigger model beating a smaller one is not evidence for the method.

### Statistical rigor
- Ask for variance across random seeds/runs, confidence intervals on headline metrics, and an appropriate significance or bootstrap test for the key comparison.
- Flag single-run SOTA claims and results reported to three decimals with no uncertainty.

### Reproducibility
- Check availability of code, data, and weights (or a stated reason for withholding), full hyperparameters, compute budget, and random seeds.
- For closed models, the exact model identifier, version, and API access date are mandatory; results from an unversioned API are not reproducible. Comment if absent.

### LLM and generative-AI specifics
- Prompts are part of the method: exact prompts, prompt-selection procedure, and sensitivity analysis; decoding parameters (temperature, top-p, max tokens) must be reported.
- Scrutinize LLM-as-judge evaluation: judge model and version, agreement with human raters, and known biases (position, verbosity, self-preference). Comment if the judged model and the judge share a family.
- Ask how hallucination/faithfulness was measured for generation tasks, not just fluency.
- Human evaluation needs a protocol: number and background of raters, rating instrument, inter-rater agreement (e.g., Cohen's or Fleiss' kappa), and blinding to system identity.
- Look for cost/latency reporting when efficiency is claimed, and for safety, toxicity, and fairness evaluation when deployment is implied.

### Claim calibration
- Downgrade "SOTA", "emergent", "human-level", "understands", and "reasons" unless the evaluation directly supports them; propose calibrated alternatives as tracked edits.
- Confine generalization claims to the tested distribution, task, and language; comment on extrapolation beyond it.

### Clinical and applied AI
- Require a stated intended use and target population, and distinguish retrospective development from prospective validation.
- Ask about deployment and dataset shift (site, scanner, era, case mix) and about the clinician-in-the-loop workflow: who acts on the output, and what happens on error.

## Reporting-standard anchors

- TRIPOD+AI for prediction models; CLAIM for medical imaging AI; MI-CLAIM for clinical ML more broadly.
- CONSORT-AI and SPIRIT-AI for trials of AI interventions; DECIDE-AI for early live clinical evaluation.
- Model Cards and Datasheets for Datasets for model/data documentation.
- NeurIPS/JMLR-style reproducibility checklists for methods papers.
- Anchor comments to the specific checklist item when a required element is missing.

## Edit vs. comment for this profile

- Edit directly (tracked change): overclaiming verbs ("proves", "understands", "human-level"), unhedged SOTA language, metric names misused (e.g., "accuracy" when AUROC is reported), a model version string that is stated elsewhere in the document but missing at a given mention, and routine clarity/grammar fixes.
- Comment (do not silently fix): suspected leakage or contamination, missing splits or baselines, absent uncertainty estimates, unreported prompts/decoding parameters, LLM-judge validity, fairness gaps, and any place where the fix requires new experiments or author knowledge. State the concern, why it matters, and the concrete addition you want.
- Never fabricate a number, a baseline result, or a checklist compliance claim in an edit; if a value is missing, ask for it.

## Verify-before-asserting hot spots

- Re-derive headline metrics from reported confusion-matrix counts or per-class numbers before asserting an inconsistency; check that F1/AUROC values are arithmetically possible given the stated prevalence.
- Confirm the abstract's numbers match the tables and the stated test set (not validation) before flagging a discrepancy.
- Check whether a "no leakage" concern is actually addressed elsewhere in the manuscript (splitting section, appendix) before raising it.
- Before alleging benchmark contamination, check the benchmark release date and the model's training cutoff *as stated in the paper*; if either is absent, comment asking for them rather than asserting contamination.
- Confirm which model version each result belongs to before claiming an unfair comparison; mixed-version tables are common and sometimes deliberate.
- Before asserting a missing standard item (e.g., TRIPOD+AI element), scan the supplement — abstracts and appendices often carry what the main text omits.
