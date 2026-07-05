# Eval fixtures (mostly local-only)

The eval cases in `../evals.json` reference fixture files that are **intentionally not committed**:

- Full-text trial PDFs and supplements (e.g. `2023_Baek_JCO.pdf`, `2019_Mamounas_LancetOnc.pdf`,
  `paperA/B/C.pdf`) — these are **copyrighted journal articles** and must not be redistributed here.
- `example_extractions.xlsx`, `input_sheet_2rows.xlsx`, `prefilled_with_type_errors.xlsx` — working
  spreadsheets containing extracted trial data; kept out of the repo per the "no unpublished data" rule.

`columns.csv` (a small synthetic column list used by the no-example test) **is** included as a format sample.

To run the evals locally, drop the referenced PDFs/spreadsheets into this folder using the filenames in
`../evals.json`, then follow the skill-creator eval workflow.
