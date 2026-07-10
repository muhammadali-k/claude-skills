# Profile: randomized & interventional trials

Applies to: randomized controlled trials (superiority, non-inferiority, cluster, crossover), non-randomized interventional studies, and single-arm or early-phase (phase 1/2) trials, whether abstract or full manuscript.

Follow the shared workflow in `../method.md`; this profile defines what to scrutinize and how to phrase edits and comments for interventional trials.

## What to scrutinize

### Internal validity
- Randomization: is the method stated (computer-generated, permuted blocks, stratification factors)? "Randomized" with no method is a comment-worthy gap in a manuscript; acceptable in an abstract only if the ratio and stratification are given.
- Allocation concealment: distinct from randomization and from blinding. Flag if the text conflates them or omits concealment in an open-label trial where it still matters.
- Blinding: who was blinded (participants, clinicians, outcome assessors, statisticians)? "Double-blind" without specifying which parties is imprecise; suggest naming them. For open-label trials, ask whether outcome assessment was blinded, especially for subjective endpoints (response, PROs).
- Analysis population: ITT vs modified ITT vs per-protocol. The primary analysis of a superiority trial should be ITT; per-protocol as primary needs justification. For non-inferiority, both ITT and per-protocol should be concordant; flag if only one is reported.
- Attrition and flow: check that randomized, treated, discontinued, and analyzed numbers reconcile (CONSORT flow). Differential dropout between arms >10 percentage points warrants a comment on attrition bias.
- Pre-specification: were the primary endpoint, analysis, and any interim looks pre-specified in the protocol/SAP? Flag endpoint switching, post hoc analysis populations, or unregistered outcomes presented as primary.

### Endpoints and multiplicity
- Identify the primary endpoint(s) explicitly. If co-primary, both must be met unless the SAP says otherwise; a missed co-primary removes alpha protection from everything downstream.
- Alpha allocation: with hierarchical (gated) testing, a failed test breaks the chain — any "significant" endpoint below the break is nominal only. Flag secondary endpoints described as "significant" when they were not alpha-protected; suggest "nominally significant" or descriptive language.
- Surrogate vs clinical endpoints: pCR, ORR, PFS, and biomarker endpoints are surrogates; comment when conclusions extrapolate from a surrogate to survival or benefit without qualification.
- Check that the endpoint definition matches the registry entry (measure, timepoint, analysis population).

### Effect estimates and claims
- Every comparative claim needs an effect estimate with 95% CI: HR for time-to-event, RR/OR for binary, MD/SMD for continuous. Edit in the CI if it is in the source tables but missing from the text; comment if it is nowhere.
- Non-inferiority vs superiority: the framing must match the design. For non-inferiority, the margin must be stated and the CI compared against it; "as effective as" from a failed superiority trial is a rewrite-level error.
- Absolute vs relative effects: a large relative effect on a rare outcome should be accompanied by absolute rates or an absolute difference; suggest adding them.
- Subgroups and interactions: subgroup findings are exploratory unless pre-specified with multiplicity control and a significant interaction test. Flag confirmatory language ("benefit in patients with X"), claims based on within-subgroup p-values, or subgroup counts that invite chance findings.

### Time-to-event maturity
- Check event counts against sample size: OS or PFS with few events (immature data) cannot support definitive claims. Flag HRs reported at low information fractions and soften to "preliminary" or "early".
- "Median not reached" is a maturity signal, not an efficacy claim; edit text that treats it as one.
- Median follow-up should be stated; comment if absent or clearly short relative to the natural history of the disease.
- Informative censoring: heavy censoring for toxicity, crossover, or withdrawal can bias PFS/OS; comment when censoring patterns are asymmetric between arms or unaddressed.

### Single-arm and early-phase caveats
- No control arm means no comparative claim: ORR, DCR, or pCR in a single-arm study is descriptive. Rewrite "improved response" or "superior to historical controls" unless a formal historical comparison with a pre-specified benchmark is described.
- Dose-finding: check that DLT definitions, the DLT window, escalation design (3+3, BOIN, mTPI), and the basis for the RP2D are stated.
- Small N: demand exact denominators and CIs around response rates; a 40% ORR in n=10 is 4 patients — comment when precision is overstated. Watch for evaluable-patient denominators that quietly exclude enrolled patients.
- Efficacy-adjacent conclusions from phase 1 ("promising activity") should be labeled preliminary; edit accordingly.

### Safety
- Adverse events should be graded per CTCAE (version stated), with denominators (safety population, not ITT) explicit.
- Unequal exposure between arms distorts crude AE rates; ask for exposure-adjusted rates when treatment durations differ materially.
- Distinguish all-cause AEs from treatment-related AEs; flag text that reports only one or blurs attribution.
- Check discontinuation-for-toxicity, dose-reduction, and dose-interruption rates, and grade >=3 and serious AE rates; comment if a "well tolerated" claim lacks these numbers. Deaths on study need cause and attribution.

### Reporting and registration
- Trial registration number (NCT, EudraCT, ISRCTN) should appear; comment if missing.
- Manuscripts should follow CONSORT 2025 with a flow diagram; abstracts should follow CONSORT for Abstracts (design, participants, randomization, blinding, numbers analyzed, primary outcome result with effect size and precision, harms, registration, funding).
- Funding source and sponsor role in design, analysis, and writing should be disclosed; comment if absent from a manuscript.

## Reporting-standard anchors

- CONSORT 2025 for parallel-group RCT manuscripts; CONSORT for Abstracts for conference abstracts and journal abstracts.
- CONSORT extensions where applicable: non-inferiority/equivalence, cluster, crossover, pilot/feasibility, harms.
- SPIRIT 2025 for protocol content when the manuscript references or includes the protocol.
- CTCAE (current version) for adverse event grading and terminology.
- ICH E9 and the E9(R1) estimands addendum for analysis populations, intercurrent events, and sensitivity analyses.

## Edit vs. comment for this profile

- Edit directly (tracked change): adding CIs or denominators present elsewhere in the document; softening immature or unprotected findings ("significant" -> "nominally significant", "improved" -> "was associated with" for non-alpha-protected endpoints); fixing superiority/non-inferiority phrasing; converting comparative language in single-arm studies to descriptive language; tightening "double-blind" to name blinded parties when stated elsewhere.
- Comment (do not edit): missing randomization method, allocation concealment, registration, funding role, CTCAE version, median follow-up, or SAP pre-specification — you cannot invent these; ask the authors. Also comment for suspected endpoint switching, discordant registry entries, asymmetric censoring, and any subgroup claim that needs the interaction test.
- When a conclusion overreaches (e.g., survival claim from a surrogate, definitive claim from immature OS), pair a softening edit with a comment explaining the multiplicity or maturity reason, so the authors see why.

## Verify-before-asserting hot spots

- Alpha protection: before flagging or endorsing a "significant" secondary endpoint, trace the testing hierarchy in the methods/SAP; do not assume protection or its absence.
- Non-inferiority margin: read the actual margin and CI bounds before commenting that non-inferiority was or was not shown.
- Numbers reconciliation: recompute that arm Ns, events, responders, and percentages are internally consistent (numerator/denominator/percent) before asserting a discrepancy.
- Registry check: only claim endpoint switching if you have compared the stated primary endpoint against the registration or protocol text available in the document; otherwise phrase as a question.
- Event maturity: count reported events against planned events or information fraction if given; do not call data "immature" on sample size alone.
- ITT vs per-protocol: confirm which population each headline number comes from before flagging a mismatch; tables and text often differ.
