# Worked examples and edge cases

These are the reference cases for `treatment-group-namer`. Read them when a mapping
is ambiguous or when you want to confirm a naming choice. Every example uses the
convention in the main SKILL.md: preserve arm order and the `plus` / `vs` structure,
substitute each drug with its class label, keep pass-through tokens verbatim, use
lowercase `plus` / `vs` with Title-Case labels, and never add "alone".

## Anchor: the drug ↔ class pairs seen in the module

From the "Support Evidences" navigator (the source of truth for house naming):

| Individual treatment token | Treatment-group token |
|---|---|
| Fulvestrant | Estrogen Receptor Degrader |
| Anastrozole / Letrozole / Exemestane | Aromatase Inhibitor |
| Tamoxifen | SERM |
| Palbociclib / Ribociclib / Abemaciclib | CDK4/6 Inhibitor |
| Goserelin / Leuprolide (or the modality itself) | Ovarian Function Suppression |
| Ovarian Function Suppression | Ovarian Function Suppression (pass-through) |
| No Systemic Treatment | No Systemic Treatment (pass-through) |
| Placebo | Placebo (pass-through) |
| Anthracycline/Cyclophosphamide followed by Taxane | Anthracycline/Cyclophosphamide followed by Taxane (pass-through) |

Note the intentional asymmetry: **SERM** stays an acronym; **Aromatase Inhibitor**,
**Estrogen Receptor Degrader**, and **CDK4/6 Inhibitor** are spelled out. That is how
the module renders them — match it exactly, don't "normalize" one to the other.

## Primary worked set — endocrine therapy for local breast cancer

The four comparisons this skill was first built from, each mapped comparison → group:

| Treatment group | Individual treatment |
|---|---|
| SERM plus Ovarian Function Suppression vs SERM | Tamoxifen plus Ovarian Function Suppression vs Tamoxifen |
| Aromatase Inhibitor plus Ovarian Function Suppression vs SERM plus Ovarian Function Suppression | Exemestane plus Ovarian Function Suppression vs Tamoxifen plus Ovarian Function Suppression |
| Aromatase Inhibitor plus Ovarian Function Suppression vs SERM | Exemestane plus Ovarian Function Suppression vs Tamoxifen |
| SERM vs No Systemic Treatment | Tamoxifen vs No Systemic Treatment |

Teaching points:
- Only the drug token changes. `Tamoxifen` → `SERM`, `Exemestane` → `Aromatase Inhibitor`.
  `Ovarian Function Suppression` and `No Systemic Treatment` carry through unchanged
  because neither resolves to a more specific named agent.
- Order is preserved arm-for-arm and component-for-component. If the source says
  `Exemestane plus Ovarian Function Suppression`, the group is
  `Aromatase Inhibitor plus Ovarian Function Suppression` — do not reorder to put OFS first.

## Order is mirrored, not canonicalized

The module contains a group written `Ovarian Function Suppression plus SERM vs ...`
(OFS first) and this skill would also produce `SERM plus Ovarian Function Suppression`
(drug first) from a source arm written drug-first. Both are correct **for their own
source**. The rule is: mirror the order of the individual treatment you were given;
never impose a house order of your own.

## Edge case — within-class collapse (flag it)

Input: `Exemestane vs Anastrozole`
Naive output: `Aromatase Inhibitor vs Aromatase Inhibitor`

This is a within-class comparison. The class-level label is uninformative — it looks
like a comparison of a thing against itself. **Flag this to the user** and offer to keep
the group at the drug level for this row (e.g., leave it as `Exemestane vs Anastrozole`,
or label it `Aromatase Inhibitor (steroidal) vs Aromatase Inhibitor (non-steroidal)` if
the module supports qualifiers). The script prints a `WITHIN-CLASS COLLAPSE` warning for
exactly this situation.

## Edge case — unknown drug (flag it, don't guess)

Input: `Elacestrant vs Fulvestrant` with a map that only has `fulvestrant`.
The script echoes `Elacestrant` unchanged and prints an `UNMAPPED` warning. Resolve it by
adding the drug to `references/drug-class-map.json` under the right class (here,
`Estrogen Receptor Degrader`) — never invent a class on the fly inside the output.

## Edge case — atomic regimen names contain "followed by"

Input arm: `Anthracycline/Cyclophosphamide followed by Taxane`
This is **one** token, not three. It is a pass-through and is emitted verbatim. Do not
split it on "followed by" and do not try to class-map "Anthracycline" or "Taxane"
separately. (The tokenizer only splits on `plus` and `vs`/`versus`, so this is handled
automatically — but reviewers sometimes try to "fix" it by hand; don't.)

## Two shapes of output the module may want

- **Comparison → group (default).** One row per comparison, group label is itself a
  comparison. This is the primary function and matches the navigator screenshots.
- **Bucketing regimens under a class category.** If a module step instead wants a flat
  list of individual *regimens* grouped under their drug-*class category* (one category
  holding several regimens — e.g. category **SERM** holding both `Tamoxifen` and
  `Tamoxifen plus Ovarian Function Suppression`), the same drug-class map drives it; you
  just group by the class of the core agent rather than mapping a full comparison. Ask
  the user which shape their module step expects if it is not obvious.
