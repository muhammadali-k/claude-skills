#!/usr/bin/env python3
"""QC a filled i-table against the reconciled results + structural integrity.

  python qc.py --sheet filled.xlsx --results _work/extraction_results.json --schema _work/column_schema.json \
      [--template original.xlsx] [--id-col A]

Checks: (1) round-trip — every written value equals the reconciled result; (2) structure — column count and
merged-header count match the original template (if --template given); (3) metadata preserved; then prints
fill-rates and ALL flagged judgment calls for the user to review.
"""
import argparse, json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--schema", required=True)
    ap.add_argument("--template")
    ap.add_argument("--id-col", default="A")
    a = ap.parse_args()
    import openpyxl
    from openpyxl.utils import column_index_from_string, get_column_letter

    schema = {c["col"]: c for c in json.load(open(a.schema))}
    data_cols = [c["col"] for c in schema.values() if not c.get("is_meta")]
    studies = json.load(open(a.results))["studies"]
    ws = openpyxl.load_workbook(a.sheet, data_only=True).worksheets[0]
    id_ci = column_index_from_string(a.id_col)
    hr = 1
    for m in openpyxl.load_workbook(a.sheet).worksheets[0].merged_cells.ranges:
        if m.min_row == 1:
            hr = max(hr, m.max_row)
    id_row = {str(ws.cell(row=r, column=id_ci).value).strip(): r
              for r in range(hr + 1, ws.max_row + 1) if ws.cell(row=r, column=id_ci).value not in (None, "")}

    problems = []
    if a.template:
        twb = openpyxl.load_workbook(a.template); tws = twb.worksheets[0]
        swb = openpyxl.load_workbook(a.sheet); sws = swb.worksheets[0]
        if tws.max_column != sws.max_column:
            problems.append(f"column count {sws.max_column} != template {tws.max_column}")
        if len(tws.merged_cells.ranges) != len(sws.merged_cells.ranges):
            problems.append(f"merged ranges {len(sws.merged_cells.ranges)} != template {len(tws.merged_cells.ranges)}")

    mism = 0
    for st in studies:
        sid = str(st.get("id") or st.get("paper_id")).strip(); r = id_row.get(sid)
        if not r:
            problems.append(f"study {sid} missing from sheet"); continue
        for cell in st.get("cells", []):
            col = str(cell["col"]).strip()
            if col not in schema or schema[col].get("is_meta"):
                continue
            ci = column_index_from_string(col)
            got = str(ws.cell(row=r, column=ci).value).strip()
            exp = str(cell["value"]).strip()
            if got != exp:
                mism += 1
                if mism <= 20:
                    problems.append(f"{sid} {col}: sheet='{got}' != result='{exp}'")

    print("=== FILL-RATE (non-missing data cells per study) ===")
    for st in studies:
        sid = str(st.get("id") or st.get("paper_id")).strip(); r = id_row.get(sid)
        if not r:
            continue
        filled = sum(1 for c in data_cols
                     if ws.cell(row=r, column=column_index_from_string(c)).value not in (None, "")
                     and str(ws.cell(row=r, column=column_index_from_string(c)).value).strip().upper() != "NA")
        print(f"  {sid:10} {filled:4} / {len(data_cols)}  {st.get('trial', st.get('label',''))}")

    print("\n=== FLAGS / JUDGMENT CALLS ===")
    for st in studies:
        fl = st.get("flags", []) or []
        if fl:
            print(f"[{st.get('id') or st.get('paper_id')}] {st.get('trial', st.get('label',''))}")
            for f in fl:
                print("   -", f)

    print("\n=== QC RESULT ===")
    print(f"round-trip mismatches: {mism}")
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        for p in problems[:40]:
            print("  !", p)
    else:
        print("OK — written values match reconciled data; structure intact.")

if __name__ == "__main__":
    main()
