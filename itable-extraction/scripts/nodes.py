#!/usr/bin/env python3
"""Controlled vocabulary for treatment-node labels, and the validator that enforces it.

WHY THIS EXISTS
A network meta-analysis joins arms by STRING EQUALITY of their node labels. "Nivolumab +
Ipilimumab" and "Nivolumab plus iplimumab" are two nodes, not one, and the network silently
fragments: netmeta reports a disconnected component, or worse, reports a connected one that
is missing an edge nobody notices. The failure is invisible in the extraction sheet and only
surfaces as a wrong league table.

This module makes node labels machine-checkable. A project supplies a vocabulary file; every
label written into an extraction sheet must resolve against it exactly.

THE RULES (locked 2026-07-30)
  1. AGENT labels are UPPERCASE, 3-5 characters, no punctuation:
        SUN SOR PAZO AXI EVE PEM NIVO IPI ATEZO BELZ GIREN DURVA TREME
  2. COMBINATIONS join with a bare "+", NO SPACES:
        NIVO+IPI          not "NIVO + IPI", not "NIVO plus IPI", not "Nivo+Ipi"
     Component ORDER is fixed per combination by the vocabulary's `combinations` list. It is
     NOT derived from a rule - "backbone first" and "alphabetical" disagree, and a lookup
     table cannot drift the way a rule can.
  3. The pooled comparator is ONE label, by default NOADJ, whatever the trial actually used.
     What it actually was - placebo, observation, surgery alone - is recorded in a SEPARATE
     field so the blinding sensitivity analysis can still separate them. A trial whose control
     is an ACTIVE regimen (an add-on design) does NOT get NOADJ; it gets that regimen's label.
  4. Dose, intended duration and setting variants are SUFFIXED with a hyphen:
        SOR-1Y  SOR-3Y  PAZO-600  PAZO-800  NIVO-PERI  SOR-NEO
     The suffix is part of the node identity. Merging two variants into one node is a
     deliberate relabelling, which is the point: it cannot happen by accident.

WHITESPACE IS THE ENEMY. A trailing space, a double space, or a non-breaking space creates a
phantom node that looks identical in a spreadsheet cell. The no-spaces rule removes the whole
class of failure rather than trying to normalise around it.
"""
import json
import os
import re
import sys

CANON_RE = re.compile(r"^[A-Z0-9]{2,6}(-[A-Z0-9]{1,5})?(\+[A-Z0-9]{2,6}(-[A-Z0-9]{1,5})?)*$")


