# GRADE plain-language summary conventions

The rules `scripts/sof_to_gdt.py` implements to turn `(relative effect, 95% CI, certainty, absolute
effect)` into one GRADE-conventions plain-language sentence **and** a recommended MAGICapp
"Direction of benefit" value per outcome — deterministically, no LLM call, from a single shared decision
tree so the two outputs can never disagree with each other. This is a standalone reference: a future
session or engineer should be able to follow it, or re-implement the generator from scratch, without
re-deriving GRADE methodology.

## Sources

- Santesso N, Glenton C, Dahm P, Garner P, Akl EA, Alper B, et al. "GRADE guidelines 26: informative
  statements to communicate the findings of systematic reviews of interventions." *J Clin Epidemiol.*
  2020;119:126–135. (PMID 31711912) — the primary methodology paper; wording was iterated against a
  110-respondent survey of producers/users of systematic reviews, keeping only phrasing ≥60% found
  acceptable.
- Schünemann HJ, Vist GE, Higgins JPT, Santesso N, Deeks JJ, Glasziou P, Akl EA, Guyatt GH. Chapter 15,
  "Interpreting results and drawing conclusions," *Cochrane Handbook for Systematic Reviews of
  Interventions* (current version) — Cochrane's own operationalization of Santesso 2020; Table 15.6.b and
  §§15.3.1/15.6.4 are the direct basis for the tables below.
- Corroborated by AHRQ / NCBI Bookshelf NBK563880, which reproduces the same four-tier structure.

## 1. Certainty → verb (reconstructed from Table 15.6.b)

`I` = intervention name, `O` = outcome name. Choose the reduction/increase noun or verb by the direction
of the point estimate (or, in the null-crossing cases below, by the direction each CI bound points).

| Certainty | Large effect | Moderate effect | Small effect | Trivial / no important effect |
|---|---|---|---|---|
| High | "`I` results in a large reduction/increase in `O`" | "`I` reduces/increases `O`" | "`I` reduces/increases `O` slightly" | "`I` results in little to no difference in `O`" |
| Moderate | "`I` probably results in a large reduction/increase in `O`" | "`I` probably reduces/increases `O`" | "`I` probably reduces/increases `O` slightly" | "`I` probably results in little to no difference in `O`" |
| Low | "`I` may result in a large reduction/increase in `O`" | "`I` may reduce/increase `O`" | "`I` may reduce/increase `O` slightly" | "`I` may result in little to no difference in `O`" |
| Very low | *(magnitude is not used — see below)* | | | |

**Very low certainty collapses the magnitude axis entirely.** There is no "large effect, very-low-certainty"
cell — regardless of what the point estimate or CI look like, the only sentence used is:

> "The evidence is very uncertain about the effect of `I` on `O`."

