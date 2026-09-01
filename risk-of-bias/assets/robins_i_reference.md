# ROBINS-I & RoB 2 — bundled reference

This skill bundles the official Cochrane risk-of-bias tools. The programmatic rules
in `kernel.py` are transcribed directly from these sources.

## RoB 2 (randomized trials)
- **Source:** the official RoB 2 crib sheet for individually-randomized parallel-group
  trials (`RoB2_cribsheet_parallel_trial.pdf`; signalling questions + domain algorithm
  flowcharts + overall rule). Included in the Git repository copy of this skill; its
  content is transcribed into `rob2_tool.json` and the algorithms in `kernel.py`.
- **Citation:** Sterne JAC, Savović J, Page MJ, et al. RoB 2: a revised tool for assessing
  risk of bias in randomised trials. *BMJ* 2019;366:l4898.
- **Machine-readable:** `rob2_tool.json` (domains, signalling questions, response options,
  overall rule). Domain algorithms are encoded as deterministic functions in `kernel.py`,
  transcribed from the crib-sheet flowcharts.

## ROBINS-I (non-randomized studies of interventions)
- **Citation:** Sterne JAC, Hernán MA, Reeves BC, et al. ROBINS-I: a tool for assessing
  risk of bias in non-randomised studies of interventions. *BMJ* 2016;355:i4919.
  Tool reproduced from riskofbias.info (CC BY-NC; the tool should not be modified for use).
- **Machine-readable:** `robins_i_tool.json` (7 domains, signalling questions, judgement
  scale, overall rule).

### Table 2 — Interpretation of domain-level and overall risk-of-bias judgements (ROBINS-I)

| Judgement | Within each domain | Across domains (overall) |
|---|---|---|
| **Low** | Comparable to a well-performed randomised trial for this domain | Low risk of bias for **all** domains |
| **Moderate** | Sound for a non-randomised study but not comparable to a well-performed RCT | Low or moderate for **all** domains (≥1 moderate; none serious/critical) |
| **Serious** | Some important problems in this domain | Serious in **at least one** domain, but not critical in any |
| **Critical** | Too problematic to provide any useful evidence on the effects of intervention | Critical in **at least one** domain |
| **No information** | No information on which to base a judgement for this domain | No clear indication of serious/critical bias, but a lack of information in ≥1 key domain (a judgement is required) |

Overall aggregation is a "worst-domain" rule with the precedence:
`critical > serious > no information > moderate > low`.

## RoB 2 overall rule
- **Low** — low risk of bias for all domains.
- **Some concerns** — some concerns in ≥1 domain, but not high risk of bias for any domain.
- **High** — high risk of bias in ≥1 domain, OR some concerns for multiple domains in a way
  that substantially lowers confidence in the result (assessor judgement).