class Vocabulary:
    """A project's controlled node vocabulary, loaded from JSON."""

    def __init__(self, blob):
        self.agents = blob["agents"]                      # LABEL -> generic name
        self.combinations = blob.get("combinations", [])  # exact canonical strings, ordered
        self.variants = blob.get("variants", {})          # LABEL -> what the suffix means
        self.comparator = blob.get("comparator", "NOADJ")
        self.comparator_forms = blob.get("comparator_forms", [])
        self.aliases = {k.lower(): v for k, v in blob.get("aliases", {}).items()}
        self.arms = blob.get("arms", {})                  # record id -> {treatment:[], control:...}

    @classmethod
    def load(cls, path):
        with open(path) as fh:
            return cls(json.load(fh))

    def valid_labels(self):
        s = set(self.agents) | set(self.combinations) | set(self.variants) | {self.comparator}
        return s

    def resolve(self, raw):
        """Return (canonical_label, note). canonical_label is None if it cannot be resolved."""
        if raw is None:
            return None, "empty"
        s = str(raw).strip()
        if not s or s.upper() in {"NA", "N/A", "NR", "-"}:
            return None, "empty"

        # Exact hit on the vocabulary - the only silent success.
        if s in self.valid_labels():
            return s, None

        # An alias the project has explicitly mapped (a trial's own wording, a known misspelling).
        if s.lower() in self.aliases:
            return self.aliases[s.lower()], f"resolved via alias from {s!r}"

        # Everything below is a REJECTION with a diagnosis, never a silent repair.
        if re.search(r"\bplus\b|\band\b|/|&|,", s, re.I):
            guess = re.sub(r"(?i)\s*(?:plus|and|/|&|,)\s*", "+", s).upper()
            return None, (f"{s!r} uses a word or symbol joiner. The only joiner is '+'. "
                          f"Did you mean {guess!r}?")
        if re.search(r"\s", s):
            guess = re.sub(r"\s*\+\s*", "+", s).upper()
            guess = re.sub(r"\s+", "", guess)
            return None, (f"{s!r} contains whitespace. Combination labels join with a bare '+' "
                          f"and no spaces. Did you mean {guess!r}?")
        if s != s.upper():
            up = s.upper()
            hint = f" Did you mean {up!r}?" if up in self.valid_labels() else ""
            return None, f"{s!r} is not uppercase.{hint}"
        if "+" in s:
            parts = s.split("+")
            unknown = [p for p in parts if p not in self.agents and p not in self.variants]
            if unknown:
                return None, f"{s!r} contains component(s) not in the vocabulary: {unknown}"
            for c in self.combinations:
                if sorted(c.split("+")) == sorted(parts):
                    return None, (f"{s!r} has the right components in the wrong order. "
                                  f"The canonical string is {c!r}.")
            return None, (f"{s!r} is a combination the vocabulary does not define. Add it to "
                          f"`combinations` with the component order you want, or fix the label.")
        if "-" in s:
            base = s.split("-")[0]
            if base in self.agents:
                known = [v for v in self.variants if v.startswith(base + "-")]
                return None, (f"{s!r} is an undefined variant of {base}. Defined variants: "
                              f"{known or 'none'}. Add it to `variants` or use {base!r}.")
        return None, f"{s!r} is not in the vocabulary and matches no alias."


def check_rows(vocab, rows):
    """rows = [{record, field, value}]. Returns (ok, problems, resolved)."""
    problems, resolved = [], {}
    for r in rows:
        label, note = vocab.resolve(r["value"])
        if label is None and note != "empty":
            problems.append({**r, "problem": note})
        elif label is not None:
            resolved[(r["record"], r["field"])] = label
            if note:
                problems.append({**r, "problem": "ACCEPTED but non-canonical - " + note})
    return (not [p for p in problems if not p["problem"].startswith("ACCEPTED")]), problems, resolved


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: nodes.py <vocabulary.json> [label ...]\n"
                 "  with labels: resolve each and report\n"
                 "  without:     print the vocabulary")
    vocab = Vocabulary.load(sys.argv[1])
    labels = sys.argv[2:]
    if not labels:
        print(f"comparator: {vocab.comparator}")
        print(f"  actual control forms recorded separately: {', '.join(vocab.comparator_forms) or '(none listed)'}")
        print(f"\nagents ({len(vocab.agents)}):")
        for k, v in sorted(vocab.agents.items()):
            print(f"  {k:<10} {v}")
        if vocab.combinations:
            print(f"\ncombinations ({len(vocab.combinations)}) - order is canonical, not derived:")
            for c in vocab.combinations:
                print(f"  {c}")
        if vocab.variants:
            print(f"\nvariants ({len(vocab.variants)}):")
            for k, v in sorted(vocab.variants.items()):
                print(f"  {k:<12} {v}")
        if vocab.aliases:
            print(f"\naliases ({len(vocab.aliases)}) - accepted on input, rewritten on output:")
            for k, v in sorted(vocab.aliases.items()):
                print(f"  {k!r:<46} -> {v}")
        return
    bad = 0
    for raw in labels:
        label, note = vocab.resolve(raw)
        if label and not note:
            print(f"  OK        {raw!r} -> {label}")
        elif label:
            print(f"  ACCEPTED  {raw!r} -> {label}   ({note})")
        else:
            bad += 1
            print(f"  REJECTED  {note}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