"Likely" and "probably" are Cochrane-sanctioned synonyms for the Moderate tier; "probably" is what this
generator uses (it's the more common default in published GRADEpro-style tables).

## 2. Magnitude classification

**GRADE does not define a universal numeric cutoff.** Magnitude (trivial/small/moderate/large) is
properly a judgment against a **minimally important difference (MID)** that a review/guideline panel
sets *per outcome* (Cochrane Handbook §15.3.1). Classify using the **point estimate**, not the CI bounds —
the CI's width feeds the null-crossing rule below instead, so re-deriving magnitude from the CI edges in
the ordinary case would double-count imprecision the certainty rating already reflects.

**This generator has no per-outcome MID.** The source Excel doesn't carry one, and `sof_to_gdt.py`'s CLI
only exposes one threshold triple per run — `--mid-small`, `--mid-moderate`, `--mid-large` (default
`5 / 20 / 40`, all in percent) — applied to **every** outcome in that run. This is the widely-used,
**explicitly non-authoritative** practical fallback for dichotomous outcomes: band the point estimate's
relative change from the null by:

| Relative change from null | Magnitude |
|---|---|
| < 5% | trivial |
| 5–20% | small |
| 20–40% | moderate |
| > 40% | large |

For HR/RR/OR, "relative change from null" is `\|1 − value\| × 100`. If you have a real, outcome-specific
MID, override `--mid-small/--mid-moderate/--mid-large` for that run rather than trust the default bands —
and if different outcomes in the same PICO need genuinely different MIDs, run the converter once per
outcome group and merge, since the CLI has no per-outcome override.

## 3. Handling a CI that crosses the null

Cochrane Handbook §15.6.4's principle: "no evidence of an effect" is not "evidence of no effect." If the
95% CI includes the null, the data are compatible with both a true benefit and a true harm — a conclusion
that leans on only one of those must also mention the other. Turning that into a deterministic rule means
classifying **both CI bounds** (not just the point estimate) against the magnitude bands above:

| Pattern | Meaning | Sentence used |
|---|---|---|
| CI does not cross the null | direction isn't in question | normal certainty×magnitude lookup on the point estimate (§1) |
| CI crosses the null, **both** bounds land in the trivial band | classic "no important difference" | the certainty's **trivial** cell (§1) |
| CI crosses the null, **one** bound trivial, the **other** reaches an important magnitude | meaningful effect possible in one direction, negligible in the other; importantly-harmful-elsewhere is implausible | the certainty's trivial cell, **plus** a hedge naming the possible direction: "…, but may `reduce`/`increase` `O`" |
| CI crosses the null and **both** bounds reach an important magnitude, in **opposite** directions | direction genuinely cannot be determined from the data | verb downshifted to "may" regardless of nominal certainty; states both directions explicitly; **flagged for human review** |

The fourth row is the one GRADE itself treats as a judgment call, not a formula — the generator produces
grammatically valid output for it, but every such outcome is marked `[NEEDS HUMAN REVIEW]` in the
companion checklist file specifically so it doesn't get pasted into MAGICapp unread.

## 3a. Direction of benefit (MAGICapp's own field — same branching, different output)

MAGICapp's outcome edit panel has a "Direction of benefit" selector: Intervention favourable / Comparator
favourable / No important difference / High uncertainty. It has no equivalent anywhere in GRADEpro's own
schema (confirmed absent from a real GDT export — see `schema_mapping.md`), so this skill can't set it via
the JSON-LD; instead it recommends a value using the *same* branches as the sentence generator above:

| Case (from §3 / §1's branches) | Direction of benefit |
|---|---|
| Very low certainty | `UNCERTAIN` ("High uncertainty") |
| CI crosses null, both bounds trivial | `NO_DIFF` |
| CI crosses null, one bound trivial / one important (the hedge case) | `UNCERTAIN` |
| CI crosses null, both bounds important, opposite directions | `UNCERTAIN` |
| CI doesn't cross null, magnitude trivial | `NO_DIFF` |
| CI doesn't cross null, magnitude small/moderate/large | `INT_BETTER` if the point estimate's direction matches `--favorable-direction` (default `reduction`), else `COMP_BETTER` |

The last row is the only place an assumption gets made: **this skill's v1 scope is dichotomous/
time-to-event outcomes (OS/DFS/PFS/RFS-style), where the "event" is something undesirable — death,
progression, recurrence — so a reduction in the event rate is assumed favourable to the intervention.**
That's a safe default for this scope, but it is an assumption, not something read from the source Excel
(which never states outcome valence). Pass `--favorable-direction increase` for the rare outcome where a
higher rate is the desirable direction; get it wrong and every clean-cut outcome in the run will recommend
the opposite of what a reviewer would pick.

## 4. How the generator assembles a sentence (matches `sof_to_gdt.py` exactly)

1. If certainty is **very low** → emit the fixed template (§1), append
   `(PREFIX point, 95% CI lo to hi; <certainty>-certainty evidence).` — done. (No absolute-effect text in
   this branch; magnitude was never evaluated.)
2. Else, check whether the relative-effect CI crosses the null (`1.0` for HR/RR/OR).
   - **No crossing** → classify the point estimate (§2), look up the certainty×magnitude cell (§1),
     append `(PREFIX point, 95% CI lo to hi; <risk-difference cell text verbatim>; <certainty>-certainty
     evidence).`
   - **Crossing** → classify both CI bounds (§2):
     - both trivial → the certainty's trivial cell, same parenthetical as above.
     - one trivial, one important → the certainty's trivial cell + `, but may reduce/increase <outcome>`
       (direction taken from whichever bound was important), same parenthetical.
     - both important, opposite directions → the fixed hedge sentence naming both directions, a
       parenthetical that explicitly caveats the absolute number as "at the point estimate" rather than a
       confident estimate, and the `[NEEDS HUMAN REVIEW]` flag.
3. The outcome name used inside the sentence (`O` in §1's templates) is **not** the full display name —
   it's everything in the outcome's display name before its first `(`. A filename-derived display name like
   `"ORR (DrugX vs Placebo) Subgroup A"` produces the sentence-internal label `"ORR"`. Since the source
   Excel never spells out the full outcome name (only its abbreviation survives into the filename — see
   `references/schema_mapping.md` §1), sentences necessarily read with whatever abbreviation the filename
   uses. Rename source files to spelled-out names before conversion, or pass `--outcome-name`, if you want
   a more polished sentence.
4. The risk-difference clause in the parenthetical is the **verbatim source cell text** (e.g. "120 fewer
   per 1000"), not a recomputed value.

## 5. Worked examples

All numbers below are **invented for illustration** — not from any real trial or real evidence file. Each
includes the paired Direction-of-benefit output (default `--favorable-direction reduction`, correct for all
of these since they're death/progression/event-type outcomes).

**High certainty, large effect (no crossing).**
Input: Drug A vs. Placebo, mortality, RR 0.55 (95% CI 0.45 to 0.68), high certainty, "120 fewer per 1000".
`|1−0.55|×100 = 45%` → large; CI doesn't cross 1.
> *"Drug A results in a large reduction in mortality (RR 0.55, 95% CI 0.45 to 0.68; 120 fewer per 1000;
> high-certainty evidence)."* — Direction of benefit: **Intervention favourable**.

**Moderate certainty, small effect (no crossing).**
Input: Drug B vs. standard care, disease progression, RR 0.88 (95% CI 0.79 to 0.98), moderate certainty,
"30 fewer per 1000". `|1−0.88|×100 = 12%` → small; CI doesn't cross 1.
> *"Drug B probably reduces disease progression slightly (RR 0.88, 95% CI 0.79 to 0.98; 30 fewer per 1000;
> moderate-certainty evidence)."* — Direction of benefit: **Intervention favourable**.

**Low certainty, trivial effect, narrow null-crossing (both bounds trivial).**
Input: Drug C vs. Placebo, minor adverse events, RR 0.98 (95% CI 0.96 to 1.04), low certainty, "2 fewer
per 1000". Both bounds are within 5% of the null (4% and 4%) → both trivial.
> *"Drug C may result in little to no difference in minor adverse events (RR 0.98, 95% CI 0.96 to 1.04;
> 2 fewer per 1000; low-certainty evidence)."* — Direction of benefit: **No important difference**.

**Very low certainty (magnitude not evaluated).**
Input: Drug D vs. Placebo, overall survival, HR 0.80 (95% CI 0.45 to 1.55), very low certainty.
> *"The evidence is very uncertain about the effect of Drug D on overall survival (HR 0.8, 95% CI 0.45 to
> 1.55; very low-certainty evidence)."* — Direction of benefit: **High uncertainty**.

**Moderate certainty, one bound trivial / one important (hedge).**
Input: Drug E vs. Placebo, "Readmission (Drug E vs Placebo)", RR 0.99 (95% CI 0.97 to 1.35), moderate
certainty, "3 fewer per 1000". Lower bound trivial (3%); upper bound reaches "moderate" magnitude (35%,
direction = increase).
> *"Drug E probably results in little to no difference in Readmission, but may increase Readmission
> (RR 0.99, 95% CI 0.97 to 1.35; 3 fewer per 1000; moderate-certainty evidence)."* — Direction of benefit:
> **High uncertainty**.
Note the mechanical repetition of the outcome name — this is exactly what the algorithm produces (§4,
step 2); it reads slightly awkwardly but is the templated, deterministic output. Light copyedit before
pasting into MAGICapp if you want smoother prose.

**Moderate certainty, both bounds important, opposite directions — direction undetermined (flagged).**
Input: Drug F vs. Placebo, major cardiovascular events, HR 0.62 (95% CI 0.30 to 1.55), moderate certainty,
"140 fewer per 1000". Lower bound → 70% reduction (large); upper bound → 55% increase (large). Both
important, opposite directions.
> *"Drug F may reduce major cardiovascular events, but it may also increase it — the evidence does not
> allow a clear conclusion about the direction of the effect (HR 0.62, 95% CI 0.3 to 1.55; approximately
> 140 fewer per 1000 at the point estimate, but the interval is compatible with either a large reduction
> or an increase in events; moderate-certainty evidence)."* — Direction of benefit: **High uncertainty**.
Flagged `[NEEDS HUMAN REVIEW]` in the companion checklist.

## 6. Known simplifications (spot-check these, don't silently trust them)

- **The "both important, opposite directions" template always says "a large reduction or an increase"**
  in its parenthetical, regardless of whether the two bounds actually classified as "large" vs. "moderate"
  vs. some other pairing — the phrase is fixed text, not re-derived per outcome. If one side is only
  "moderate," the sentence still says "large." Read the actual CI numbers alongside the sentence rather
  than trusting the adjective.
- **One shared `--mid-small/--mid-moderate/--mid-large` triple applies to every outcome in a run** — if a
  PICO mixes outcomes that genuinely need different MIDs (e.g. a hard endpoint like mortality vs. a
  patient-reported outcome), run the converter separately per group, or accept that the magnitude words
  ("slightly," "large," …) are calibrated the same generic way for all of them.
- **The sentence/direction generator does not use the absolute-effect CI** (which `sof_to_gdt.py` computes
  separately for the JSON-LD — see `schema_mapping.md`) to classify magnitude; every magnitude judgment in
  these sentences is made on the **relative** effect (HR/RR/OR) only, per §2 above. The absolute per-1000
  number is quoted in the parenthetical for context, not independently classified — the two computations
  (plain-language magnitude, and the absolute-effect CI written into the JSON) are separate code paths that
  happen to share the same relative-effect CI as an input, not the same classification logic.
- **Numbers are printed with trailing zeros stripped** (the source's `0.80` becomes `0.8` in the sentence,
  `0.30` becomes `0.3`, as in the worked examples above) — a formatting quirk from parsing cell text to
  `float`, not a transcription error if you're comparing sentence output back against the source cell.
- This whole generator is a **starting point for the sentence**, not a publication-ready one. GRADE panels
  make these calls with clinical judgment a formula can't fully replace — treat every output sentence,
  and especially every `[NEEDS HUMAN REVIEW]`-flagged one, as a draft to review, not a final answer.
