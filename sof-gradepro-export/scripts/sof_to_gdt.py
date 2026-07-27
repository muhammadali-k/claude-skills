#!/usr/bin/env python3
"""Convert per-outcome Summary-of-Findings Excel exports into one combined
GRADEpro-GDT-format JSON-LD file for MAGICapp's Evidence tab -> "Add PICO" ->
"Import PICO using a GDT Gradepro file" beta feature.

Usage:
    python3 sof_to_gdt.py <xlsx-file-or-folder> \
        --population "..." --intervention "..." --comparator "..." \
        [--title "..."] [--sof-title "..."] [--outcome-name "..."] \
        [--mid-small PCT] [--mid-moderate PCT] [--mid-large PCT] [--no-pls] \
        -o <output.json>

Input is either ONE outcome's .xlsx (single sheet "Summary of Findings", headers in
rows 1-2, one data record starting row 3, citations one-per-row overflowing into
extra rows below) or a FOLDER of many such files -- one outcome per file, combined
into a single PICO/question with one evidenceSummary entry per outcome, in the
order files are found (sorted by filename).

Output:
    <output.json>                                combined GDT JSON-LD, one PICO
    <output-stem>_plain_language_summaries.md     one section per outcome, for
                                                   pasting into MAGICapp's per-outcome
                                                   "Plain language summary" field by
                                                   hand (see LIMITATIONS below)

Non-obvious rules / documented limitations (see also the skill's SKILL.md):
  - Relative-effect prefix (HR/RR/OR/...) is parsed with a generic regex, not
    hardcoded to "HR" -- unrecognized prefixes still convert, using the literal
    prefix text as the relativeEffect @type, with a printed warning.
  - Risk-difference sign ("fewer"/"more") sets the absoluteEffect value's sign.
  - controlRisk.value = the control arm's "X per 1000" figure / 10 (GDT stores
    control risk per 100, confirmed against a real GDT export).
  - absoluteEffect.confidenceIntervalFrom/To are always left null: the source
    Excel gives no CI on the risk-difference cell itself, so there is nothing
    honest to compute -- inventing symmetric bounds would be a fabrication.
  - patientGroup totalCount (N per arm) is always left null: not present anywhere
    in the source Excel.
  - studyDesign is always the generic {"RandomisedTrials","randomised trials"}
    default -- the source Excel does not state study design.
  - quality domain sub-ratings (riskOfBias/inconsistency/indirectness/imprecision)
    are always null: the source Excel gives only the single overall "Overall: X"
    rating, no domain breakdown.
  - controlRisk's @type label (Low/Moderate/HighControlRisk) is cosmetic/arbitrary
    in GDT's own schema -- this script always emits "LowControlRisk" and does not
    try to infer a meaningful band from the control rate.
  - Plain-language summaries are generated deterministically (GRADE Table 15.6.b /
    Cochrane Handbook Ch.15 conventions -- certainty-keyed verb choice + magnitude
    classification, including the CI-crosses-null special cases) and are (a) best-
    effort embedded into the output JSON-LD's explanation[] array, one item per
    outcome with a non-standard "forOutcome" cross-reference (there is no confirmed
    native per-outcome slot in this JSON-LD schema for this content, and MAGICapp's
    own help docs confirm the GDT importer does not import plain-language text even
    when present), and (b) ALWAYS also written to the companion .md file, which is
    the reliable path -- paste those sentences into each outcome's "Plain language
    summary" field in MAGICapp by hand after import.
  - Magnitude bands (trivial/small/moderate/large) default to a generic relative
    risk/hazard-reduction heuristic (<5% / 5-20% / 20-40% / >40%), because GRADE
    does not define a universal numeric cutoff -- a real minimally-important-
    difference (MID) is outcome-specific and should be supplied by the review
    panel. Override the default bands with --mid-small/--mid-moderate/--mid-large
    if you have real MID-derived boundaries; there is no per-outcome override in
    this CLI (all outcomes in one run share the same bands) -- a documented
    limitation, not an oversight.
"""
import argparse, json, os, re, glob, sys, uuid, datetime

