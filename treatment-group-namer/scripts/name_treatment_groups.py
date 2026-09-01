#!/usr/bin/env python3
"""
name_treatment_groups.py

Map individual treatment comparisons (drug-level) to their treatment-group
(drug-class-level) labels for a clinical-guideline evidence module, following the
module's naming convention: keep arm order and the 'plus' / 'vs' structure exactly,
substitute each drug token with its class label, leave pass-through tokens verbatim,
never add the word 'alone'.

Usage
-----
  # one comparison per line in a file (blank lines and #-comments ignored):
  python name_treatment_groups.py comparisons.txt

  # or pass comparisons directly as arguments:
  python name_treatment_groups.py "Tamoxifen plus Ovarian Function Suppression vs Tamoxifen"

  # custom map:
  python name_treatment_groups.py --map /path/to/drug-class-map.json comparisons.txt

Output
------
A two-column Markdown table (Treatment group | Individual treatment) on stdout.
Warnings — unmapped drugs, and within-class collapses where both arms reduce to the
same label so the group name is uninformative — are printed to stderr so they don't
pollute the table but are still visible.
"""

import argparse
import json
import os
import re
import sys

DEFAULT_MAP = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "references", "drug-class-map.json"
)

# Arms are separated by 'vs' / 'vs.' / 'versus'. Components within an arm are joined
# by 'plus'. Note we deliberately do NOT split on 'followed by' — it is part of an
# atomic regimen name (e.g. "Anthracycline/Cyclophosphamide followed by Taxane"),
# which is handled as a single pass-through token.
ARM_SPLIT = re.compile(r"\s+(?:vs\.?|versus)\s+", re.IGNORECASE)
COMP_SPLIT = re.compile(r"\s+plus\s+", re.IGNORECASE)


def load_map(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    drug_to_label = {}
    for label, drugs in data.get("classes", {}).items():
        for d in drugs:
            drug_to_label[d.strip().lower()] = label
    passthrough = {p.strip().lower(): p for p in data.get("passthrough", [])}
    return drug_to_label, passthrough


def map_component(comp, drug_to_label, passthrough, unmapped):
    key = comp.strip().lower()
    if key in passthrough:          # emit canonical casing of the pass-through token
        return passthrough[key]
    if key in drug_to_label:        # substitute the drug with its class label
        return drug_to_label[key]
    unmapped.append(comp.strip())   # unknown token: echo it unchanged and flag it
    return comp.strip()


def name_group(comparison, drug_to_label, passthrough):
    unmapped = []
    arms = ARM_SPLIT.split(comparison.strip())
    mapped_arms = []
    for arm in arms:
        comps = COMP_SPLIT.split(arm.strip())
        mapped = [map_component(c, drug_to_label, passthrough, unmapped) for c in comps]
        mapped_arms.append(" plus ".join(mapped))
    group = " vs ".join(mapped_arms)
    collapsed = len({a.strip().lower() for a in mapped_arms}) < len(mapped_arms)
    return group, unmapped, collapsed


def normalize_individual(comparison):
    """Echo the individual treatment for the second column, normalizing only the
    'versus' connector to 'vs' so the two columns read consistently. Drug names are
    left exactly as the user supplied them (never re-cased — that would break tokens
    like CDK4/6 or pCR)."""
    return ARM_SPLIT.sub(" vs ", comparison.strip())


def read_inputs(args_positional):
    # If the single positional argument is a readable file, treat it as a list.
    if len(args_positional) == 1 and os.path.isfile(args_positional[0]):
        with open(args_positional[0], "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f]
        return [ln for ln in lines if ln and not ln.startswith("#")]
    return [a.strip() for a in args_positional if a.strip()]


def main():
    ap = argparse.ArgumentParser(description="Name treatment groups from individual treatments.")
    ap.add_argument("inputs", nargs="+", help="A .txt file (one comparison per line) OR comparison strings.")
    ap.add_argument("--map", default=DEFAULT_MAP, help="Path to drug-class-map.json.")
    args = ap.parse_args()

    drug_to_label, passthrough = load_map(args.map)
    comparisons = read_inputs(args.inputs)
    if not comparisons:
        print("No comparisons provided.", file=sys.stderr)
        sys.exit(1)

    rows = []
    warnings = []
    for comp in comparisons:
        group, unmapped, collapsed = name_group(comp, drug_to_label, passthrough)
        rows.append((group, normalize_individual(comp)))
        for u in unmapped:
            warnings.append(f"UNMAPPED drug/token '{u}' in: {comp}  -> left unchanged; add it to the map.")
        if collapsed:
            warnings.append(
                f"WITHIN-CLASS COLLAPSE in: {comp}  -> group '{group}' is uninformative "
                f"(both arms reduce to the same class); consider naming at the drug level here."
            )

    print("| Treatment group | Individual treatment |")
    print("|---|---|")
    for group, individual in rows:
        print(f"| {group} | {individual} |")

    if warnings:
        print("", file=sys.stderr)
        for w in warnings:
            print("⚠ " + w, file=sys.stderr)


if __name__ == "__main__":
    main()
