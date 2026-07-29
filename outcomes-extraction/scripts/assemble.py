#!/usr/bin/env python3
"""Assemble adjudicated results into outcome templates (in place, backup first).

Handles all three template families — `pwma` (incl. the legacy OS/DFS/RFS sheets), `nma`, and
`pwma_subgroup` — detected from each file's own header by scripts/families.py.

Usage:
  python assemble.py --config _work/assemble_config.json

Config schema (see references/workflow.md):
  {
    "results": "_work/extraction_results.json",       # the workflow's {papers:[...]} return value
    "today": "2026-07-28",                            # backup date stamp
    "files": {"PWMA": {"path": "/abs/pwma_template.xlsx", "family": "pwma"}, ...},
    "study_info": {"1483": {"trial_name","nct","pmid","arms"}, ...}   # per paper-id (string keys)
  }

*** THE Ec/Et TRAP ***
The result JSON always uses PWMA semantics, and only PWMA semantics:
    et = EVENTS in treatment, nt = N in treatment, ec = EVENTS in control, nc = N in control.
The NMA sheet labels its columns "Ec T1 / Et T1 / Ec T2 / Et T2", where Ec is the EVENT COUNT and
Et is the EVENT TOTAL (participants) — the opposite meaning of `Et`. That relabelling happens HERE,
once, at write time (events -> Ec, N -> Et), so no extractor ever has to hold two conventions in
its head. Never hand-edit an NMA sheet using the PWMA convention: the numbers stay plausible and
nothing downstream catches the swap.

Maps every value to a column BY HEADER ROLE (never by column letter — each family has its own field-ID
set). Writes all data cells as TEXT; missing -> "NA". Backs up each file once. Emits a provenance
workbook next to the results.
"""
import argparse, json, os, shutil, sys, openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import families as F

# result-object key -> internal role. Aliases let a result object be explicit about the counts
# ("events_treatment") instead of relying on the PWMA shorthand; both are accepted.
RESULT_KEYS = {
    "te": ("hr", "te", "measure"),
    "lower_ci": ("ci_lower", "lower_ci"),
    "upper_ci": ("ci_upper", "upper_ci"),
    "treatment": ("treatment_name", "treatment", "regimen_t1"),
    "control": ("control_name", "control", "regimen_t2"),
    "surv_t": ("surv_treatment", "surv_t"),
    "surv_c": ("surv_control", "surv_c"),
    "events_t": ("et", "events_treatment", "events_t"),
    "n_t": ("nt", "n_treatment", "n_t"),
    "events_c": ("ec", "events_control", "events_c"),
    "n_c": ("nc", "n_control", "n_c"),
    "med_t": ("median_treatment", "med_t"),
    "med_c": ("median_control", "med_c"),
}


def pick(res, role):
    for k in RESULT_KEYS[role]:
        if k in res and res[k] is not None:
            return res[k]
    return None


def s(v):
    if v is None: return "NA"
    v = str(v).strip()
    return v if v else "NA"