# ---------------------------------------------------------------------------
# GRADE plain-language templates (Cochrane Handbook Table 15.6.b)
# ---------------------------------------------------------------------------
CERTAINTY_LABEL = {"high": "high", "moderate": "moderate", "low": "low", "very_low": "very low"}

TEMPLATES = {
    "high":     {"large": "{I} results in a large {dirnoun} in {O}",
                 "moderate": "{I} {dirverb} {O}",
                 "small": "{I} {dirverb} {O} slightly",
                 "trivial": "{I} results in little to no difference in {O}"},
    "moderate": {"large": "{I} probably results in a large {dirnoun} in {O}",
                 "moderate": "{I} probably {dirverb} {O}",
                 "small": "{I} probably {dirverb} {O} slightly",
                 "trivial": "{I} probably results in little to no difference in {O}"},
    "low":      {"large": "{I} may result in a large {dirnoun} in {O}",
                 "moderate": "{I} may {dirverb} {O}",
                 "small": "{I} may {dirverb} {O} slightly",
                 "trivial": "{I} may result in little to no difference in {O}"},
}

MEASURE_TYPE_MAP = {"HR": "HazardRatio", "RR": "RiskRatio", "OR": "OddsRatio"}


def numify(s):
    """'420' -> 420 (int); '0.72' -> 0.72 (float)."""
    v = float(s)
    return int(v) if v == int(v) else v


def is_number(s):
    try:
        float(s); return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Excel parsing
# ---------------------------------------------------------------------------
def build_colmap(ws, path):
    """Locate columns by header ROLE (row1 keyword match), not hardcoded letter --
    survives column reordering between exports."""
    row1 = {c: str(ws.cell(row=1, column=c).value or "") for c in range(1, ws.max_column + 1)}

    def find(keyword):
        for c, v in row1.items():
            if keyword.lower() in v.lower():
                return c
        return None

    cols = {"outcomes": find("outcome"), "relative": find("relative"),
            "absolute": find("absolute"), "certainty": find("certainty"),
            "citations": find("citation")}
    missing = [k for k, v in cols.items() if v is None]
    if missing:
        raise SystemExit(f"{path}: could not find header column(s) for {missing} in row 1 "
                          f"(found: {row1}) -- unexpected Summary-of-Findings layout.")

    a = cols["absolute"]
    intervention_col, control_col, riskdiff_col = a, a + 1, a + 2
    row2 = {c: str(ws.cell(row=2, column=c).value or "") for c in range(a, min(a + 4, ws.max_column + 1))}
    for c, v in row2.items():
        lv = v.lower()
        if "intervention" in lv: intervention_col = c
        elif "control" in lv: control_col = c
        elif "difference" in lv: riskdiff_col = c

    return {"outcomes": cols["outcomes"], "relative": cols["relative"],
            "intervention": intervention_col, "control": control_col, "riskdiff": riskdiff_col,
            "certainty": cols["certainty"], "citations": cols["citations"]}


def find_data_start_row(ws):
    """Merged-header detection: header block is however many rows the row-1 merges span."""
    hr = 1
    for m in ws.merged_cells.ranges:
        if m.min_row == 1:
            hr = max(hr, m.max_row)
    return hr + 1


