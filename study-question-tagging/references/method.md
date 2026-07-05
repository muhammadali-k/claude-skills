# The tagging method: deciding which studies answer which question

This is the judgment layer of the skill. Mechanics (parsing the doc, building the files) are easy; the
hard part is deciding, defensibly, whether a given trial *answers* a given clinical question. The aim is
to reproduce what a careful guideline methodologist would do: include a study under a question only when
it provides **direct evidence bearing on the decision that question asks**, and to be transparent about
the close calls.

## 1. Read each question as a decision, and derive its inclusion criteria

A clinical question is a decision in disguise. Before looking at any study, restate each question as the
specific contrast it is trying to resolve, and write down the criteria a study must meet to inform it.
Most guideline questions decompose into some of:

- **Population** — who the decision is about (e.g. premenopausal vs postmenopausal; node-positive; a
  biomarker-defined subgroup). This is frequently the single most decisive filter.
- **Intervention / comparison** — what is being chosen between (drug A vs B, treat vs not, longer vs
  shorter, concurrent vs sequential, an adherence intervention vs usual care).
- **The decision type** — questions usually fall into recognizable shapes: *who to select/treat*,
  *which treatment*, *how long (duration)*, *when (timing/sequencing)*, *how to support tolerability/
  adherence*. Two questions can share a population but ask different decisions (e.g. "which treatment"
  vs "how long") — a study can answer one, the other, or both.

A study answers the question only if its randomized contrast maps onto that decision **in that
population**. Write the criteria down (even informally) so every study is judged against the same bar.

**Tag by what the trial randomizes, not by the population it enrolled** — reading "what it randomizes"
against the question's decision, not mechanically. Being in the right population is necessary but not
sufficient; the *contrast* has to be one the question is actually asking about. Three patterns recur:

- **Different agents/regimens → a "which treatment" answer.** A trial that randomizes between different
  treatments (drug A vs B, add-a-drug vs not, agent X vs Y, sequence vs monotherapy) answers the
  treatment-choice question for its population.
- **Extending / continuing / intensifying therapy is itself a treatment choice.** A trial that randomizes
  whether to *extend, continue, or intensify* treatment (more years of an agent, adding a second agent,
  escalating the regimen) answers BOTH the duration question AND the "which treatment" question for that
  population — extended/intensified therapy is one of the strategies the treatment recommendation weighs.
  **Multi-assign it to both.** (E.g., "5 vs 10 years of an aromatase inhibitor," or "extend the AI vs stop
  at 5 years," belongs under the postmenopausal-treatment question *and* the duration question.)
- **Varying the length of one component inside an otherwise-fixed regimen is not a new treatment.** If
  every arm delivers the same regimen and only the duration (or schedule/timing) of one component differs,
  and the treatment question is about choosing between *different regimens or agents*, the trial answers
  the *duration* (or *timing*) question only — not "which treatment," even though the population fits.
  (E.g., a premenopausal trial randomizing 2 vs 3+ years of ovarian suppression on a fixed
  ovarian-suppression-plus-tamoxifen backbone answers "how long," not "which premenopausal regimen.")

The line between the last two is whether the contrast is a strategy the treatment recommendation actually
weighs. When the guideline states its evidence comparisons per question — in the recommendation text or in
GRADE / summary-of-findings tables that name trials under each comparison — use those as the authority for
which contrasts answer which question (the comparisons are reliable even when you've restricted the
*included set* to a newer subset of trials). Fall back to the reasoning above when the guideline is silent.

## 2. The direct-evidence standard

Include a study under a question when it contributes a **randomized comparison that bears directly on
the question's decision**. Be conservative:

- A trial that *reports* an outcome is not the same as a trial that *answers* the question. Nearly every
  endocrine-therapy trial reports adverse events, but that does not make every trial an answer to "how
  should we monitor adverse effects and improve adherence." Ask: *is this contrast designed to resolve
  this decision, or is the relevant data just incidental reporting?* When the user's project treats a
  whole class as in-scope (e.g. "any trial surfacing a duration-dependent toxicity tradeoff counts for
  the adherence question"), follow that — but make the rule explicit and apply it to every study, not
  just some. Consistency is what makes the set defensible.
- Indirect or background evidence (a study cited only to motivate a recommendation, or a different
  population) does not earn an assignment.
- If the only signal is a global p-value or a descriptive, non-randomized comparison, treat it as a flag,
  not a clean assignment.

## 3. A study can answer more than one question (multi-assignment)

Assignment is many-to-many. A postmenopausal extended-aromatase-inhibitor trial, for example, can answer
both "which treatment for postmenopausal women" (extended therapy is a treatment strategy) and "how long
should treatment last" (it randomizes duration). List the study under **every** question it directly
answers. The reverse constraint is the important one: never attach a study to a question it does not
actually inform.

## 4. Gatekeepers: criteria that hard-exclude

Some criteria are absolute for a given question and should short-circuit the decision. Population is the
classic one: a question scoped to premenopausal women cannot be answered by a postmenopausal-only trial,
regardless of how relevant the intervention is, and vice versa. Identify each question's gatekeeper(s)
up front (population, line of therapy, biomarker status, setting) and apply them first — they resolve a
large share of studies immediately and prevent the most common mis-assignments.

## 5. Abstracts first, full text for the ambiguous

The included-studies sheet almost always carries each study's abstract, and abstracts usually state the
population, the design, and the headline comparison — enough to tag most studies confidently. Reserve
full-text + supplement reading for studies whose question-fit is genuinely unclear from the abstract:

- borderline or mixed population (is this trial pre- or postmenopausal? what fraction?),
- which arm/comparison actually carries the reported effect,
- treatment-choice vs duration overlap (does it vary the agent, the schedule, or the length?),
- relevance to a tolerability/adherence question,
- a multi-arm trial where the relevant contrast isn't obvious.

This keeps the work tractable and focuses careful reading where it changes the answer. Match each study
to its publication files first (see `workflow.md`) so the full text is one Read away when needed.

## 6. When to ask vs when to proceed

Default to **proceeding**: if a study's fit is clear under the criteria, assign it and move on — do not
interrupt the user for confirmations they don't need. **Ask** only when a decision is genuinely the
user's to make and would change the output:

- a study sits right on the boundary of two questions and the criteria don't cleanly resolve it;
- a question's scope itself is ambiguous (which sections/questions are even in scope for this run);
- a study has no matching publication file, or matches several;
- a near-miss inclusion/exclusion that reasonable reviewers would split on (e.g. the one trial that
  could populate an otherwise-empty question).

Batch these into a short, specific list with your recommendation for each, rather than a stream of
one-off questions. Collect the genuine judgment calls during adjudication and raise them together.

## 7. Empty questions are a valid, important result

Some questions will have **no** answering study in the included set — typically the "which patients to
select" and "timing of initiation" style questions, which guidelines often base on expert consensus or
on study types outside the trial set. Do not manufacture a fit to avoid an empty file. Produce the
header-only file and say plainly that no included study answers it. If a study *could* arguably populate
such a question (e.g. the only trial comparing treatment vs no treatment, which bears on selection),
surface it as a judgment call (§6) rather than deciding silently — and note when this contradicts a
draft that asserted "no evidence," since that draft may need updating.

## 8. Write down the rules you applied

Before classifying, compose the explicit assignment rules for this project — the gatekeepers, the
direct-evidence bar, the multi-assignment policy, and any project-specific scope decisions the user has
made. These rules are passed verbatim to the classifier and adjudicator agents (see `workflow.md`), so
that every study is judged the same way and the result can be explained. Capturing them is also what lets
a future update re-run the same logic when new studies arrive.
