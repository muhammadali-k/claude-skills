# Schema mapping: SoF Excel → GDT JSON-LD

This is the field-by-field record of what `scripts/sof_to_gdt.py` writes into the output JSON-LD, where
each value comes from, and — critically — exactly which target fields it leaves `null` and why. Read this
before treating the converter's output as complete; several fields need a manual pass in MAGICapp
regardless of how well the conversion ran.

**Scope (v1):** every outcome this converter handles is `evidenceSummary[i].@type: "DichotomousData"`
paired with `question.outcome[i].@type: ["Outcome","TimeToEvent"]` — the only shape confirmed by direct
inspection of a real GDT export (all 36 outcomes in the sample file were this shape). Other GDT outcome
types (`Continuous`, `Narrative`) are out of scope for v1; the source Excel format this skill reads is
itself always this dichotomous/time-to-event shape (relative effect + two absolute rates + risk
difference), so this isn't currently a practical limitation, only a documented boundary.

## How to read the tables below

Each row is tagged with how confident the mapping is:
- **confirmed** — directly observed in a real GDT JSON-LD sample during this skill's development.
- **derived** — computed from the source Excel by a parsing rule (regex etc.), not guessed.
- **constant / default** — a fixed value the converter always emits because the source Excel cannot
  supply anything better; chosen as the safest generic value, not a guess at the true value.
- **null (deliberate)** — left empty on purpose because nothing in the source Excel can honestly populate
  it. Never a fabricated number.
- **extrapolated / unconfirmed** — inferred by analogy from the one confirmed case, not independently
  verified against a real sample. Flagged so a reviewer knows to double-check it if it matters.

## 1. Parsing the source Excel

These rules run once per input `.xlsx`, before any JSON is built. All columns are located by matching a
keyword in the row-1 (and, for the Absolute sub-columns, row-2) header text — not by hardcoded column
letter — so the converter survives minor header reordering.