def parse_excel_outcome(path):
    """Parse one outcome .xlsx -> dict of raw + derived fields. Raises SystemExit with
    an actionable message on any layout it doesn't recognize."""
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["Summary of Findings"] if "Summary of Findings" in wb.sheetnames else wb.active

    colmap = build_colmap(ws, path)
    r0 = find_data_start_row(ws)
    if ws.cell(row=r0, column=colmap["outcomes"]).value is None:
        raise SystemExit(f"{path}: no data row found at row {r0} (below the detected header block).")

    def cell(col_key, row=r0):
        v = ws.cell(row=row, column=colmap[col_key]).value
        return "" if v is None else str(v).strip()

    # --- A: stratum label + stated citation count ---
    a_text = cell("outcomes")
    lines = [l.strip() for l in a_text.split("\n") if l.strip()]
    stated_n_citations = None
    if lines and re.match(r"^\d+\s+citations?$", lines[-1], re.I):
        stated_n_citations = int(re.match(r"^(\d+)", lines[-1]).group(1))
        lines = lines[:-1]
    stratum = " ".join(lines)

    # --- B: relative effect "PREFIX value\n(lo to hi)" ---
    b_text = cell("relative")
    m_point = re.search(r"([A-Za-z]{2,4})\s*([\d.]+)", b_text)
    if not m_point:
        raise SystemExit(f"{path}: could not parse relative-effect cell {b_text!r} "
                          f"(expected e.g. 'HR 0.72').")
    prefix, point = m_point.group(1).upper(), numify(m_point.group(2))
    m_ci = re.search(r"([\d.]+)\s*to\s*([\d.]+)", b_text, re.I) or \
           re.search(r"\(\s*([\d.]+)\s*[-–—]\s*([\d.]+)\s*\)", b_text)
    if not m_ci:
        raise SystemExit(f"{path}: could not parse the CI in relative-effect cell {b_text!r} "
                          f"(expected e.g. '(0.55 to 0.95)').")
    ci_lo, ci_hi = numify(m_ci.group(1)), numify(m_ci.group(2))
    if prefix not in MEASURE_TYPE_MAP:
        print(f"WARNING: {path}: unrecognized relative-effect prefix {prefix!r} "
              f"(expected HR/RR/OR) -- using it literally as the relativeEffect @type.",
              file=sys.stderr)

    # --- C/D: arm absolute rates "N per 1000" ---
    def per1000(col_key):
        t = cell(col_key)
        m = re.search(r"([\d.]+)\s*per\s*1000", t, re.I)
        if not m:
            raise SystemExit(f"{path}: could not parse absolute-rate cell {t!r} (expected 'N per 1000').")
        return numify(m.group(1))

    intervention_rate = per1000("intervention")
    control_rate = per1000("control")

    # --- E: signed risk difference "N fewer/more per 1000" ---
    e_text = cell("riskdiff")
    m_rd = re.search(r"([\d.]+)\s*(fewer|less|more)\s*per\s*1000", e_text, re.I)
    if not m_rd:
        raise SystemExit(f"{path}: could not parse risk-difference cell {e_text!r} "
                          f"(expected e.g. '80 fewer per 1000').")
    rd_value = numify(m_rd.group(1))
    rd_signed = -rd_value if m_rd.group(2).lower() in ("fewer", "less") else rd_value

    # --- F: "Overall: <level>" certainty ---
    f_text = cell("certainty")
    m_cert = re.search(r"overall:?\s*(.+)", f_text, re.I)
    if not m_cert:
        raise SystemExit(f"{path}: could not parse certainty cell {f_text!r} (expected 'Overall: Moderate').")
    certainty_display = m_cert.group(1).strip().upper()          # e.g. "MODERATE", "VERY LOW"
    certainty_key = m_cert.group(1).strip().lower().replace(" ", "_")  # e.g. "moderate", "very_low"
    if certainty_key not in ("high", "moderate", "low", "very_low"):
        raise SystemExit(f"{path}: unrecognized certainty level {m_cert.group(1)!r} "
                          f"(expected High/Moderate/Low/Very low).")

    # --- G: citations, one per row from r0 downward ---
    citations = []
    for r in range(r0, ws.max_row + 1):
        v = ws.cell(row=r, column=colmap["citations"]).value
        if v is not None and str(v).strip():
            citations.append(str(v).strip())
    if stated_n_citations is not None and len(citations) != stated_n_citations:
        print(f"WARNING: {path}: outcome cell states {stated_n_citations} citations "
              f"but {len(citations)} citation row(s) were found -- using the found count.",
              file=sys.stderr)
    n_studies = len(citations) or stated_n_citations

    return {
        "path": path, "stratum": stratum, "prefix": prefix, "point": point,
        "ci_lo": ci_lo, "ci_hi": ci_hi, "intervention_rate": intervention_rate,
        "control_rate": control_rate, "rd_signed": rd_signed, "rd_text": e_text,
        "certainty_display": certainty_display, "certainty_key": certainty_key,
        "citations": citations, "n_studies": n_studies,
    }


