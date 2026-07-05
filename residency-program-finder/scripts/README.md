# Deliverable builders

Two scripts turn a verified program list into the applicant's deliverables. Both take the **same two files** so you build the list once and render it two ways.

```bash
python3 build_workbook.py programs.json --config config.json --out "program list.xlsx"
python3 build_interactive_list.py programs.json --config config.json --out "apply list.html"
```

`build_workbook.py` needs **openpyxl** (`pip install openpyxl`). `build_interactive_list.py` is pure standard library and produces one self-contained HTML file (opens offline; searchable / sortable / filterable).

## `programs.json` — a JSON array of program records

Only `name` is strictly required; every other field defaults gracefully, so partial data still renders. Fill what you've verified and leave the rest blank.

```json
[
  {
    "name": "Example University Medical Center",
    "city": "Cleveland", "state": "OH",
    "division": "East North Central",
    "type": "university-affiliated",
    "tier": "Target",
    "signal": "Gold",
    "nonus_img": "~90% (roster 38/42)",
    "affinity": "3 — School A, School B, School C (roster-confirmed)",
    "same_school": true,
    "visa": "J-1 + H-1B",
    "fellowship": "enterprise NCI heme/onc",
    "verified": true,
    "url": "https://example.edu/.../internal-med-program",
    "notes": "Same-school resident + affinity-group APD; safe + prestige.",
    "re_nonus_rate": "5%",
    "re_gold": "31% (no-sig 1%)",
    "re_step": "243-267"
  }
]
```

Field meanings:
- **tier** — `Reach` | `Target` | `Safety`.
- **signal** — `Gold` | `Silver` | `""` (empty = apply but don't signal).
- **nonus_img** — the NON-US IMG share; note whether it's from the roster or an aggregator.
- **affinity** — the applicant's-nationality residents, as a count + schools + a confidence tag (`roster-confirmed` / `aggregator-only` / `not roster-confirmed`). This is the column the applicant cares about most.
- **same_school** — `true` if the applicant's OWN medical school is represented (drives the ◆ marker).
- **verified** — `true` only when read from the program's own current roster/visa page. Drives the "live-checked ✓" marker.
- **re_*** — optional Residency Explorer values; omit if RE wasn't used.
- **division** — the ERAS division; prefix out-of-preference programs with `(out-of-division)` if you want them grouped separately.

## `config.json` — labels and counts for headers/legends

```json
{
  "applicant": "Jane Doe",
  "specialty": "Internal Medicine",
  "cycle": "ERAS 20XX",
  "affinity_label": "Affinity group",
  "same_school_label": "Own school",
  "gold_count": 3,
  "silver_count": 12,
  "notes": "Free-text strategy summary shown on the workbook READ-ME sheet."
}
```

Every config key is optional; sensible defaults apply (specialty → "Internal Medicine", affinity_label → "Affinity", etc.).
