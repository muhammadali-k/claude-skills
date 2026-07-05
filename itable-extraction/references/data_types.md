# Upload data-type validation

Many i-table host systems validate **per-column data types** on import and reject the whole file if any
cell violates its column's type. The classic failures:

- `Value 'NA' must be a number` — a text missing-marker placed in a **numeric** column.
- `Value 'Tamoxifen + OFS' must contain only letters` — digits/symbols in a **letters-only** column
  (arm names, author names, category labels).

So "fill every blank with `NA`" — which reads fine to a human — breaks the upload. Each column has a type,
and the missing-value marker must match that type.

## Deriving column types from an example file
The example file uploads cleanly, so it encodes the correct type for every column. `parse_template.py`
derives types into `col_types.json` using this rule (and you should understand it, because it's the crux):

> **A column that contains a literal `NA` anywhere in the example cannot be a numeric column** — if it
> were, the example itself would have failed to import. So the example's own use of `NA` tells you which
> columns are text (NA-tolerant) vs numeric (NA-forbidden).

Concretely, per column across the example's data rows:
- **NUMBER** — every non-empty real value parses as a number AND the column never contains `NA`
  (missing is shown as blank or `0`, never `NA`). Numeric cells must hold a number; missing → blank, or
  `0` if the example uses `0` for missing (some do — e.g. a median age that wasn't reported).
- **LETTER** — every non-empty real value is letters + spaces only (no digits/`+`/`-`/`/`/parens). `NA`
  is allowed here (it's letters). Arm-name, phase, setting, yes/no columns are often LETTER.
- **TEXT** — everything else (`N (%)` strings, free text, identifiers with hyphens). `NA` is fine.

Columns that are all-`NA`/blank in the example are ambiguous; if they contain a literal `NA` they are
treated as TEXT (safe). Truly empty-everywhere columns are left as TEXT unless the user says otherwise.

## Fixing violations (`validate_types.py --fix`)
- **NUMBER column holding a non-number** (`NA`, `NA-not stated`, `Not reported (NA)`, etc.) → replace with
  the example's numeric-missing convention: blank, or `0` if the example uses `0`. Genuine numbers are kept.
- **LETTER column holding non-letters** → sanitize to letters + spaces while preserving meaning:
  `+` → `plus`, `->`/`→` → `then`, `/` → `or`, spell small digits (`6 yr` → `six years`), drop residual
  symbols/parentheses, collapse spaces. `NA` is left as-is. Examples:
  - `Tamoxifen + OFS` → `Tamoxifen plus OFS`
  - `Anastrozole 6 yr` → `Anastrozole six years`
  - `Letrozole -> Tamoxifen` → `Letrozole then Tamoxifen`
  - `Tjan-Heijnen et al` → `Tjan Heijnen et al`
- **Identifiers that should be present** (e.g. a PubMed ID column that the example always fills) — prefer
  filling the real value over a placeholder. PMIDs can be resolved from a DOI via the PubMed MCP
  (`convert_article_ids`, id_type `doi`); verify ambiguous matches with `get_article_metadata`.

After fixing, re-scan: every NUMBER cell numeric, every LETTER cell letters+spaces-or-`NA`, zero
violations. Keep a pre-fix safety copy. Record what changed (old → new + reason) in the provenance file so
the formatting transforms are auditable — they are display changes, not new data.

## If there is no example file
You can't derive types. Either ask the user for the target system's column types (or a sample of a
previously-accepted file), or skip type-validation and warn the user the file may need type fixes on
upload. Do not invent types silently.
