#!/usr/bin/env python3
"""Insert extra rows into an outcome template, contiguously (grouped by study, then by comparison).

Handles all three families:
  pwma / nma      -> one extra row per extra arm-vs-control COMPARISON (col F "Treatment Arm").
  pwma_subgroup   -> one extra row per (comparison x SUBGROUP LEVEL): subgroup label in col F,
                     "Extraction Possible" left blank in col G for the extraction to answer,
                     comparison label in col H.

Usage:
  python add_rows.py --config _work/add_rows_config.json

Config schema (see references/workflow.md):
  {
    "files": {"PWMA": {"path": "/abs/pwma_template.xlsx", "family": "pwma"},
              "SUB":  {"path": "/abs/pwma_subgroup_template.xlsx", "family": "pwma_subgroup"}},
    "new_rows": {
      "PWMA": {"1515": ["3 year Sorafenib"]},
      "SUB":  {"1553": [{"comparison": "Primary",
                         "subgroups": ["Risk group: High", "Risk group: M0 High"]}],
               "1515": [{"comparison": "3 year Sorafenib", "subgroup": "Risk group: M1 NED"}]}
    }
  }

THE NUMBER OF SUBGROUP LEVELS VARIES BY STUDY AND BY SUBGROUP TYPE — this script inserts exactly as
many rows as you list, per study, per comparison. Never assume every study has the same set (in the
seeded Living-Periop-RCC sheet most studies carry 4 risk-group levels but study 1553 carries 2).

For each new row it copies the pre-seeded metadata columns (Paper ID, Author, Title, Publish Date,
Publication ID) from that study's existing row, sets the key columns, and inserts it immediately after
the matching study/comparison block. Only the data region (rows 4+) is rewritten; the merged header
(rows 1-3) is untouched. The data fields are cleared so assemble.py fills them by role afterward — so
add the matching result objects to extraction_results.json first, then run add_rows, then re-run
assemble.
"""
import argparse, json, os, sys, openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import families as F


def specs_for(fam, raw, pid, table):
    """Normalize one study's new-row spec into a list of (comparison, subgroup) pairs."""
    out = []
    for item in raw:
        if fam == "pwma_subgroup":
            if not isinstance(item, dict):
                raise SystemExit(f"[{table}] {pid}: subgroup sheets need "
                                 f'{{"comparison": ..., "subgroups": [...]}}, got {item!r}')
            comp = item.get("comparison", "Primary")
            subs = item.get("subgroups") or ([item["subgroup"]] if item.get("subgroup") else [])
            if not subs:
                raise SystemExit(f"[{table}] {pid}: no subgroup level(s) given in {item!r}")
            out += [(comp, sg) for sg in subs]
        else:
            comp = item["comparison"] if isinstance(item, dict) else item
            out.append((comp, ""))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = json.load(open(ap.parse_args().config))
    files = F.files_from_cfg(cfg)

    for table, path in files.items():
        raw_want = cfg.get("new_rows", {}).get(table, {})
        if not raw_want:
            print(f"[{table}] no new rows; skipped"); continue
        wb = openpyxl.load_workbook(path); ws = F.sheet_of(wb)
        lay = F.Layout(ws)
        meta_cols = lay.meta_cols()
        want = {int(k): specs_for(lay.family, v, k, table) for k, v in raw_want.items()}

        # existing rows: full metadata block + their (pid, comparison, subgroup) key
        rows, keys, meta_by_pid = [], [], {}
        for r in range(4, ws.max_row + 1):
            if ws.cell(row=r, column=lay.col_paper_id).value is None: continue
            vals = [ws.cell(row=r, column=c).value for c in meta_cols]
            pid, comp, sub = lay.key(r)
            rows.append(vals); keys.append((int(pid), comp, sub))
            meta_by_pid.setdefault(int(pid), vals)
        existing = set(map(lambda k: (k[0], F.clean(k[1]).lower(), F.clean(k[2]).lower()), keys))

        def make(pid, comp, sub):
            vals = list(meta_by_pid[pid])
            for i, c in enumerate(meta_cols):
                if c == lay.col_comparison: vals[i] = comp
                elif c == lay.col_subgroup: vals[i] = sub
                elif c == lay.col_extraction_possible: vals[i] = ""   # the extraction answers this
            return vals

        # place each new row after the last existing row of its (study, comparison) block;
        # if that comparison doesn't exist yet, after the study's last row.
        placed, new, added = set(), [], []
        for i, (vals, (pid, comp, sub)) in enumerate(zip(rows, keys)):
            new.append(vals)
            nxt = keys[i + 1] if i + 1 < len(keys) else (None, None, None)
            for (ncomp, nsub) in want.get(pid, []):
                if (pid, ncomp, nsub) in placed: continue
                if (pid, F.clean(ncomp).lower(), F.clean(nsub).lower()) in existing: continue
                comp_exists = any(k[0] == pid and F.clean(k[1]).lower() == F.clean(ncomp).lower() for k in keys)
                end_of_comp_block = F.clean(comp).lower() == F.clean(ncomp).lower() and \
                    not (nxt[0] == pid and F.clean(nxt[1] or "").lower() == F.clean(ncomp).lower())
                end_of_study = nxt[0] != pid
                if (comp_exists and end_of_comp_block) or (not comp_exists and end_of_study):
                    new.append(make(pid, ncomp, nsub)); placed.add((pid, ncomp, nsub))
                    added.append((pid, ncomp, nsub))

        skipped = [(pid, c, s) for pid, specs in want.items() for (c, s) in specs
                   if (pid, c, s) not in placed]

        # rewrite the data region: clear everything, write back the metadata columns only
        maxr = max(ws.max_row, 3 + len(new))
        for r in range(4, maxr + 1):
            for c in range(1, ws.max_column + 1): ws.cell(row=r, column=c).value = None
        for i, vals in enumerate(new):
            for j, c in enumerate(meta_cols):
                ws.cell(row=4 + i, column=c).value = vals[j]
        wb.save(path)

        print(f"[{table}] family={lay.family}: {len(rows)} -> {len(new)} rows (added {len(added)})")
        for pid, c, s in added:
            print(f"     + {pid} | comparison={c!r}" + (f" | subgroup={s!r}" if s else ""))
        for pid, c, s in skipped:
            print(f"     ! {pid} | comparison={c!r} subgroup={s!r} — already present or study not in sheet")
    print("Done. Add the matching result objects to extraction_results.json, then re-run assemble.py.")


if __name__ == "__main__":
    main()