def derive_outcome_name(path):
    """Filename -> display name: strip trailing _YYYYMMDD_HHMM, underscores -> spaces.
    'OS_(DrugX_vs_Placebo)_Overall_20260101_0900.xlsx' ->
    'OS (DrugX vs Placebo) Overall'."""
    stem = os.path.splitext(os.path.basename(path))[0]
    stem = re.sub(r"_\d{8}_\d{4}$", "", stem)
    return stem.replace("_", " ").strip()


def short_outcome_label(display_name):
    """For plain-language sentences: the leading metric token before any '(' --
    e.g. 'OS (DrugX vs Placebo) Overall' -> 'OS'. The source data never gives a
    spelled-out outcome name (see module docstring), so sentences necessarily use
    whatever abbreviation is in the filename."""
    return display_name.split("(")[0].strip() or display_name


# ---------------------------------------------------------------------------
# GRADE plain-language summary generation (deterministic, no LLM)
# ---------------------------------------------------------------------------
def classify_effect_magnitude(value, null, thresholds):
    """value = a point on the ratio scale (point estimate or a CI bound); null = 1.0
    for HR/RR/OR. Returns (magnitude, direction) where direction is 'reduction' or
    'increase' and magnitude in trivial/small/moderate/large, classified against the
    RELATIVE % change from null -- see module docstring re: MID vs. this default."""
    pct = (null - value) / null * 100.0   # positive = reduction, negative = increase
    direction = "reduction" if pct >= 0 else "increase"
    ap = abs(pct)
    t_small, t_mod, t_large = thresholds
    if ap < t_small: magnitude = "trivial"
    elif ap < t_mod: magnitude = "small"
    elif ap < t_large: magnitude = "moderate"
    else: magnitude = "large"
    return magnitude, direction


def crosses_null(ci_lo, ci_hi, null=1.0):
    return (ci_lo - null) * (ci_hi - null) < 0


def render_cell(certainty_key, magnitude, direction, intervention, outcome):
    dirverb = "reduces" if direction == "reduction" else "increases"
    dirnoun = "reduction" if direction == "reduction" else "increase"
    sentence = TEMPLATES[certainty_key][magnitude].format(I=intervention, O=outcome,
                                                            dirverb=dirverb, dirnoun=dirnoun)
    return sentence[0].upper() + sentence[1:]


