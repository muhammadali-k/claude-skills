# Statistical reporting

Khan's quantitative fingerprints. Read before writing any Results or reporting any number. These conventions are recognizable and several are genuine strengths — keep them.

## The inline effect triple

Report effect estimates **inline in prose as a fixed parenthetical triple**: point estimate to two decimals, then `95% CI: lo–hi`, then p (and I² where relevant), then the exhibit pointer.

```
(HR: 0.72; 95% CI: 0.56–0.94; I²: 87%; Supplement Figure S11)
```

The label (**HR / RR / OR / β / B**) precedes the colon. **Keep the delimiter consistent — prefer semicolons** (he sometimes slips to commas by hand; standardize on semicolons).

## The compact `(coefficient; p)` pair — his most recognizable fingerprint

For regression in clinical papers, use the **ultra-compact pair** on first mention with labels — `(B: 0.17; p=0.01)` — then **drop the labels and give bare pairs thereafter** — `depression (10.53; 0.001)`. Example from his work:

> "Young age (β: 0.17; p=0.01), depression (10.53; 0.001), and low hemoglobin (1.24; 0.003) in PV; depression (14.19; <0.001) in ET…"

This bare-pair compression is his single most recognizable quantitative habit — reproduce it in clinical/epi Results.

## Always translate relative → absolute risk

Never report a relative effect without also giving the **absolute risk difference**: *"N fewer/more events per 1000 patients"* **with its own CI** — `116 fewer (172 fewer – 61 fewer)`. This is a signature and a genuine strength; do not omit it. In legends, note how the absolute risk per 1000 was derived.

## Heterogeneity, GRADE, and directions

- **Heterogeneity** as `I²: n%`; where relevant, spell the interpretive bands (0–40% not important; 30–60% moderate; 50–90% substantial; 75–100% considerable).
- **GRADE certainty** in four labeled tiers (**High / Moderate / Low / Very low**), rendered with the GRADE certainty circle glyphs (⊕⊕⊕⊕ high → ⊕⊕⊕⊝ moderate → ⊕⊕⊝⊝ low → ⊕⊝⊝⊝ very low) in Summary-of-Findings tables.
- **Spell out effect direction** for the reader — *"HR < 1 favors dFLOT."* **Bold significant comparisons** in tables with a note — *"bold denotes statistically significant comparisons (95% CI excludes 1)."*

## Counts, central tendency, dispersion

- **Counts** as raw-over-total with a parenthetical percent — `110 (96%)`, `18/19 (95%)`, `approximately 40% (209/523)`. Carry denominators with small-n estimates; flag shifting denominators explicitly when skip logic applies.
- **Central tendency** as `median (range)` or `median (IQR)`; means as `mean X (SD: Y)`.
- **One dispersion notation per manuscript** — he mixes `mean ± SD` and `mean (SD = )` within one paper; pick one and hold it.

## NMA rankings and subgroups

- **NMA rankings** as `rank 1; P-score: 0.99` (or `P-score, 0.99; 1st of 13`); **gloss what a P-score means on first use**.
- **Subgroup interaction** as `p-value of interaction: 0.88`, with the **P<0.1** significance convention for interaction noted.

## Significance threshold and p-values

**State the threshold explicitly as its own clause** — *"A p-value of <0.05 indicated a statistically significant association."* Report p as `<0.001`, `<0.05`, two decimals, or scientific notation for very small values (`p=2×10⁻⁵`).

## ML / AI-model metrics

Report ML metrics as **two-decimal proportions (not percentages)** in the fixed order **accuracy, precision, recall, F1**; report CIs as `point estimate (95% CI, lo–hi)` and drop the label after first use.

## Name the machinery by its eponym

Name statistical methods by their branded eponym, not generically: **DerSimonian–Laird** random-effects, **Mantel–Haenszel**, **Freeman–Tukey** double-arcsine + **Clopper–Pearson**, **Hartung–Knapp** adjustment, **Guyot / WebPlotDigitizer** for IPD reconstruction, **Egger's** test, **Schoenfeld residuals**, **Cox proportional hazards**, frequentist NMA with **`meta` / `netmeta`** (state package version numbers). Reporting these by name is part of his reproducibility signature.
