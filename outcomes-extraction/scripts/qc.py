#!/usr/bin/env python3
"""QC filled outcome tables: structure, no-empty-cells, NA fill-rate, and HR sanity.

Usage:
  python qc.py <filled.xlsx> [<filled.xlsx> ...]

Checks per file:
  - 25 columns (A-Y) present
  - no empty data cell in G-Y (every field should be filled, NA where unreported)
  - count of NA per column (fill-rate sense check)
  - HR sanity: wherever TE, Lower CI, Upper CI are all numeric, that lower <= TE <= upper
"""
import sys, openpyxl
from openpyxl.utils import get_column_letter

def role_of(label):
    if not label: return None
    return str(label).split("(ID")[0].strip().lower()

def num(x):
    try: return float(str(x))
    except Exception: return None

def qc(path):
    wb = openpyxl.load_workbook(path, data_only=True); ws = wb.active
    print(f"\n=== {path}  dims={ws.dimensions} cols={ws.max_column} ===")
    if ws.max_column != 25:
        print(f"  WARNING: expected 25 columns, got {ws.max_column}")
    # locate TE / Lower CI / Upper CI columns by role
    tec = {}
    for r in (2, 3):
        for c in range(7, ws.max_column + 1):
            role = role_of(ws.cell(row=r, column=c).value)
            if role in ("te", "lower ci", "upper ci") and role not in tec:
                tec[role] = c
    empties, na_count, hr_issues, ci_no_te, nrows = [], {}, [], [], 0
    for r in range(4, ws.max_row + 1):
        if ws.cell(row=r, column=1).value is None: continue
        nrows += 1; pid = ws.cell(row=r, column=1).value
        for c in range(7, min(ws.max_column, 25) + 1):
            v = ws.cell(row=r, column=c).value
            col = get_column_letter(c)
            if v is None or str(v).strip() == "":
                empties.append((r, col, pid))
            elif str(v).strip() == "NA":
                na_count[col] = na_count.get(col, 0) + 1
        if all(k in tec for k in ("te", "lower ci", "upper ci")):
            te = num(ws.cell(row=r, column=tec["te"]).value)
            lo = num(ws.cell(row=r, column=tec["lower ci"]).value)
            up = num(ws.cell(row=r, column=tec["upper ci"]).value)
            if None not in (te, lo, up) and not (lo <= te <= up):
                hr_issues.append((r, pid, lo, te, up))
            # logical consistency: a CI with no TE is impossible to *report*
            # (almost always a survival-RATE CI mis-placed into the HR-CI columns).
            if te is None and (lo is not None or up is not None):
                ci_no_te.append((r, pid, lo, up))
    print(f"  data rows: {nrows}")
    print(f"  EMPTY cells (should be 0): {len(empties)}", empties[:10] if empties else "")
    print(f"  NA per column: " + ", ".join(f"{k}:{v}" for k, v in sorted(na_count.items())))
    print(f"  HR sanity violations (need lower<=TE<=upper): {len(hr_issues)}", hr_issues if hr_issues else "")
    print(f"  CI-without-TE (likely mis-placed rate CI): {len(ci_no_te)}", ci_no_te if ci_no_te else "")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python qc.py <filled.xlsx> [<filled.xlsx> ...]")
    for p in sys.argv[1:]:
        qc(p)
    print("\nQC done.")