def generate_plain_language_summary(intervention, outcome_display, parsed, thresholds=(5, 20, 40)):
    """Returns (sentence: str, flagged: bool) per GRADE Table 15.6.b / Cochrane Handbook
    Ch.15 conventions, including the CI-crosses-null special cases (Handbook Sec 15.6.4)."""
    out = short_outcome_label(outcome_display)
    I, cert = intervention, parsed["certainty_key"]
    label = CERTAINTY_LABEL[cert]
    prefix, point, lo, hi = parsed["prefix"], parsed["point"], parsed["ci_lo"], parsed["ci_hi"]
    rd_text = parsed["rd_text"]
    stats_ci = f"{prefix} {point}, 95% CI {lo} to {hi}"

    if cert == "very_low":
        sentence = f"The evidence is very uncertain about the effect of {I} on {out}"
        return f"{sentence} ({stats_ci}; {label}-certainty evidence).", False

    if not crosses_null(lo, hi):
        magnitude, direction = classify_effect_magnitude(point, 1.0, thresholds)
        sentence = render_cell(cert, magnitude, direction, I, out)
        return f"{sentence} ({stats_ci}; {rd_text}; {label}-certainty evidence).", False

    lo_mag, lo_dir = classify_effect_magnitude(lo, 1.0, thresholds)
    hi_mag, hi_dir = classify_effect_magnitude(hi, 1.0, thresholds)

    if lo_mag == "trivial" and hi_mag == "trivial":
        sentence = render_cell(cert, "trivial", "reduction", I, out)
        return f"{sentence} ({stats_ci}; {rd_text}; {label}-certainty evidence).", False

    if lo_mag == "trivial" or hi_mag == "trivial":
        important_dir = hi_dir if lo_mag == "trivial" else lo_dir
        important_verb = "reduce" if important_dir == "reduction" else "increase"
        base = render_cell(cert, "trivial", "reduction", I, out)
        sentence = f"{base}, but may {important_verb} {out}"
        return f"{sentence} ({stats_ci}; {rd_text}; {label}-certainty evidence).", False

    # both bounds important, opposite directions -> direction genuinely undetermined
    point_dir = "reduction" if point <= 1 else "increase"
    point_verb = "reduce" if point_dir == "reduction" else "increase"
    opp_verb = "increase" if point_dir == "reduction" else "reduce"
    sentence = (f"{I} may {point_verb} {out}, but it may also {opp_verb} it — the evidence "
                f"does not allow a clear conclusion about the direction of the effect")
    stats = (f"{stats_ci}; approximately {rd_text} at the point estimate, but the interval is "
             f"compatible with either a large reduction or an increase in events; "
             f"{label}-certainty evidence")
    return f"{sentence} ({stats}).", True


# ---------------------------------------------------------------------------
# JSON-LD assembly
# ---------------------------------------------------------------------------
GDT_CONTEXT = [
    {"@base": "http://dbep.gradepro.org/", "@vocab": "http://dbep.gradepro.org/schema/",
     "@language": "en", "schema": "http://schema.org/",
     "cochrane": "http://linkeddata.cochrane.org/ontologies/pico/",
     "xsd": "http://www.w3.org/2001/XMLSchema#", "version": "schema:version", "name": "schema:name",
     "sameAs": "schema:sameAs",
     "publicationTime": {"@id": "schema:datePublished", "@type": "xsd:dateTime"},
     "modificationTime": {"@id": "schema:dateModified", "@type": "xsd:dateTime"},
     "author": {"@id": "schema:author", "@container": "@list"},
     "footnote": {"@container": "@list"}, "code": "schema:code", "codeValue": "schema:codeValue",
     "codingSystem": "schema:codingSystem", "unitCode": "schema:unitCode", "unitText": "schema:unitText",
     "value": "schema:value", "text": "schema:value", "lowerBound": "schema:minValue",
     "upperBound": "schema:maxValue", "Person": "schema:Person", "MedicalCode": "schema:MedicalCode",
     "MedicalSymptom": "schema:MedicalSymptom", "MedicalCondition": "schema:MedicalCondition",
     "QuantitativeValue": "schema:QuantitativeValue"},
    {"PICO": "cochrane:PICO", "healthProblemOrPopulation": "cochrane:population",
     "condition": "cochrane:condition", "intervention": "cochrane:intervention",
     "comparison": "cochrane:comparison", "outcome": {"@id": "cochrane:outcome", "@container": "@list"}},
    {"title": "name", "sofTitle": "alternateName",
     "evidenceSummary": {"@container": "@list"}, "patientGroup": {"@container": "@list"}},
]


def build_outcome_entry(outcome_id, display_name):
    return {"@id": outcome_id, "@type": ["Outcome", "TimeToEvent"],
            "name": {"value": display_name}, "event": {"@type": "Event"}}


