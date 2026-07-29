#!/usr/bin/env python3
"""QC filled outcome tables — all three families (pwma, nma, pwma_subgroup).

Usage:
  python qc.py <filled.xlsx> [<filled.xlsx> ...]

Checks per file:
  - the header resolves to a known family and every expected role is present
  - the sheet has the expected number of columns for that family (pwma 25 / nma 24 / subgroup 27)
  - no empty data cell (every field filled, "NA" where unreported)
  - NA fill-rate per column
  - effect sanity: lower <= TE <= upper (TE = "TE" in pwma, "Measure" in nma)
  - a CI with no point estimate (almost always a survival-RATE CI mis-placed into the effect CI cells)
  - *** EVENTS > DENOMINATOR *** — the Ec/Et guard, see below
  - subgroup sheets: "Extraction Possible" answered, no duplicate (study, comparison, subgroup) rows,
    and no row that says extraction is impossible while still carrying an effect estimate

*** THE Ec/Et GUARD (the reason this check exists) ***
`Et` means opposite things in the two pairwise/network layouts:
    pwma / pwma_subgroup : Et = EVENTS in treatment, Nt = N in treatment,
                           Ec = EVENTS in control,   Nc = N in control
    nma                  : Ec T1 = EVENT COUNT in T1, Et T1 = EVENT TOTAL (participants) in T1
                           Ec T2 / Et T2 likewise for the comparator
So an extractor who carries the PWMA convention into an NMA sheet writes the participant total where
the event count belongs and vice versa. The output still looks plausible and NOTHING downstream
catches it. The one arithmetic fact that always breaks is events > denominator, so this script flags
any row where the event count exceeds its own arm's N, per family, and says which two columns to swap.
"""
import sys, os, collections, openpyxl
from openpyxl.utils import get_column_letter as L

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import families as F

NO_TOKENS = {"no", "n", "false", "0", "not possible", "not extractable"}


def qc(path):
    wb = openpyxl.load_workbook(path, data_only=True); ws = F.sheet_of(wb)
    lay = F.Layout(ws)
    print(f"\n=== {path}")
    print(f"    {lay.describe()}")
    print(f"    counts: {F.COUNT_COLS_HELP[lay.family]}")
    if lay.missing_roles():
        print(f"  ERROR: header did not resolve roles {sorted(lay.missing_roles())}")
    if ws.max_column != lay.expected_cols():
        print(f"  WARNING: expected {lay.expected_cols()} columns for family {lay.family}, "
              f"got {ws.max_column}")

    empties, na_count, hr_issues, ci_no_te = [], {}, [], []
    count_issues, ep_missing, ep_contradiction, dup = [], [], [], []
    seen = collections.Counter()
    nrows = 0

    for r in range(4, ws.max_row + 1):
        pid, comp, sub = lay.key(r)
        if pid is None: continue
        nrows += 1
        tag = f"row{r} pid={pid} comp={comp!r}" + (f" sub={sub!r}" if sub else "")
        seen[(pid, F.clean(comp).lower(), F.clean(sub).lower())] += 1

        for c in range(lay.data_first_col, lay.data_last_col + 1):
            v = ws.cell(row=r, column=c).value
            col = L(c)
            if v is None or str(v).strip() == "":
                empties.append((r, col, pid))
            elif F.is_missing(v):
                na_count[col] = na_count.get(col, 0) + 1

        cell = lambda role: ws.cell(row=r, column=lay.col(role)).value if lay.col(role) else None
        te, lo, up = F.num(cell("te")), F.num(cell("lower_ci")), F.num(cell("upper_ci"))
        if None not in (te, lo, up) and not (lo <= te <= up):
            hr_issues.append((tag, lo, te, up))
        # a reported CI always implies a point estimate; a CI with no TE is a mis-filed RATE CI
        if te is None and (lo is not None or up is not None):
            ci_no_te.append((tag, lo, up))

        # --- events vs denominator, per arm ---
        for ev_role, n_role, arm in (("events_t", "n_t", "treatment/T1"), ("events_c", "n_c", "control/T2")):
            ev, n = F.num(cell(ev_role)), F.num(cell(n_role))
            if ev is None or n is None: continue
            if ev > n:
                ecol, ncol = L(lay.col(ev_role)), L(lay.col(n_role))
                hint = (f"swap {ecol}<->{ncol} — looks like the pwma Et/Ec convention was carried into "
                        f"an nma sheet" if lay.family == "nma" else
                        f"swap {ecol}<->{ncol} — looks like the nma Ec/Et convention was carried into "
                        f"a pwma sheet")
                count_issues.append((tag, arm, f"{lay.labels.get(ev_role)}={ev:g} > "
                                                f"{lay.labels.get(n_role)}={n:g}", hint))

        # --- subgroup-sheet specific ---
        if lay.col_extraction_possible:
            ep = F.clean(ws.cell(row=r, column=lay.col_extraction_possible).value)
            if not ep or F.is_missing(ep):
                ep_missing.append(tag)
            elif ep.lower() in NO_TOKENS and te is not None:
                ep_contradiction.append((tag, ep, te))
            if not F.clean(sub):
                dup.append((tag, "blank subgroup label"))

    for key, n in seen.items():
        if n > 1:
            dup.append((f"pid={key[0]} comp={key[1]!r} sub={key[2]!r}", f"{n} duplicate rows"))

    print(f"  data rows: {nrows}")
    print(f"  EMPTY cells (should be 0): {len(empties)}", empties[:10] if empties else "")
    print(f"  missing/NA per column: " + ", ".join(f"{k}:{v}" for k, v in sorted(na_count.items())))
    print(f"  effect sanity violations (need lower<=TE<=upper): {len(hr_issues)}", hr_issues or "")
    print(f"  CI-without-TE (likely mis-placed rate CI): {len(ci_no_te)}", ci_no_te or "")
    print(f"  *** EVENTS > DENOMINATOR: {len(count_issues)} ***")
    for tag, arm, detail, hint in count_issues:
        print(f"      {tag}  [{arm}]  {detail}\n         -> {hint}")
    if lay.col_extraction_possible:
        print(f"  'Extraction Possible' unanswered: {len(ep_missing)}", ep_missing[:10] or "")
        print(f"  'Extraction Possible'=no but an effect estimate is present: {len(ep_contradiction)}",
              ep_contradiction or "")
    print(f"  duplicate / unlabelled row keys: {len(dup)}", dup or "")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python qc.py <filled.xlsx> [<filled.xlsx> ...]")
    for p in sys.argv[1:]:
        qc(p)
    print("\nQC done.")