def norm(x): return " ".join(str(x or "").split()).lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = json.load(open(ap.parse_args().config))
    workdir = os.path.dirname(os.path.abspath(cfg["results"]))
    data = json.load(open(cfg["results"]))
    papers = data["papers"] if isinstance(data, dict) and "papers" in data else data
    info = {str(k): v for k, v in cfg.get("study_info", {}).items()}
    today = cfg.get("today", "backup")
    files = F.files_from_cfg(cfg)

    # index results by (paper_id, table, comparison, subgroup) — subgroup is "" on main sheets,
    # so one keying scheme covers all three families.
    idx, pinfo = {}, {}
    for p in papers:
        pid = int(p["paper_id"])
        pinfo[pid] = {"of": p.get("of_recommendation"), "pmid": p.get("pmid"),
                      "nct": p.get("nct"), "trial_name": p.get("trial_name"),
                      "paper_flags": p.get("paper_flags", []),
                      "adjudications": p.get("adjudications", []) or p.get("disagreements", []),
                      "unresolved": p.get("unresolved", []),
                      "confidence": p.get("confidence", "")}
        for res in p.get("results", []):
            idx[(pid, res["table"], norm(res["comparison"]), norm(res.get("subgroup", "")))] = res

    prov, flags, longr, missing = [], [], [], []
    for table, path in files.items():
        bak = path.replace(".xlsx", f"_BACKUP_{today}.xlsx")
        if not os.path.exists(bak): shutil.copy2(path, bak)
        wb = openpyxl.load_workbook(path); ws = F.sheet_of(wb)
        lay = F.Layout(ws)
        if lay.missing_roles():
            raise SystemExit(f"{table}: header did not resolve roles {sorted(lay.missing_roles())} "
                             f"(family={lay.family}, roles={sorted(lay.roles)})")
        print(f"[{table}] family={lay.family}  {F.COUNT_COLS_HELP[lay.family]}")

        for r in range(4, ws.max_row + 1):
            pid, comp, sub = lay.key(r)
            if pid is None: continue
            pid = int(pid)
            si = info.get(str(pid), {}); pi = pinfo.get(pid, {})

            def put(role, val):
                c = lay.col(role)
                if c: ws.cell(row=r, column=c).value = s(val)

            put("trial_name", si.get("trial_name") or pi.get("trial_name"))
            put("nct", si.get("nct") or (pi.get("nct") if s(pi.get("nct")) != "NA" else "NA"))
            put("pmid", si.get("pmid") or pi.get("pmid"))
            put("of", pi.get("of"))
            if lay.col("zero"): put("zero", si.get("zero", "0"))     # nma has no "(0 selected)" column
            put("arms", str(si.get("arms", "2")))

            res = idx.get((pid, table, norm(comp), norm(sub)))
            if res is None:
                missing.append((table, pid, comp, sub))
                for role in F.DATA_ROLES: put(role, "NA")
                if lay.col_extraction_possible:
                    ws.cell(row=r, column=lay.col_extraction_possible).value = "NA"
                flags.append([table, pid, comp, sub, "NO RESULT MATCHED",
                              "check workflow output / comparison+subgroup labels"])
                continue

            for role in F.DATA_ROLES:
                put(role, pick(res, role))
            if lay.col_extraction_possible:
                # honest "no" belongs here rather than a blank row or an invented value
                ws.cell(row=r, column=lay.col_extraction_possible).value = s(res.get("extraction_possible"))

            for pr in res.get("provenance", []):
                prov.append([table, pid, comp, sub, res.get("endpoint_used"),
                             pr.get("field"), pr.get("source"), pr.get("snippet")])
            for fl in res.get("flags", []):
                flags.append([table, pid, comp, sub, "flag", fl])
            longr.append([table, lay.family, pid, comp, sub, res.get("extraction_possible"),
                          res.get("endpoint_used"), res.get("surv_timepoint"),
                          pick(res, "treatment"), pick(res, "control"), pick(res, "te"),
                          pick(res, "lower_ci"), pick(res, "upper_ci"),
                          pick(res, "surv_t"), pick(res, "surv_c"),
                          pick(res, "events_t"), pick(res, "n_t"),
                          pick(res, "events_c"), pick(res, "n_c"), pi.get("of")])
        wb.save(path)
        print(f"[{table}] filled {ws.max_row - 3} rows -> {path}")

    for pid, pi in pinfo.items():
        for f in pi.get("paper_flags", []): flags.append(["(paper)", pid, "", "", "paper_flag", f])
        for d in pi.get("adjudications", []):
            flags.append([d.get("table"), pid, d.get("comparison"), d.get("subgroup", ""), "SENIOR ADJUDICATION",
                          f"{d.get('field')}: A={d.get('value_a', d.get('extractor_value'))} "
                          f"B={d.get('value_b')} -> senior={d.get('senior_value', d.get('resolved_value'))} "
                          f"[agreed_with={d.get('agreed_with')}] ({d.get('reason')})"])
        for u in pi.get("unresolved", []):
            flags.append([u.get("table"), pid, u.get("comparison"), u.get("subgroup", ""),
                          "UNRESOLVED — NEEDS A HUMAN", f"{u.get('field')}: {u.get('why')}"])

    pv = openpyxl.Workbook()
    a = pv.active; a.title = "Provenance"
    a.append(["Table", "PaperID", "Comparison", "Subgroup", "Endpoint", "Field", "Source", "Snippet"])
    for row in prov: a.append(row)
    b = pv.create_sheet("Flags_and_Changes")
    b.append(["Table", "PaperID", "Comparison", "Subgroup", "Type", "Detail"])
    for row in flags: b.append(row + [""] * (6 - len(row)))
    c = pv.create_sheet("Long_format")
    c.append(["Table", "Family", "PaperID", "Comparison", "Subgroup", "ExtractionPossible", "EndpointUsed",
              "Timepoint", "Treatment", "Control", "TE", "LowerCI", "UpperCI", "SurvT", "SurvC",
              "EventsTreatment", "NTreatment", "EventsControl", "NControl", "O/F"])
    for row in longr: c.append(row)
    pvp = os.path.join(workdir, "outcomes_provenance.xlsx"); pv.save(pvp)
    print(f"[provenance] {pvp}  (prov={len(prov)}, flags/changes={len(flags)}, long={len(longr)})")
    print("MISSING RESULTS:" if missing else "All rows matched a result.")
    for m in missing: print("   ", m)


if __name__ == "__main__":
    main()
