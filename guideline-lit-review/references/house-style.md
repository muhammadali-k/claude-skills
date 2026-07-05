# House style — phrasing templates, worked examples, edge cases

This is the source of truth for how the narrative reads. Read it fully before drafting. The three worked examples at the end are real sections; match their voice and structure.

---

## Which table field drives which part of the sentence

For each outcome row in a SoF table:

| Sentence element | Comes from |
|---|---|
| Intervention name | The comparison label / "Risk with intervention" column header context, or the subtitle |
| Comparator name | The comparison label / "Risk with control" context |
| "was / was not associated with a statistically significant improvement" | Whether the **95% CI of the relative effect crosses 1** |
| Outcome abbreviation (OS, DFS, iDFS, DDFS, rPFS, PFS) | The "Outcome" column |
| HR and 95% CI | The "Relative Effect (95% CI)" column — transcribe verbatim into square brackets |
| Certainty of evidence | The "Certainty of Evidence" column |
| Trial name(s); single-trial vs meta-analysis phrasing | The "Trial Used" column (count the names) |

The absolute-risk columns (Risk with control / intervention / Risk Difference) are **not** cited in the narrative. They stay in the table only.

---

## Sentence templates

### Opening summary

Single set of comparisons:
> [N spelled out] randomized trials assessing [intervention class] in patients with [population, mirroring the question stem] were identified by the systematic review.

Stratified comparisons (add a second sentence):
> [N] randomized trials assessing [intervention class] … were identified by the systematic review. Outcomes were assessed in the overall population and by [stratifier, e.g., menopausal status / biomarker status].

Single trial only:
> One randomized trial assessing [intervention] in patients with [population, including any biomarker restriction such as germline BRCA1/2 variants] was identified by the systematic review.

Count **distinct trials** (the union of names across all Trial Used cells), not the number of comparisons or rows.

### Numbered subsection — single outcome, single trial, significant

> X.Y. [Intervention] was associated with a statistically significant improvement in [outcome] compared with [comparator] ([Trial]; [outcome abbr], HR, [point] [95% CI, [low] to [high]]; [certainty] certainty of evidence).

### Numbered subsection — single outcome, single trial, not significant

> X.Y. [Intervention] was not associated with a statistically significant improvement in [outcome] compared with [comparator] ([Trial]; [outcome abbr], HR, [point] [95% CI, [low] to [high]]; [certainty] certainty of evidence).

### Numbered subsection — meta-analysis (2+ trials)

> X.Y. [In the relevant population,] meta-analysis showed that [intervention] was [not] associated with a statistically significant improvement in [outcome] compared with [comparator] ([Trial A, Trial B]; [outcome abbr], HR, [point] [95% CI, [low] to [high]]; [certainty] certainty of evidence).

### Numbered subsection — multiple outcomes in one comparison

Write one sentence per outcome, intervention named once then referred to by name or pronoun:

> X.Y. [In the {subgroup} of the {Trial} trial,] [intervention] was not associated with a statistically significant improvement in invasive disease-free survival compared with placebo ([Trial]; iDFS, HR, … ; [certainty] certainty of evidence). [Intervention] was not associated with a statistically significant improvement in distant disease-free survival compared with placebo ([Trial]; DDFS, HR, … ; [certainty] certainty of evidence). [Intervention] was not associated with a statistically significant improvement in overall survival compared with placebo ([Trial]; OS, HR, … ; [certainty] certainty of evidence).

### Certainty-downgrade closing sentence

When the table has a certainty footnote (e.g., imprecision), close the subsection by explaining the rating in plain words, consistent with the footnote:

> Certainty of evidence was rated as [moderate] for all [N] endpoints due to very serious imprecision, as the wide confidence intervals crossed the null and included the possibility of both clinically meaningful benefit and harm.

Adapt the reason to the footnote actually present (imprecision, inconsistency, indirectness, risk of bias, publication bias). Do not invent a reason the footnote does not state.

