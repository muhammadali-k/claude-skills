# risk-of-bias

A Claude Science skill for **risk-of-bias assessment** of clinical-trial and
non-randomized-study publications using the official Cochrane tools:

- **RoB 2** (randomized trials) — 5 domains, deterministic domain algorithms transcribed
  from the official crib-sheet flowcharts; overall rule per Cochrane guidance.
- **ROBINS-I** (non-randomized studies of interventions) — 7 domains, guided domain
  judgements, deterministic worst-domain overall rule (BMJ 2016 Table 2).

## Design (three programs + plots)
1. **Reader** (LLM, per `SKILL.md`): answers every signalling question with a supporting quote.
2. **Domain-level rule program** (`kernel.py`): deterministic map answers → domain judgement.
3. **Overall-assessment program** (`kernel.py`): deterministic domain judgements → overall.
4. **robvis-style plots**: `traffic_light_plot()` and `weighted_bar_plot()`.

## Layout
- `SKILL.md` — when-to-use, workflow, answer schema, API reference.
- `kernel.py` — the deterministic engine + plotting (auto-loads into the Claude kernel).
- `assets/` — bundled official tool sheets (RoB 2 crib sheet PDF; machine-readable
  `rob2_tool.json` / `robins_i_tool.json`; ROBINS-I reference + full text).

## Citations
- RoB 2: Sterne JAC, Savović J, Page MJ, et al. *BMJ* 2019;366:l4898.
- ROBINS-I: Sterne JAC, Hernán MA, Reeves BC, et al. *BMJ* 2016;355:i4919 (tool from riskofbias.info, CC BY-NC).