| Source cell | Parsing rule | Extracted value(s) |
|---|---|---|
| A ("Outcomes") | Split on `\n`; if the last line matches `^\d+\s+citations?$`, capture that count and drop the line; remaining lines joined = the stratum/subgroup text | `stratum` (used only to cross-check the citation count below — **not written into the output JSON on its own**; any stratum text ends up in the output only via the filename-derived outcome name, per the source format's own convention of repeating it there) |
| B ("Relative") | `([A-Za-z]{2,4})\s*([\d.]+)` → prefix + point estimate; `([\d.]+)\s*to\s*([\d.]+)` or a parenthesized `(lo–hi)` form → the two CI bounds | `prefix` (HR/RR/OR/… — generic, not hardcoded to HR), `point`, `ci_lo`, `ci_hi` — **kept in source order** (first number = "From", second = "To"), never numerically re-sorted |
| C ("Intervention") | `([\d.]+)\s*per\s*1000` | `intervention_rate` — parsed but **not written to any output field** (see callout below) |
| D ("Control") | `([\d.]+)\s*per\s*1000` | `control_rate` |
| E ("Risk Difference") | `([\d.]+)\s*(fewer|less|more)\s*per\s*1000` | `rd_signed` = **−**value for "fewer"/"less", **+**value for "more" |
| F ("Certainty of Evidence") | `overall:?\s*(.+)` | `certainty_display` (uppercased, e.g. `"VERY LOW"`), `certainty_key` (lowercased/underscored, e.g. `"very_low"`); anything other than High/Moderate/Low/Very low is a hard parse failure |
| G ("Citations") | Every non-empty cell from the data row downward (this is how citation rows overflowing below the record are collected) | `citations` list; `n_studies = len(citations)`, falling back to the A-column's stated count only if zero citation rows were found |
| filename | Strip a trailing `_YYYYMMDD_HHMM` (regex `_\d{8}_\d{4}$`); underscores → spaces | the outcome's display name, e.g. `ORR_(DrugX_vs_Placebo)_Subgroup_A_20260101_0900.xlsx` → `"ORR (DrugX vs Placebo) Subgroup A"` (fictional example) |

A malformed cell (wrong pattern, missing header) raises an error naming the file and the exact cell text
it couldn't parse — the converter does not guess past a layout it doesn't recognize.

## 2. Top-level document fields

| Target JSON-LD path | Value | Confidence |
|---|---|---|
| `@id` | a freshly generated UUID | constant (generated fresh each run — not derived from anything, just a required identifier) |
| `@context` | a fixed 3-entry array (`@base`/`@vocab`/schema.org & Cochrane-ontology prefixes in entry 0; PICO/outcome container terms in entry 1; `title`/`sofTitle`/list-container terms in entry 2) | extrapolated — modeled on the *shape* of a real sample's context (3 entries, same @base/@vocab), but not byte-verified against the full real context, which wasn't captured verbatim during research |
| `@type` | `"ManagementEvidenceProfile"` | confirmed |
| `version` | `"1"` | constant / default — the field's real semantics (a schema version? a document revision?) were never confirmed; this is a placeholder |
| `modificationTime` | the conversion run's local timestamp, ISO-8601 with UTC offset, second precision | generated at run time, not from source |
| `bibliography` | `{"value": ""}` | constant / default — the source Excel gives no bibliography-level text; the `{value: str}` shape is guessed by analogy with other `{value: …}` fields elsewhere in the schema, unconfirmed |
| `title` | `--title`, or generated `"Should {intervention} vs. {comparator} be used for {population}?"` | CLI flag, or a template built from CLI flags |
| `sofTitle` | `--sof-title`, or generated `"{intervention} vs. {comparator} for {population}"` | CLI flag, or template |
| `question` | see §3 | built from CLI flags + per-outcome parses |
| `explanation` | one placeholder entry + one plain-language entry per outcome — see §6 | see §6 |
| `evidenceSummary` | one entry per outcome, same order as `question.outcome` | see §4 |
| `reference` | `[]` (always empty) | not attempted — see §7 |

## 3. `question` (the PICO object)

| Target path | Value | Confidence |
|---|---|---|
| `question.@id` | `"questions/<same uuid as the top-level @id>"` | extrapolated — a reasonable, internally-consistent choice, not confirmed against a real sample's linking convention |
| `question.@type` | `"PICO"` | confirmed |
| `question.healthProblemOrPopulation.@type` | `"HealthProblemOrPopulation"` | extrapolated — this exact literal wasn't captured verbatim during research |
| `question.healthProblemOrPopulation.name.value` | `--population`, verbatim | CLI flag |
| `question.healthProblemOrPopulation.setting.value` | `""` (always empty) | null (deliberate) — there's no `--setting` flag, and nothing in the source Excel states a care setting |
| `question.intervention.name` / `.@type` | `--intervention` / `"Intervention"` | CLI flag / confirmed constant |
| `question.comparison.name` / `.@type` | `--comparator` / `"Comparison"` | CLI flag / confirmed constant |
| `question.outcome[i].@id` | `"outcomes/<fresh uuid>"`, one per outcome | generated per outcome |
| `question.outcome[i].@type` | `["Outcome", "TimeToEvent"]` | confirmed (v1 scope, §"Scope" above) |
| `question.outcome[i].name.value` | filename-derived display name, or `--outcome-name` for single-file runs | derived (§1) |
| `question.outcome[i].event.@type` | `"Event"` | confirmed |

## 4. `evidenceSummary[i]` — one per outcome

Cross-referenced to its outcome via `forOutcome.@id`, generated in lock-step with the matching
`question.outcome[i].@id` so the two arrays always line up positionally *and* by reference.

| Target path | Value | Confidence |
|---|---|---|
| `@type` | `"DichotomousData"` | confirmed (v1 scope) |
| `forOutcome.@id` | the paired outcome's `@id` | generated, cross-referenced |
| `studyDesign` | `{"@type": "RandomisedTrials", "name": "randomised trials"}` | constant / default — the source Excel never states study design; if the underlying evidence is actually observational, this needs a manual fix after import |
| `numberOfStudies.value` | citation-row count (§1) | derived |
| `patientGroup[0]` (`InterventionGroup`) `.totalCount.value` | `null` | **null (deliberate)** — no per-arm N anywhere in this Excel format |
| `patientGroup[1]` (`ControlGroup`) `.totalCount.value` | `null` | **null (deliberate)**, same reason |
| `measuredWith` | `{"@type": "OutcomeMeasure", "name": ""}` | confirmed shape; `name` left blank (no instrument text in source) |
| `effectSummary.@type` | `"Pooled"` | confirmed |
| `effectSummary.relativeEffect.@type` | `HazardRatio` for HR, `RiskRatio` for RR, `OddsRatio` for OR; any other prefix passes through literally (with a printed warning) | **`HazardRatio` confirmed**; `RiskRatio`/`OddsRatio` are **extrapolated** — only the HR case was directly observed in the real sample |
| `.value.value` | point estimate | derived (§1) |
| `.confidenceLevel.value` | `0.95` | constant |
| `.confidenceIntervalFrom` / `.confidenceIntervalTo` | the two CI bounds, source order preserved | derived (§1) — **not** numerically sorted; "From"/"To" mean "first number in the cell" / "second number", matching how the source presents them |
| `effectSummary.absoluteEffect[0].@type` | `"AutoCalculatedAbsoluteEffect"` | confirmed |
| `.forControlRisk.@id` | `"_:cr1"` | matches `controlRisk[0].@id` below |
| `.value.value` | signed risk difference per 1000 | derived (§1) |
| `.confidenceLevel.value` | `0.95` | constant / default — assumed to match the relative effect's level; not independently stated anywhere in the source |
| `.confidenceIntervalFrom` / `.confidenceIntervalTo` | `null` / `null` | **null (deliberate) — see the callout below** |
| `.denominator` | `1000` | confirmed, matches the "per 1000" convention used throughout the source |
| `quality.@type` | `"GradeQuality"` | confirmed |
| `quality.value` | `null` | confirmed — the real sample also carries `null` here even though `name` states the level |
| `quality.name` | e.g. `"MODERATE"`, `"VERY LOW"` | derived (§1) |
| `quality.riskOfBias` / `.inconsistency` / `.indirectness` / `.imprecision` | `null` (all four) | **null (deliberate)** — the source gives only the single overall rating, no domain breakdown |
| `quality.otherConsiderations.name` | `""` | constant |
| `.publicationBias` | `null` | null (deliberate) — not in source |
| `.doseResponseGradient` / `.plausibleConfounding` / `.largeEffect` | `{"@type": "NoChange", "name": "no"}` (all three) | constant / default, matches the confirmed real-sample shape — these are **assumed "no"**, not independently assessed from the source |
| `controlRisk[0].@id` | `"_:cr1"` | matches `absoluteEffect[0].forControlRisk.@id` |
| `controlRisk[0].@type` | `"LowControlRisk"` — **always this literal**, regardless of the actual rate | confirmed that this label is cosmetic/arbitrary in the real schema; the converter deliberately doesn't try to infer Low/Moderate/High from the number, so don't read anything into it |
| `controlRisk[0].value` | `control_rate / 10`, rounded to 4 dp | derived — confirmed "per 1000 → per 100" conversion |

### Why `intervention_rate` (column C) never appears in the output

The source Excel states the intervention arm's absolute rate directly (e.g. "420 per 1000", fictional
example), and the converter does parse it — but GDT's schema has no field to put it in.
`effectSummary.absoluteEffect[0].@type` is `"AutoCalculatedAbsoluteEffect"` (confirmed against the real
sample), meaning GDT/MAGICapp derives the intervention arm's risk itself from `controlRisk` +
`relativeEffect` rather than storing it as its own number. So `intervention_rate` is parsed, used only to
confirm the row makes internal sense (lower rate + HR&lt;1 = favors intervention, etc. — a sanity check,
not a written field), and then dropped. This isn't a bug or an oversight; there's genuinely nowhere in the
target schema for it to go. If MAGICapp's import ever displays the intervention arm's rate incorrectly
after import, it's being recomputed from `controlRisk` and the relative effect, not read from this value —
worth knowing if a post-import number looks off.

