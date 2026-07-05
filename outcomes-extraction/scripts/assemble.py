#!/usr/bin/env python3
"""Assemble verified OS/DFS/RFS results into the *_to_extract.xlsx files (in place, backup first).

Usage:
  python assemble.py --config _work/assemble_config.json

Config schema (see references/workflow.md):
  {
    "results": "_work/extraction_results.json",     # the workflow's {papers:[...]} return value
    "today": "2026-06-20",                            # backup date stamp
    "files": {"OS": "/abs/os_to_extract.xlsx", ...},  # table-key -> file path
    "study_info": {"33451": {"trial_name","nct","pmid","arms"}, ...}  # per paper-id (string keys)
  }

Maps each result to the right cell BY HEADER ROLE (robust to column-order differences). Writes all G-Y
cells as TEXT; missing -> "NA". Backs up each file once. Emits <stem>_provenance.xlsx next to the results.
"""
import argparse, json, os, shutil, openpyxl

ROLES = {
  "trial name":"trial_name","nct":"nct","pmid":"pmid","o/f":"of","(0 selected)":"zero","arms":"arms",
  "te":"te","lower ci":"lower_ci","upper ci":"upper_ci","treatment":"treatment","control":"control",
  "survival in treatment":"surv_t","survival in control":"surv_c","et":"et","nt":"nt","ec":"ec","nc":"nc",
  "median survival in treatment":"med_t","median survival in control":"med_c",
}
DATA_ROLES = ("te","lower_ci","upper_ci","treatment","control","surv_t","surv_c","et","nt","ec","nc","med_t","med_c")

def role_of(label):
    if not label: return None
    return ROLES.get(str(label).split("(ID")[0].strip().lower())

def build_colmap(ws):
    cmap = {}
    for r in (2, 3):
        for c in range(7, ws.max_column + 1):
            role = role_of(ws.cell(row=r, column=c).value)
            if role and role not in cmap: cmap[role] = c
    return cmap

def s(v):
    if v is None: return "NA"
    v = str(v).strip()
    return v if v else "NA"

def norm(x): return " ".join(str(x).split()).lower()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    cfg = json.load(open(ap.parse_args().config))
    workdir = os.path.dirname(os.path.abspath(cfg["results"]))
    data = json.load(open(cfg["results"]))
    papers = data["papers"] if isinstance(data, dict) and "papers" in data else data
    info = {str(k): v for k, v in cfg.get("study_info", {}).items()}
    today = cfg.get("today", "backup")

    # index results by (paper_id, table, normalized comparison)
    idx, pinfo = {}, {}
    for p in papers:
        pid = int(p["paper_id"])
        pinfo[pid] = {"of": p.get("of_recommendation"), "pmid": p.get("pmid"),
                      "nct": p.get("nct"), "trial_name": p.get("trial_name"),
                      "paper_flags": p.get("paper_flags", []), "disagreements": p.get("disagreements", []),
                      "confidence": p.get("confidence", "")}
        for res in p.get("results", []):
            idx[(pid, res["table"], norm(res["comparison"]))] = res

    prov, flags, longr, missing = [], [], [], []
    for table, path in cfg["files"].items():
        bak = path.replace(".xlsx", f"_BACKUP_{today}.xlsx")
        if not os.path.exists(bak): shutil.copy2(path, bak)
        wb = openpyxl.load_workbook(path); ws = wb.active
        cmap = build_colmap(ws)
        need = set(ROLES.values())
        if need - set(cmap):
            raise SystemExit(f"{table}: unmapped roles {need - set(cmap)} (colmap={cmap})")
        for r in range(4, ws.max_row + 1):
            pid = ws.cell(row=r, column=1).value
            if pid is None: continue
            pid = int(pid); comp = ws.cell(row=r, column=6).value
            si = info.get(str(pid), {}); pi = pinfo.get(pid, {})
            def put(role, val): ws.cell(row=r, column=cmap[role]).value = s(val)
            put("trial_name", si.get("trial_name") or pi.get("trial_name"))
            put("nct", si.get("nct") or (pi.get("nct") if s(pi.get("nct")) != "NA" else "NA"))
            put("pmid", si.get("pmid") or pi.get("pmid"))
            put("of", pi.get("of"))
            put("zero", "0")
            put("arms", str(si.get("arms", "2")))
            res = idx.get((pid, table, norm(comp)))
            if res is None:
                missing.append((table, pid, comp))
                for role in DATA_ROLES: put(role, "NA")
                flags.append([table, pid, comp, "NO RESULT MATCHED", "check workflow output / comparison label", ""])
                continue
            put("te", res.get("hr")); put("lower_ci", res.get("ci_lower")); put("upper_ci", res.get("ci_upper"))
            put("treatment", res.get("treatment_name")); put("control", res.get("control_name"))
            put("surv_t", res.get("surv_treatment")); put("surv_c", res.get("surv_control"))
            put("et", res.get("et")); put("nt", res.get("nt")); put("ec", res.get("ec")); put("nc", res.get("nc"))
            put("med_t", res.get("median_treatment")); put("med_c", res.get("median_control"))
            for pr in res.get("provenance", []):
                prov.append([table, pid, comp, res.get("endpoint_used"), pr.get("field"), pr.get("source"), pr.get("snippet")])
            for fl in res.get("flags", []):
                flags.append([table, pid, comp, "flag", fl, ""])
            longr.append([table, pid, comp, res.get("endpoint_used"), res.get("surv_timepoint"),
                          res.get("treatment_name"), res.get("control_name"), res.get("hr"),
                          res.get("ci_lower"), res.get("ci_upper"), res.get("surv_treatment"),
                          res.get("surv_control"), res.get("et"), res.get("nt"), res.get("ec"),
                          res.get("nc"), pi.get("of")])
        wb.save(path)
        print(f"[{table}] filled {ws.max_row - 3} rows -> {path}")

    for pid, pi in pinfo.items():
        for f in pi.get("paper_flags", []): flags.append(["(paper)", pid, "", "paper_flag", f, ""])
        for d in pi.get("disagreements", []):
            flags.append([d.get("table"), pid, d.get("comparison"), "VERIFIER CHANGED",
                          f"{d.get('field')}: extractor={d.get('extractor_value')} -> resolved={d.get('resolved_value')} ({d.get('reason')})", ""])

    pv = openpyxl.Workbook()
    a = pv.active; a.title = "Provenance"; a.append(["Table","PaperID","Comparison","Endpoint","Field","Source","Snippet"])
    for row in prov: a.append(row)
    b = pv.create_sheet("Flags_and_Changes"); b.append(["Table","PaperID","Comparison","Type","Detail","Extra"])
    for row in flags: b.append(row + [""] * (6 - len(row)))
    c = pv.create_sheet("Long_format"); c.append(["Table","PaperID","Comparison","EndpointUsed","Timepoint","Treatment","Control","HR","LowerCI","UpperCI","SurvT","SurvC","Et","Nt","Ec","Nc","O/F"])
    for row in longr: c.append(row)
    pvp = os.path.join(workdir, "outcomes_provenance.xlsx"); pv.save(pvp)
    print(f"[provenance] {pvp}  (prov={len(prov)}, flags/changes={len(flags)}, long={len(longr)})")
    print("MISSING RESULTS:" if missing else "All rows matched a result.")
    for m in missing: print("   ", m)

if __name__ == "__main__":
    main()