def build_evidence_summary_entry(outcome_id, parsed):
    measure_type = MEASURE_TYPE_MAP.get(parsed["prefix"], parsed["prefix"])
    return {
        "@type": "DichotomousData",
        "forOutcome": {"@id": outcome_id},
        "studyDesign": {"@type": "RandomisedTrials", "name": "randomised trials"},
        "numberOfStudies": {"value": parsed["n_studies"]},
        "patientGroup": [
            {"@type": "InterventionGroup", "totalCount": {"value": None}},
            {"@type": "ControlGroup", "totalCount": {"value": None}},
        ],
        "measuredWith": {"@type": "OutcomeMeasure", "name": ""},
        "effectSummary": {
            "@type": "Pooled",
            "relativeEffect": {"@type": measure_type, "value": {"value": parsed["point"]},
                                "confidenceLevel": {"value": 0.95},
                                "confidenceIntervalFrom": parsed["ci_lo"],
                                "confidenceIntervalTo": parsed["ci_hi"]},
            "absoluteEffect": [{
                "@type": "AutoCalculatedAbsoluteEffect", "forControlRisk": {"@id": "_:cr1"},
                "value": {"value": parsed["rd_signed"]}, "confidenceLevel": {"value": 0.95},
                "confidenceIntervalFrom": None, "confidenceIntervalTo": None, "denominator": 1000,
            }],
        },
        "quality": {"@type": "GradeQuality", "value": None, "name": parsed["certainty_display"],
                     "riskOfBias": None, "inconsistency": None, "indirectness": None, "imprecision": None,
                     "otherConsiderations": {"name": "", "publicationBias": None,
                        "doseResponseGradient": {"@type": "NoChange", "name": "no"},
                        "plausibleConfounding": {"@type": "NoChange", "name": "no"},
                        "largeEffect": {"@type": "NoChange", "name": "no"}}},
        "controlRisk": [{"@id": "_:cr1", "@type": "LowControlRisk",
                          "value": round(parsed["control_rate"] / 10.0, 4)}],
    }


def assemble_jsonld(outcomes, population, intervention, comparator, title, sof_title):
    pico_id = str(uuid.uuid4())
    question_outcomes, evidence_summaries, explanations = [], [], [
        {"@type": "Explanation", "@id": "_:e0", "text": "no_explanation_provided"},
    ]
    for i, (display_name, parsed, pls_text) in enumerate(outcomes):
        outcome_id = f"outcomes/{uuid.uuid4()}"
        question_outcomes.append(build_outcome_entry(outcome_id, display_name))
        evidence_summaries.append(build_evidence_summary_entry(outcome_id, parsed))
        if pls_text is not None:
            explanations.append({"@type": "Explanation", "@id": f"_:pls{i}", "text": pls_text,
                                  "forOutcome": {"@id": outcome_id}})

    default_title = f"Should {intervention} vs. {comparator} be used for {population}?"
    default_sof_title = f"{intervention} vs. {comparator} for {population}"

    return {
        "@id": pico_id,
        "@context": GDT_CONTEXT,
        "@type": "ManagementEvidenceProfile",
        "version": "1",
        "modificationTime": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "bibliography": {"value": ""},
        "title": title or default_title,
        "sofTitle": sof_title or default_sof_title,
        "question": {
            "@id": f"questions/{pico_id}", "@type": "PICO",
            "healthProblemOrPopulation": {"@type": "HealthProblemOrPopulation",
                                           "name": {"value": population}, "setting": {"value": ""}},
            "intervention": {"name": intervention, "@type": "Intervention"},
            "comparison": {"name": comparator, "@type": "Comparison"},
            "outcome": question_outcomes,
        },
        "explanation": explanations,
        "evidenceSummary": evidence_summaries,
        "reference": [],
    }


