# Node labels: the controlled vocabulary

## Why this is a hard rule and not a style preference

A network meta-analysis joins arms by **string equality**. `netmeta` does not know that
"Nivolumab + Ipilimumab" and "Nivolumab plus iplimumab" are the same regimen. It creates two
nodes, and then one of three things happens, in increasing order of how long it takes to
notice:

1. The network reports as disconnected and you find out immediately. This is the good case.
2. The network stays connected through some other path, an edge silently disappears, and the
   league table is wrong in a way nothing flags.
3. Two nodes that should have been one each carry half the evidence, both are underpowered,
   and the ranking inverts.

None of this is visible in the extraction sheet. Every cell looks fine. That is why node
labels are validated mechanically rather than left to care.

**This is not hypothetical.** In the Living Periop RCC project, CheckMate 914 Part A's single
treatment arm appeared four different ways across two templates — `Nivolumab + Iplimumab`,
`Nivolumab plus iplimumab`, `Nivulumab + ipililumab`, `Nivolumab plus ipilimumab` — three of
them containing misspellings, and all four would have been distinct nodes. `Atezolezumab` and
`Atezolizumab` both appeared for IMmotion010; `Everolimus` and `Everoilmus` for EVEREST.

A secondary reason, which matters more than it sounds: **long labels wreck the output.** A
league table is an n×n grid of node names. "Pembrolizumab plus belzutifan" as a column header
forces either a rotated axis or a truncated one, and a network plot with names that long is
unreadable. Short labels are a presentation decision as much as a data-integrity one.

## The rules

**1. Agent labels are UPPERCASE, 3–5 characters, no punctuation.**
```
SUN  SOR  PAZO  AXI  EVE  PEM  NIVO  IPI  ATEZO  BELZ  GIREN  DURVA  TREME
```
Long enough to read without a legend if you know the field; short enough that an 11-node
league table fits on a page.

**2. Combinations join with a bare `+`, no spaces.**
```
NIVO+IPI        PEM+BELZ        DURVA+TREME
```
Not `NIVO + IPI`, not `NIVO plus IPI`, not `Nivo+Ipi`. The no-spaces rule exists to delete an
entire class of failure: a trailing space, a double space, or a non-breaking space pasted from
a PDF creates a phantom node that is **visually identical** in a spreadsheet cell. You cannot
see it, and neither can a reviewer. Forbidding whitespace outright is cheaper than trying to
normalise around it.

**3. Component order is fixed by a lookup, not by a rule.**
The vocabulary file lists each combination as an exact canonical string. Order is not derived.
"Backbone first" and "alphabetical" disagree — `NIVO+IPI` versus `IPI+NIVO` — and two people
applying a rule will resolve it differently on different days. A list cannot drift.

**4. The pooled comparator is ONE label.**
Default `NOADJ`. Every control arm gets it, whatever the trial actually used. What it actually
was — placebo, observation, surgery alone plus surveillance, active monitoring — is recorded
in a **separate field** (`control_actual`), so a blinding or control-type sensitivity analysis
can still separate them.

The alternative — labelling controls `PBO`, `OBS`, `SURG` and merging downstream — fragments
the comparator every time somebody forgets to merge. The merge has to be remembered once per
analysis, forever. This way it is remembered once, in the vocabulary.

**One exception, and it is important.** A trial whose control arm is an **active regimen** —
an add-on design — does **not** get `NOADJ`. It gets that regimen's own label, because it is
genuinely a different node. In the Periop RCC project LITESPARK-022 is the only such trial:
its control is pembrolizumab plus placebo, so its control label is `PEM`, and that is what
chains belzutifan onto the pembrolizumab node instead of dangling it off the comparator.

**5. Dose, duration and setting variants are hyphen-suffixed.**
```
SOR-1Y  SOR-3Y  SOR-NEO  PAZO-600  PAZO-800  NIVO-PERI
```
The suffix is **part of the node identity**. Merging two variants into one node then becomes a
deliberate relabelling rather than something that happens by accident because two people typed
the same base name. That is the whole point: the default is to keep them apart, and combining
them is a decision somebody has to make explicitly.

## The vocabulary file

Each project supplies its own `*_node_vocabulary.json`. The skill supplies the rules and the
validator; the project supplies the drug list. Shape:

```json
{
  "comparator": "NOADJ",
  "comparator_forms": ["placebo", "observation", "surgery alone + surveillance"],
  "agents":       {"SUN": "sunitinib", "NIVO": "nivolumab", "IPI": "ipilimumab"},
  "combinations": ["NIVO+IPI"],
  "variants":     {"SOR-1Y": "sorafenib, 1 year intended duration"},
  "aliases":      {"nivolumab plus iplimumab": "NIVO+IPI", "placebo": "NOADJ"},
  "arms": {
    "1500": {"trial": "CheckMate 914 A", "treatment": ["NIVO+IPI"],
             "control": "NOADJ", "control_actual": "placebo"}
  }
}
```

`aliases` is where every wrong spelling you have ever seen goes. It accepts legacy data on
input and rewrites it to canonical on output — but the validator **reports** every alias hit
rather than resolving it silently, so a sheet full of legacy labels is visible as such.

`arms` pins the expected labels per record. It is what lets the validator catch a row that is
internally well-formed but attached to the wrong trial.

## Using it

```bash
# print the vocabulary
python scripts/nodes.py <project>_node_vocabulary.json

# resolve specific labels, exit non-zero if any are rejected
python scripts/nodes.py <project>_node_vocabulary.json "NIVO + IPI" "Nivo+Ipi" "NIVO+IPI"
```

`scripts/qc.py` runs the same check over a filled sheet and fails the run on any rejection.

Rejections carry a diagnosis and a suggestion, not just a complaint:

```
REJECTED  'NIVO + IPI' contains whitespace. Combination labels join with a bare '+'
          and no spaces. Did you mean 'NIVO+IPI'?
REJECTED  'IPI+NIVO' has the right components in the wrong order. The canonical
          string is 'NIVO+IPI'.
REJECTED  'SOR-5Y' is an undefined variant of SOR. Defined variants: ['SOR-1Y',
          'SOR-3Y', 'SOR-NEO']. Add it to `variants` or use 'SOR'.
```

## What to do when a new trial arrives

Add its agents to `agents`, its combination to `combinations` **with the component order you
want**, and its record to `arms`. Do not invent a label at extraction time and backfill the
vocabulary later — that is exactly how the second spelling gets in.

If a new trial uses a drug already in the vocabulary but in a different setting or dose that
the review has decided to keep separate, add a **variant**, do not reuse the base label.
Reusing the base label silently merges two nodes, which is the failure this whole file exists
to prevent.
