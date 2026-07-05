#!/usr/bin/env python3
"""Dump the structure of outcome to_extract / example xlsx files so you can learn the layout.

Usage:
  python inspect_tables.py <file.xlsx> [<file.xlsx> ...]

For each sheet it prints: merged ranges, the header rows with each field's role + (ID: NNNN) tag,
and the data rows (so you can see pre-seeded studies and example values). Read this before extracting.
"""
import sys, openpyxl
from openpyxl.utils import get_column_letter

def role_of(label):
    if not label: return None
    return str(label).split("(ID")[0].strip()

def dump(path):
    print("=" * 92)
    print("FILE:", path)
    print("=" * 92)
    wb = openpyxl.load_workbook(path, data_only=True)
    for ws in wb.worksheets:
        print(f"\n--- SHEET: {ws.title}  dims={ws.dimensions}  rows={ws.max_row} cols={ws.max_column}")
        if ws.merged_cells.ranges:
            print("  merged:", [str(r) for r in ws.merged_cells.ranges][:48])
        # header field map (scan rows 1-3, cols G+)
        print("  field map (col -> role (ID)):")
        for r in range(1, 4):
            cells = []
            for c in range(7, ws.max_column + 1):
                v = ws.cell(row=r, column=c).value
                if v is not None and str(v).strip():
                    cells.append(f"{get_column_letter(c)}={v}")
            if cells:
                print(f"    R{r}: " + " | ".join(cells))
        # data rows
        for r in range(1, min(ws.max_row, 40) + 1):
            row = []
            for c in range(1, ws.max_column + 1):
                v = ws.cell(row=r, column=c).value
                if v is not None and str(v).strip():
                    row.append(f"{get_column_letter(c)}{r}={v!r}")
            if row and r >= 4:
                print("  " + " | ".join(row))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python inspect_tables.py <file.xlsx> [<file.xlsx> ...]")
    for p in sys.argv[1:]:
        dump(p)