def write_plain_language_md(path, intervention, comparator, population, rows, flagged_count):
    with open(path, "w") as f:
        f.write(f"# Plain-language summaries: {intervention} vs. {comparator}\n\n")
        f.write(f"Population: {population}\n\n")
        f.write("Generated deterministically from GRADE Table 15.6.b / Cochrane Handbook Ch.15 "
                "conventions (see the skill's SKILL.md and references/ for the exact rules). "
                "MAGICapp's GDT importer does not import plain-language text (confirmed in "
                "MAGICapp's own help docs) -- paste each sentence below into that outcome's "
                "\"Plain language summary\" field in MAGICapp by hand after import.\n\n")
        if flagged_count:
            f.write(f"**{flagged_count} outcome(s) below are flagged `[NEEDS HUMAN REVIEW]`** -- "
                    "their confidence interval crosses the null with an important effect plausible "
                    "in BOTH directions, so GRADE's own convention is to state direction is "
                    "undetermined rather than default to the point estimate. Review before using.\n\n")
        f.write("---\n\n")
        for display_name, sentence, flagged in rows:
            tag = " `[NEEDS HUMAN REVIEW]`" if flagged else ""
            f.write(f"## {display_name}{tag}\n\n{sentence}\n\n")


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="one outcome's .xlsx, or a folder of many (one outcome each)")
    ap.add_argument("--population", required=True)
    ap.add_argument("--intervention", required=True)
    ap.add_argument("--comparator", required=True)
    ap.add_argument("--title", default=None)
    ap.add_argument("--sof-title", default=None)
    ap.add_argument("--outcome-name", default=None,
                     help="override the filename-derived outcome name (single-file input only)")
    ap.add_argument("--mid-small", type=float, default=5.0,
                     help="trivial/small relative-%% boundary (default 5, non-authoritative default -- see docstring)")
    ap.add_argument("--mid-moderate", type=float, default=20.0, help="small/moderate boundary (default 20)")
    ap.add_argument("--mid-large", type=float, default=40.0, help="moderate/large boundary (default 40)")
    ap.add_argument("--no-pls", action="store_true", help="skip plain-language summary generation")
    ap.add_argument("-o", "--output", required=True, help="output .json path")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        ap.error(f"input path not found: {args.input}")

    if os.path.isdir(args.input):
        if args.outcome_name:
            ap.error("--outcome-name only applies to single-file input, not a folder")
        paths = sorted(p for p in glob.glob(os.path.join(args.input, "*.xlsx"))
                        if not os.path.basename(p).startswith(("~$", ".")))
        if not paths:
            ap.error(f"no .xlsx files found in folder: {args.input}")
    else:
        paths = [args.input]

    thresholds = (args.mid_small, args.mid_moderate, args.mid_large)
    outcomes, pls_rows, flagged_count = [], [], 0
    for path in paths:
        parsed = parse_excel_outcome(path)
        display_name = args.outcome_name if (args.outcome_name and len(paths) == 1) else derive_outcome_name(path)
        pls_text, flagged = (None, False)
        if not args.no_pls:
            pls_text, flagged = generate_plain_language_summary(args.intervention, display_name, parsed, thresholds)
            if flagged:
                flagged_count += 1
            pls_rows.append((display_name, pls_text, flagged))
        outcomes.append((display_name, parsed, pls_text))

    doc = assemble_jsonld(outcomes, args.population, args.intervention, args.comparator,
                           args.title, args.sof_title)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(doc, f, indent=1)

    print(f"Wrote {args.output} ({len(outcomes)} outcome(s), {len(paths)} source file(s)).")

    if not args.no_pls:
        pls_path = os.path.splitext(args.output)[0] + "_plain_language_summaries.md"
        write_plain_language_md(pls_path, args.intervention, args.comparator, args.population,
                                 pls_rows, flagged_count)
        print(f"Wrote {pls_path}.")
        if flagged_count:
            print(f"  {flagged_count} outcome(s) flagged NEEDS HUMAN REVIEW (CI crosses null with "
                  f"important effect plausible either direction) -- see the .md file.")

    print("Reminder: this is a beta MAGICapp import path. After importing, manually check per the "
          "documented limitations in SKILL.md -- patientGroup N per arm, absolute-effect CI bounds, "
          "study design, GRADE domain sub-ratings, and the plain-language summary field are all "
          "either null/default here or not imported by MAGICapp's GDT importer.")


if __name__ == "__main__":
    main()
