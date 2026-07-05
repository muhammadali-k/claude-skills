#!/usr/bin/env python3
"""Insert multi-arm comparison rows into outcome tables, contiguously (grouped by study).

Usage:
  python add_rows.py --config _work/add_rows_config.json

Config schema (see references/workflow.md):
  {
    "files": {"DFS": "/abs/pfs_to_extract.xlsx", "RFS": "/abs/rfs_to_extract.xlsx"},
    "new_rows": {"DFS": {"12269": ["Exemestane vs. Anastrozole", "Letrozole vs. Anastrozole"]},
                 "RFS": {"33451": ["Exemestane + ovarian suppression vs Tamoxifen alone"]}}
  }

For each new row it copies cols A-F (study metadata) from that study's existing row, sets col F to the
new comparison label, and inserts it immediately after that study's last existing row. Only the data
region (rows 4+) is rewritten; the merged header (rows 1-3) is left untouched. G-Y are cleared so
assemble.py fills them by ID+label afterward -- so add the matching result objects to
extraction_results.json first, then run add_rows, then re-run assemble.
"""
import argparse, json, openpyxl

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = json.load(open(ap.parse_args().config))
    for table, path in cfg["files"].items():
        want = {int(k): v for k, v in cfg.get("new_rows", {}).get(table, {}).items()}
        if not want:
            print(f"[{table}] no new rows; skipped"); continue
        wb = openpyxl.load_workbook(path); ws = wb.active
        rows = []
        for r in range(4, ws.max_row + 1):
            if ws.cell(row=r, column=1).value is None: continue
            rows.append([ws.cell(row=r, column=c).value for c in range(1, 7)])  # A-F
        meta = {}
        for row in rows:
            meta.setdefault(int(row[0]), row[1:5])  # B-E per pid
        new = []
        for i, row in enumerate(rows):
            new.append(row)
            pid = int(row[0])
            nxt = int(rows[i + 1][0]) if i + 1 < len(rows) else None
            if pid in want and pid != nxt:  # last occurrence of this study
                b, c, d, e = meta[pid]
                for lbl in want[pid]:
                    new.append([pid, b, c, d, e, lbl])
        maxr = max(ws.max_row, 3 + len(new))
        for r in range(4, maxr + 1):
            for c in range(1, 26): ws.cell(row=r, column=c).value = None
        for idx, row in enumerate(new):
            for c in range(6): ws.cell(row=4 + idx, column=c + 1).value = row[c]
        wb.save(path)
        added = sum(len(v) for v in want.values())
        print(f"[{table}] {len(rows)} -> {len(new)} rows (added {added}, grouped by study)")
        for row in new:
            if int(row[0]) in want and row[5] in want[int(row[0])]:
                print(f"     + {row[0]} | F='{row[5]}'")
    print("Done. Add the matching result objects to extraction_results.json, then re-run assemble.py.")

if __name__ == "__main__":
    main()