### Why the absolute-effect CI is left null

The source Excel gives exactly three numbers for the absolute effect: the intervention arm's rate, the
control arm's rate, and the (already-computed) signed risk difference. **None of those, alone or
together, determine a confidence interval on the risk difference.** Computing one honestly would require
either the per-arm events/N (not in this export) or converting the *relative*-effect CI through GDT's own
absolute-risk-transform formula (not confirmed by this skill's research). A symmetric-offset guess around
the point value would also be provably wrong whenever the underlying relative-effect CI is asymmetric —
which HR/RR/OR confidence intervals almost always are. So the converter leaves both bounds `null` rather
than fabricate numbers that would look authoritative in MAGICapp but aren't derivable from anything.

## 5. Fields intentionally left `null` — quick-scan list

- `patientGroup[0].totalCount.value`, `patientGroup[1].totalCount.value` — per-arm N, both arms
- `quality.value`, `quality.riskOfBias`, `quality.inconsistency`, `quality.indirectness`, `quality.imprecision`
- `quality.otherConsiderations.publicationBias`
- `effectSummary.absoluteEffect[0].confidenceIntervalFrom` and `.confidenceIntervalTo`
- `question.healthProblemOrPopulation.setting.value` (always `""`, not `null`, but equally uninformative)

None of these are bugs to fix by guessing — they're gaps in what this Excel format contains at all. Check
them manually in MAGICapp after import (per its own "beta feature, verify the import" guidance).

## 6. Plain-language summary embedding (`explanation[]`)

`explanation[0]` is always `{"@type": "Explanation", "@id": "_:e0", "text": "no_explanation_provided"}` —
mirroring the one PICO-level, unreferenced placeholder item found in the real confirmed sample (nothing
else in that sample points to it via `@id`). One further `Explanation` entry is appended **per outcome**,
carrying the generated plain-language sentence (see `plain_language_conventions.md`) and a `forOutcome`
property pointing at that outcome's `@id`.

**`forOutcome` on an `Explanation` object is this skill's own extension, not a confirmed schema field.**
The real sample's single `explanation` item has no per-outcome linkage anywhere, and no documented
GRADEpro/GDT field for a per-outcome plain-language summary was found during research. Modeling the
cross-reference the same way `evidenceSummary[i].forOutcome` links to an outcome is the most
schema-consistent extension available, but it is *not verified* that MAGICapp's importer (or GRADEpro
itself) does anything with it. Treat the JSON embedding as a courtesy, not the delivery mechanism — the
companion `_plain_language_summaries.md` file is what you actually paste into MAGICapp.