---

## Edge cases

- **Mixed significance within one comparison** (e.g., DFS significant, OS not): state each outcome with its own correct verb. Do not let one outcome's direction bleed onto the other.
- **Stratified subgroups of one intervention** (overall / premenopausal / postmenopausal; or BRCA1/2 / non-BRCA HRR): give each its own numbered subsection in natural clinical order (overall first, then subgroups). Note in each whether it is a single-trial or pooled (meta-analysis) estimate based on that row's Trial Used cell — subgroups can differ (CQ19: overall and postmenopausal pooled two trials; premenopausal had only one).
- **Trial name casing/spelling**: match the document. If the SoF table says "Olympia" but the trial is OlympIA, match the table for internal consistency unless the user asks otherwise; you may flag the discrepancy in your summary.
- **A comparison with no significant outcome and low/very-low certainty** sorts to the end.
- **"Physician's choice" / "standard of care" comparators**: use the comparator label as the table states it.
- **Numbers spelled vs numeral**: spell out the trial count at the start of the opening sentence ("Seven randomized trials…", "One randomized trial…"). HRs, CIs, and subsection numbers stay as numerals.

---

## Worked example 1 — CQ7 (multiple comparisons, ordered by significance then certainty)

*Question:* What adjuvant chemotherapy regimens should be recommended for patients with stage I-III hormone receptor-positive, HER2-negative breast cancer?

*Opening:*
> Seven randomized trials assessing adjuvant chemotherapy in patients with stage I-III hormone receptor-positive, HER2-negative breast cancer were identified by the systematic review.

*Subsections (note the ordering: the one significant, high-certainty result leads; then moderate; then low):*
> 7.1. Sequential epirubicin/cyclophosphamide followed by paclitaxel was associated with a statistically significant improvement in OS compared with concurrent epirubicin, cyclophosphamide, and paclitaxel (AGO; OS, HR, 0.72 [95% CI, 0.60 to 0.87]; high certainty of evidence).
>
> 7.2. Dose-dense fluorouracil, epirubicin, and cyclophosphamide (FEC-14) was not associated with a statistically significant improvement in OS compared with standard-interval FEC-21 (MIG-1; OS, HR, 0.89 [95% CI, 0.72 to 1.09]; moderate certainty of evidence).
>
> 7.3. Epirubicin, cyclophosphamide, and docetaxel (EC-T) was not associated with a statistically significant improvement in OS compared with fluorouracil, epirubicin, cyclophosphamide, and docetaxel (FEC-T) (PANTHER; OS, HR, 0.82 [95% CI, 0.65 to 1.04]; moderate certainty of evidence).
>
> 7.4. Standard combination chemotherapy was not associated with a statistically significant improvement in OS compared with capecitabine (CALGB 49907; OS, HR, 0.84 [95% CI, 0.66 to 1.07]; moderate certainty of evidence).
>
> 7.5. Docetaxel and cyclophosphamide (TC) was not associated with a statistically significant difference in OS compared with epirubicin, docetaxel, and cyclophosphamide (E-TC) (DBCG 07-READ; OS, HR, 1.15 [95% CI, 0.83 to 1.59]; low certainty of evidence).
>
> 7.6. Docetaxel and cyclophosphamide (TC) was not associated with a statistically significant difference in OS compared with epirubicin, cyclophosphamide, and docetaxel (EC-T) (PlanB; OS, HR, 0.94 [95% CI, 0.65 to 1.34]; low certainty of evidence).
>
> 7.7. Epirubicin and paclitaxel (EP) was not associated with a statistically significant difference in OS compared with epirubicin, cyclophosphamide, and weekly paclitaxel (EC-wP) (NCT01026116; OS, HR, 0.81 [95% CI, 0.38 to 1.69]; low certainty of evidence).

*Table subtitles* become italic+underline, e.g. *7.1 Epirubicin/Cyclophosphamide followed by Paclitaxel vs. Epirubicin + Cyclophosphamide + Paclitaxel*. Each table carries the footnote: † Calculated using event rate in the control/comparator arm.

