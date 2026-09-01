---
name: treatment-group-namer
description: >-
  Map individual treatment comparisons (drug-level regimens like "Tamoxifen plus
  Ovarian Function Suppression vs Tamoxifen") to their treatment-group drug-class
  labels (like "SERM plus Ovarian Function Suppression vs SERM") for a clinical
  practice guideline evidence module — the two-level "Treatment Group then
  Individual Treatment" hierarchy in living-guideline navigators. Use whenever the
  user has individual treatment comparisons and needs the treatment-group name
  above them, or asks to arrange comparisons as treatment categories or groups.
  Trigger for "name the treatment groups for these comparisons", "what group does
  this go under", or "arrange these as treatment categories", even when the user
  only pastes drug comparisons and does not say "skill". Covers breast cancer
  endocrine and targeted regimens (SERM, aromatase inhibitor, ER degrader, CDK4/6
  inhibitor, ovarian function suppression); preserves arm order and plus/vs
  structure, never adds "alone", and flags unmappable drugs or within-class
  collapses.
---

# Treatment-group namer

## What this skill does

Living-guideline evidence modules present supporting evidence through a two-level
hierarchy: a **Treatment Group** step (the drug-*class* comparison, e.g.
`Aromatase Inhibitor plus Ovarian Function Suppression vs SERM`) and, nested under it,
an **Individual Treatment** step (the specific drug-*level* comparison, e.g.
`Exemestane plus Ovarian Function Suppression vs Tamoxifen`). Authors write the
individual treatments first — the actual regimens compared in the trials — and then need
the treatment-group label to sit above them.

This skill produces that treatment-group label **from the individual treatment**, in the
exact naming convention the module uses. It is a deterministic string transformation
backed by an editable drug-to-class map: substitute each drug token with its class label,
keep everything else identical.

**The governing principle is structural fidelity.** The treatment group is the individual
treatment with drug names lifted to their class — nothing more. Preserve the arm order,
the `plus` groupings, and the `vs` split exactly. Never reorder arms to a house
preference, never add or drop a component, and never add the word "alone" to a single
agent. If a token has no more-specific class (it is already a modality, a placebo, an
observation arm, or a named chemotherapy backbone), it passes through untouched.

## Before you start

Two resources do the work:

- **`references/drug-class-map.json`** — the single source of truth. Each key under
  `classes` is the exact treatment-group label to emit; its value lists the drug names
  that map to it. `passthrough` lists tokens emitted verbatim. **This is the only file you
  edit to extend coverage** (new drug, new class, new pass-through token).
- **`scripts/name_treatment_groups.py`** — a deterministic mapper. Prefer it when naming
  more than a couple of comparisons or when consistency across a whole module matters; it
  guarantees identical treatment applied to every row and prints warnings for the two
  failure modes below. For a single quick mapping you may apply the rules by hand, but
  verify against the map — do not rely on memory of drug classes.

## Workflow

1. **Collect the individual treatments.** One comparison per line, e.g.
   `Exemestane plus Ovarian Function Suppression vs Tamoxifen`. If the user pasted a table
   or a numbered list, extract just the comparison strings.

2. **Run the mapper** (recommended for anything beyond one or two rows):
   ```bash
   python scripts/name_treatment_groups.py comparisons.txt
   ```
   or pass strings directly:
   ```bash
   python scripts/name_treatment_groups.py "Tamoxifen plus Ovarian Function Suppression vs Tamoxifen"
   ```
   It prints the two-column table to stdout and any warnings to stderr.

3. **Resolve warnings before delivering.** An `UNMAPPED` warning means a drug is not in the
   map — add it under the correct class in `references/drug-class-map.json` and rerun; do
   not guess a class inside the output. A `WITHIN-CLASS COLLAPSE` warning means both arms
   reduced to the same label (e.g. `Aromatase Inhibitor vs Aromatase Inhibitor`) — see
   *Guardrails* and raise it with the user.

4. **Deliver the two-column table** (Treatment group | Individual treatment). Then note
   any mappings worth the user's eye: pass-through tokens that stayed unchanged, and any
   row you flagged. Keep the note short — the user is checking the deltas, not re-reading
   the table.

## Naming convention — the essentials

The full anchor table, the primary worked set, and every edge case live in
`references/examples.md`. **Read it before naming anything non-obvious.** The headline
rules:

### Substitute the drug, keep the structure

Split the comparison into arms on ` vs ` (accept `versus` too). Split each arm into
components on ` plus `. Replace each drug component with its class label from the map;
reassemble with the same `plus` and `vs` connectors in the same positions.

- `Tamoxifen` → `SERM`
- `Exemestane` → `Aromatase Inhibitor`
- `Fulvestrant` → `Estrogen Receptor Degrader`
- `Palbociclib` → `CDK4/6 Inhibitor`

### Pass-through tokens stay verbatim

A component that does not resolve to a more specific named agent is emitted unchanged:
`Ovarian Function Suppression`, `No Systemic Treatment`, `Placebo`, `Observation`,
`Best Supportive Care`, and named chemotherapy backbones like
`Anthracycline/Cyclophosphamide followed by Taxane`. (That last one is a **single** token —
never split it on "followed by".)

### Casing and connectors

Class labels and drug names are Title Case; connectors are lowercase `plus` and `vs`.
Normalize any `versus` in the input to `vs` in the output.

### Acronym vs spelled-out is deliberate

`SERM` stays an acronym. `Aromatase Inhibitor`, `Estrogen Receptor Degrader`, and
`CDK4/6 Inhibitor` are spelled out. This mirrors how the module renders each class —
match it exactly rather than making them uniform.

### Never add "alone"

A single-agent arm is named by the agent alone: `Tamoxifen`, not "Tamoxifen alone", and
`SERM`, not "SERM alone". The comparison already supplies the contrast.

### Mirror order, don't canonicalize

Keep arms and components in the order the individual treatment gives them. If the source
arm is `Exemestane plus Ovarian Function Suppression`, the group is
`Aromatase Inhibitor plus Ovarian Function Suppression` — do not move OFS to the front
even if another module row happens to list it first.

## Guardrails (do not skip)

- **Unknown drug → flag, don't guess.** If a token is not in the map, echo it unchanged
  and tell the user, then extend `references/drug-class-map.json`. Inventing a class label
  inline produces silent inconsistency across the module.
- **Within-class collapse → flag.** When both arms map to the same class (e.g.
  `Exemestane vs Anastrozole` → `Aromatase Inhibitor vs Aromatase Inhibitor`), the
  group label is uninformative. Surface it and offer to keep that row at the drug level,
  or to add a qualifier if the module supports one (e.g. steroidal vs non-steroidal AI).
- **Only map what is on the page.** Do not enrich a comparison with trial names, lines of
  therapy, or populations the user did not include. The transformation is drug → class and
  nothing else.

## Output format

Default to a single two-column Markdown table:

```
| Treatment group | Individual treatment |
|---|---|
| SERM plus Ovarian Function Suppression vs SERM | Tamoxifen plus Ovarian Function Suppression vs Tamoxifen |
```

One row per comparison. If the module step instead wants standalone regimens bucketed
under a drug-class *category* (one category holding several regimens), see the
"Two shapes of output" note in `references/examples.md` and confirm the intended shape
with the user.

## Extending the skill

All coverage lives in `references/drug-class-map.json`. To add a drug, drop its lowercase
name under the right class. To add a class, add a new key whose exact text is the label to
emit, with its drug list. To add a pass-through token, append it to `passthrough`. No code
changes are needed — the script reads the map at runtime.

## References

- `references/drug-class-map.json` — the drug-to-class map and pass-through list (edit here to extend).
- `references/examples.md` — anchor drug↔class pairs, the primary worked set, order-mirroring, within-class collapse, unknown-drug, atomic-regimen, and the two output shapes. **Read before naming anything non-obvious.**