(For engineers with MAGICapp API access: MAGICapp's own OpenAPI spec confirms a real, named, per-outcome
`plainSummaryComment` string field on `OutcomeDichotomous`/`OutcomeContinuous`/`OutcomeNonPoolable`,
writable via `PUT /api/v1/picos/{picoId}/outcomes/dichotomous/{id}/summary` after the GDT import completes
and outcome IDs exist. That's a genuine, confirmed destination — but populating it is a follow-up API call
outside this skill's CLI, which only produces the JSON-LD + the companion file.)

## 7. Fields not attempted

- **`reference`** (top level) — always `[]`. The target schema's exact reference-object shape (author,
  journal, DOI, year, …) was not confirmed by research, and the source's "Citations" column is unstructured
  free text (e.g. an author/year string), not per-field metadata. Mapping it to a guessed shape risked
  producing something that looks structured but isn't trustworthy, so it's simply not populated.
- **`bibliography`** (top level) — see §2; left as a placeholder empty-value object, not populated from
  the citation strings for the same reason as `reference`.
- **Raw citation text** — not written into the JSON-LD anywhere (it only feeds `numberOfStudies.value`).
  If you need the citation strings preserved for reference, they remain visible in the source `.xlsx`
  files themselves; nothing in this skill's output currently repeats them.