---

## Worked example 2 — CQ16 (single trial, biomarker-restricted, multi-outcome, one subsection)

*Question:* What patient and disease factors should be used to select patients with stage I-III HR-positive, HER2-negative breast cancer for whom PARP inhibitors are recommended?

> One randomized trial assessing a poly-ADP ribose polymerase (PARP) inhibitor in patients with stage I-III hormone receptor-positive, HER2-negative breast cancer harboring germline BRCA1/2 pathogenic or likely pathogenic variants was identified by the systematic review.
>
> 16.1. In the hormone receptor-positive, HER2-negative subgroup of the OlympIA trial, one year of adjuvant olaparib following completion of (neo)adjuvant chemotherapy was not associated with a statistically significant improvement in invasive disease-free survival compared with placebo (OlympIA; iDFS, HR, 0.68 [95% CI, 0.40 to 1.13]; moderate certainty of evidence). Olaparib was not associated with a statistically significant improvement in distant disease-free survival compared with placebo (OlympIA; DDFS, HR, 0.69 [95% CI, 0.40 to 1.18]; moderate certainty of evidence). Olaparib was not associated with a statistically significant improvement in overall survival compared with placebo (OlympIA; OS, HR, 0.90 [95% CI, 0.45 to 1.78]; moderate certainty of evidence). Certainty of evidence was rated as moderate for all three endpoints due to very serious imprecision, as the wide confidence intervals crossed the null and included the possibility of both clinically meaningful benefit and harm.

*Subtitle:* *16.1 Olaparib vs Placebo*. Footnote under the table: † Calculated using event rate in the control/comparator arm.

---

## Worked example 3 — CQ19 (one intervention, stratified subgroups, meta-analysis vs single-trial per subgroup)

*Question:* What patient and disease factors should be used to select patients with stage I-III HR-positive, HER2-negative breast cancer for whom bone-modifying agents are recommended?

> Two randomized trials assessing the bone-modifying agent denosumab compared with placebo in patients with stage I-III HR-positive, HER2-negative breast cancer were identified by the systematic review. Outcomes were assessed in the overall population and by menopausal status.
>
> 19.1. In the overall population, meta-analysis showed that adjuvant denosumab was not associated with a statistically significant improvement in disease-free survival compared with placebo (D-CARE, ABCSG-18; DFS, HR, 0.93 [95% CI, 0.74 to 1.17]; moderate certainty of evidence). Certainty of evidence was rated as moderate due to very serious imprecision, as the wide confidence interval crossed the null and included the possibility of both clinically meaningful benefit and harm.
>
> 19.2. In premenopausal patients, denosumab was not associated with a statistically significant improvement in disease-free survival compared with placebo (D-CARE; DFS, HR, 0.97 [95% CI, 0.81 to 1.17]; moderate certainty of evidence). Certainty of evidence was rated as moderate due to very serious imprecision, as the wide confidence interval crossed the null and included the possibility of both clinically meaningful benefit and harm.
>
> 19.3. In postmenopausal patients, meta-analysis showed that adjuvant denosumab was not associated with a statistically significant improvement in disease-free survival compared with placebo (D-CARE, ABCSG-18; DFS, HR, 0.96 [95% CI, 0.70 to 1.30]; moderate certainty of evidence). Certainty of evidence was rated as moderate due to very serious imprecision, as the wide confidence interval crossed the null and included the possibility of both clinically meaningful benefit and harm.

Note how 19.1 and 19.3 say "meta-analysis showed" with two trial names (D-CARE, ABCSG-18) because those rows pool two trials, while 19.2 names only D-CARE because the premenopausal row had a single trial. The subgroups stay in natural order (overall → pre → post), not re-sorted by certainty, because they are strata of one intervention. Each table gets the dagger footnote, and the existing imprecision footnote is preserved.
