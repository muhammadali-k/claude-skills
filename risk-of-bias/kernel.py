"""
Risk-of-bias assessment engine (RoB 2 + ROBINS-I).

This kernel plugin provides the *deterministic, rule-based* half of a risk-of-bias
assessment: it turns per-domain signalling-question answers into domain-level
judgements and an overall judgement, following the official Cochrane algorithms
that are bundled with this skill (assets/rob2_tool.json, assets/robins_i_tool.json,
assets/RoB2_cribsheet_parallel_trial.pdf, assets/robins_i_reference.md).

The *reading* half — extracting signalling-question answers from a trial
publication — is done by the agent following SKILL.md, which produces an answer
object with a supporting quote for each answer. That answer object is the input
to `assess_rob2()` / `assess_robins_i()` here.

Design split (matches the user's assessor + verifier workflow):
  reader (LLM)  ->  answers + quotes
  kernel (rules) -> domain judgements + overall judgement   [reproducible, auditable]
  plots (robvis-style) -> traffic-light + weighted summary

Public API
----------
  normalize_answer(x) / normalize_judgement(x)
  rob2_domain_judgement(domain, answers, effect='assignment')
  rob2_overall(domain_judgements, high_if_multiple_some_concerns=False)
  robins_i_domain_judgement(domain, answers)          # suggested per ROBINS-I guidance
  robins_i_overall(domain_judgements)
  assess_rob2(answers_by_domain, effect='assignment', ...)
  assess_robins_i(answers_by_domain, ...)
  get_signalling_questions(tool, domain=None, effect='assignment')
  load_tool(tool)
  traffic_light_plot(data, tool='rob2', ...)
  weighted_bar_plot(data, tool='rob2', ...)
  results_to_traffic_light_df(results, tool='rob2')
"""
import os
import json

# ----------------------------------------------------------------------------- #
# Answer / judgement normalization
# ----------------------------------------------------------------------------- #
ROB_ANSWER_MAP = {
    "y": "Y", "yes": "Y", "Y": "Y",
    "py": "PY", "probably yes": "PY", "probablyyes": "PY", "prob yes": "PY", "PY": "PY",
    "pn": "PN", "probably no": "PN", "probablyno": "PN", "prob no": "PN", "PN": "PN",
    "n": "N", "no": "N", "N": "N",
    "ni": "NI", "no information": "NI", "no info": "NI", "noinformation": "NI",
    "unclear": "NI", "not reported": "NI", "nr": "NI", "NI": "NI",
    "na": "NA", "n/a": "NA", "not applicable": "NA", "notapplicable": "NA", "NA": "NA",
}
ROB_ANSWERS = ("Y", "PY", "PN", "N", "NI", "NA")

ROB_JUDGEMENT_MAP = {
    "low": "low", "low risk": "low", "low risk of bias": "low",
    "some concerns": "some concerns", "some concern": "some concerns", "moderate concerns": "some concerns",
    "high": "high", "high risk": "high", "high risk of bias": "high",
    "moderate": "moderate", "moderate risk": "moderate", "moderate risk of bias": "moderate",
    "serious": "serious", "serious risk": "serious", "serious risk of bias": "serious",
    "critical": "critical", "critical risk": "critical", "critical risk of bias": "critical",
    "no information": "no information", "no info": "no information", "ni": "no information",
    "no information on which to base a judgement": "no information",
}


def normalize_answer(x):
    """Map a signalling-question answer to canonical Y/PY/PN/N/NI/NA."""
    if x is None:
        return "NA"
    k = str(x).strip().lower()
    if k in ROB_ANSWER_MAP:
        return ROB_ANSWER_MAP[k]
    if x in ROB_ANSWERS:
        return x
    raise ValueError(
        "Unrecognized signalling-question answer %r. Use one of "
        "Y, PY, PN, N, NI, NA (or 'yes'/'probably yes'/'probably no'/'no'/"
        "'no information'/'not applicable')." % (x,)
    )


def normalize_judgement(x):
    """Map a domain/overall judgement to canonical lowercase label."""
    if x is None:
        raise ValueError("Judgement is None")
    k = str(x).strip().lower()
    if k in ROB_JUDGEMENT_MAP:
        return ROB_JUDGEMENT_MAP[k]
    raise ValueError("Unrecognized judgement %r." % (x,))


# convenience predicates over canonical answers
def rob_yes(a):   return a in ("Y", "PY")     # yes / probably yes
def rob_no(a):   return a in ("N", "PN")     # no / probably no
def rob_ni(a):  return a == "NI"            # no information
def rob_na(a):  return a == "NA"            # not applicable


def rob_getter(answers):
    """Return a getter g(key) -> canonical answer, defaulting unreached to NA."""
    def g(key):
        return normalize_answer(answers.get(key, "NA")) if answers.get(key) is not None else "NA"
    return g


def rob_judgement_values(domain_judgements):
    if isinstance(domain_judgements, dict):
        return list(domain_judgements.values())
    return list(domain_judgements)


# ----------------------------------------------------------------------------- #
# Bundled tool definitions (signalling questions, response options, rules)
# ----------------------------------------------------------------------------- #
def rob_asset_dir():
    import sys
    cands = []
    env = os.environ.get("ROB_SKILL_ASSETS")
    if env:
        cands.append(env)
    # sidecars don't get __file__, but each function's co_filename points at this
    # kernel.py on disk -> its sibling assets/ dir is the bundled tool sheets.
    try:
        here = os.path.dirname(sys._getframe().f_code.co_filename)
        if here:
            cands.append(os.path.join(here, "assets"))
    except Exception:
        pass
    try:
        cands.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"))
    except NameError:
        pass
    cands.append(os.path.join(os.getcwd(), "assets"))
    cands.append(os.path.join(os.getcwd(), "rob_skill", "assets"))
    for c in cands:
        if c and os.path.isdir(c):
            return c
    return cands[-1]


ROB_TOOL_FILES = {"rob2": "rob2_tool.json", "robins-i": "robins_i_tool.json", "robins_i": "robins_i_tool.json"}
ROB_TOOL_CACHE = {}


def load_tool(tool):
    """Load a bundled tool definition ('rob2' or 'robins-i') from assets/."""
    key = str(tool).strip().lower().replace(" ", "").replace("robins-i", "robins-i")
    if key in ("rob2", "rob-2", "rob 2"):
        key = "rob2"
    elif key in ("robinsi", "robins-i", "robins_i", "robins"):
        key = "robins-i"
    if key in ROB_TOOL_CACHE:
        return ROB_TOOL_CACHE[key]
    fn = ROB_TOOL_FILES.get(key)
    if fn is None:
        raise ValueError("Unknown tool %r; use 'rob2' or 'robins-i'." % (tool,))
    with open(os.path.join(rob_asset_dir(), fn)) as fh:
        data = json.load(fh)
    ROB_TOOL_CACHE[key] = data
    return data


def get_signalling_questions(tool, domain=None, effect="assignment"):
    """Return the signalling questions for the reader.

    tool: 'rob2' or 'robins-i'
    domain: e.g. 'D1'..'D5' (RoB2) or 'D1'..'D7' (ROBINS-I); None -> all domains
    effect: for RoB2 domain D2 only, 'assignment' or 'adhering'
    """
    t = load_tool(tool)
    dom = t["domains"]
    def _key(d):
        d = d.upper()
        if load_tool(tool)["tool"] == "RoB 2" and d == "D2":
            return "D2_adhering" if effect == "adhering" else "D2_assignment"
        return d
    if domain is not None:
        k = _key(domain)
        return {k: dom[k]}
    out = {}
    for k, v in dom.items():
        if k in ("D2_assignment", "D2_adhering"):
            if (effect == "adhering") != (k == "D2_adhering"):
                continue
        out[k] = v
    return out


# ============================================================================= #
# RoB 2 — deterministic domain algorithms (transcribed from the crib-sheet
# flowcharts, assets/RoB2_cribsheet_parallel_trial.pdf). Judgements:
# 'low' / 'some concerns' / 'high'.
# ============================================================================= #
def rob2_d1(answers):
    """Domain 1: bias arising from the randomization process (SQ 1.1-1.3)."""
    g = rob_getter(answers)
    concealed, random_, imbalance = g("1.2"), g("1.1"), g("1.3")
    if rob_yes(concealed):                                  # 1.2 concealed = Y/PY
        if rob_yes(random_) or rob_ni(random_):                # 1.1 random = Y/PY/NI
            return "some concerns" if rob_yes(imbalance) else "low"   # 1.3 Y/PY -> some
        return "some concerns"                         # 1.1 = N/PN
    if rob_ni(concealed):                                 # 1.2 = NI
        return "high" if rob_yes(imbalance) else "some concerns"      # 1.3 Y/PY -> high
    return "high"                                      # 1.2 = N/PN


def rob2_d2_assignment_part1(g):
    """Part 1 (SQ 2.1-2.5): bias from deviations arising because of trial context.

    Official RoB 2 (effect of *assignment*): awareness of assignment (2.1/2.2) matters
    only insofar as it led to deviations that arose because of the trial context (2.3).
    An open-label trial with NO such deviations is Low on this part — being unblinded is
    not itself a source of assignment-effect bias. Path:
      both 2.1,2.2 N/PN                      -> low
      2.3 N/PN  (aware, but no trial-context deviations)  -> low
      2.3 NI    (unknown whether deviations occurred)     -> some concerns
      2.3 Y/PY  -> 2.4 N/PN (did not affect outcome)      -> low
                  2.4 Y/PY/NI -> 2.5 Y/PY (balanced)      -> some concerns
                              -> 2.5 N/PN/NI (not/unknown)-> high
    """
    if rob_no(g("2.1")) and rob_no(g("2.2")):                  # not aware of assignment
        return "low"
    q23 = g("2.3")
    if rob_no(q23):                                       # aware, but no trial-context deviations
        return "low"
    if rob_ni(q23):                                       # unknown whether deviations occurred
        return "some concerns"
    if rob_no(g("2.4")):                                   # 2.3 Y/PY, deviations did not affect outcome
        return "low"
    if rob_yes(g("2.5")):                                   # 2.4 Y/PY/NI, deviations balanced between groups
        return "some concerns"
    return "high"                                      # 2.5 N/PN/NI


def rob2_d2_assignment_part2(g):
    """Part 2 (SQ 2.6-2.7): appropriate analysis to estimate effect of assignment."""
    if rob_yes(g("2.6")):                                   # 2.6 Y/PY
        return "low"
    if rob_no(g("2.7")):                                   # 2.6 N/PN/NI, 2.7 N/PN
        return "some concerns"
    return "high"                                      # 2.7 Y/PY/NI


def rob2_d2_assignment(answers):
    """Domain 2, effect of *assignment* to intervention (ITT). Combine Part1/Part2."""
    g = rob_getter(answers)
    p1 = rob2_d2_assignment_part1(g)
    p2 = rob2_d2_assignment_part2(g)
    if p1 == "high" or p2 == "high":
        return "high"
    if p1 == "some concerns" or p2 == "some concerns":
        return "some concerns"
    return "low"


def rob2_d2_adhering(answers):
    """Domain 2, effect of *adhering* to intervention (per-protocol) (SQ 2.1-2.6)."""
    g = rob_getter(answers)
    if rob_no(g("2.1")) and rob_no(g("2.2")):                  # both N/PN -> 2.4/2.5 node
        at_2425 = True
    else:
        q23 = g("2.3")
        at_2425 = rob_na(q23) or rob_yes(q23)                  # NA/Y/PY -> node ; N/PN/NI -> 2.6
    if at_2425:
        clean = lambda x: rob_na(x) or rob_no(x)              # NA/N/PN
        if clean(g("2.4")) and clean(g("2.5")):        # both NA/N/PN -> low
            return "low"
    # reached 2.6
    return "some concerns" if rob_yes(g("2.6")) else "high"  # Y/PY -> some ; N/PN/NI -> high


def rob2_d3(answers):
    """Domain 3: bias due to missing outcome data (SQ 3.1-3.4)."""
    g = rob_getter(answers)
    if rob_yes(g("3.1")):                                   # 3.1 Y/PY
        return "low"
    if rob_yes(g("3.2")):                                   # 3.2 Y/PY
        return "low"
    if rob_no(g("3.3")):                                   # 3.3 N/PN
        return "low"
    return "some concerns" if rob_no(g("3.4")) else "high"  # 3.4 N/PN -> some ; else high


def rob2_d4(answers):
    """Domain 4: bias in measurement of the outcome (SQ 4.1-4.5)."""
    g = rob_getter(answers)
    if rob_yes(g("4.1")):                                   # inappropriate method
        return "high"
    a2 = g("4.2")
    if rob_yes(a2):                                          # measurement differed between groups
        return "high"
    base = "low" if rob_no(a2) else "some concerns"        # 4.2 N/PN -> low base ; NI -> some base
    if rob_no(g("4.3")):                                   # assessors unaware
        return base
    if rob_no(g("4.4")):                                   # could not be influenced
        return base
    if rob_no(g("4.5")):                                   # not likely influenced
        return "some concerns"
    return "high"


def rob2_d5(answers):
    """Domain 5: bias in selection of the reported result (SQ 5.1-5.3)."""
    g = rob_getter(answers)
    q52, q53 = g("5.2"), g("5.3")
    if rob_yes(q52) or rob_yes(q53):                             # selected from multiple -> high
        return "high"
    if rob_no(q52) and rob_no(q53):                            # both N/PN
        return "low" if rob_yes(g("5.1")) else "some concerns"  # 5.1 Y/PY -> low ; else some
    return "some concerns"                             # at least one NI, none Y/PY


def rob2_domain_judgement(domain, answers, effect="assignment"):
    """Deterministic RoB 2 domain judgement.

    domain : 'D1'..'D5' (or '1'..'5')
    answers: {'1.1': 'Y', '1.2': 'PY', ...} signalling-question answers for that domain
    effect : 'assignment' (ITT) or 'adhering' (per-protocol) — only affects D2
    """
    d = str(domain).upper().replace("DOMAIN", "").strip()
    if not d.startswith("D"):
        d = "D" + d
    if d == "D2":
        return rob2_d2_adhering(answers) if effect == "adhering" else rob2_d2_assignment(answers)
    funcs = {"D1": rob2_d1, "D3": rob2_d3, "D4": rob2_d4, "D5": rob2_d5}
    fn = funcs.get(d)
    if fn is None:
        raise ValueError("Unknown RoB 2 domain %r (expected D1-D5)." % (domain,))
    return fn(answers)


def rob2_overall(domain_judgements, high_if_multiple_some_concerns=False):
    """RoB 2 overall judgement from domain judgements (assets: crib sheet 'Overall').

    low            : low for all domains
    some concerns  : some concerns in >=1 domain, but not high in any
    high           : high in >=1 domain, OR (optionally) some concerns for multiple
                     domains in a way that substantially lowers confidence (assessor sets
                     high_if_multiple_some_concerns=True to encode that judgement).
    """
    vals = [normalize_judgement(v) for v in rob_judgement_values(domain_judgements)]
    if "high" in vals:
        return "high"
    n_some = vals.count("some concerns")
    if n_some == 0:
        return "low"
    if high_if_multiple_some_concerns and n_some > 1:
        return "high"
    return "some concerns"


# ============================================================================= #
# ROBINS-I — domain-level judgements. Unlike RoB 2, ROBINS-I does not publish a
# strict per-domain flowchart: the domain judgement is *reached* by the assessor
# using the signalling questions and the Table 2 criteria. The functions below
# encode the tool's recommended mapping as a SUGGESTION (Low/Moderate/Serious/
# Critical/No information); the assessor's judgement is authoritative and can
# override it (mirroring the user's assessor + verifier workflow). Overall
# aggregation (worst-domain) IS deterministic and fully specified.
# ============================================================================= #
ROBINS_NI = "no information"


def robins_dom_confounding(g):
    if rob_no(g("1.1")):                                   # no potential for confounding
        return "low"
    if rob_ni(g("1.4")):
        return ROBINS_NI
    if rob_yes(g("1.6")):                                   # controlled for post-intervention vars
        return "serious"
    if rob_yes(g("1.4")):                                   # appropriate method for all important confounders
        if rob_no(g("1.5")):                               # but measured invalidly
            return "serious"
        if rob_ni(g("1.5")):
            return ROBINS_NI
        return "moderate"                              # sound NRSI, not comparable to RCT
    if rob_no(g("1.4")):                                   # did not control appropriately
        return "serious"
    return ROBINS_NI


def robins_dom_selection(g):
    if rob_no(g("2.1")) and rob_yes(g("2.4")):                  # no post-intervention selection; follow-up aligned
        return "low"
    if rob_ni(g("2.1")):
        return ROBINS_NI
    if rob_yes(g("2.1")):
        if rob_yes(g("2.5")):                               # adjustment corrected for selection bias
            return "moderate"
        if rob_yes(g("2.2")) and rob_yes(g("2.3")):              # selection related to intervention and outcome
            return "serious"
        return "moderate"
    if rob_no(g("2.4")):                                   # start of follow-up != start of intervention
        return "moderate" if rob_yes(g("2.5")) else "serious"
    return "low"


def robins_dom_classification(g):
    if rob_ni(g("3.1")) or rob_ni(g("3.3")):
        return ROBINS_NI
    if rob_yes(g("3.3")):                                   # classification affected by outcome knowledge
        return "serious"
    if rob_yes(g("3.1")) and rob_yes(g("3.2")):                  # groups clearly defined, recorded at start
        return "low"
    if rob_no(g("3.2")):                                   # not recorded at start of intervention
        return "moderate"
    return "moderate"


def robins_dom_deviations(g):
    if rob_no(g("4.1")):                                   # no deviations beyond usual practice
        return "low"
    if rob_ni(g("4.1")):
        return ROBINS_NI
    if rob_yes(g("4.2")):                                   # unbalanced deviations that affected outcome
        return "serious"
    if rob_ni(g("4.2")):
        return ROBINS_NI
    return "moderate"


def robins_dom_missing(g):
    if rob_yes(g("5.1")) and rob_no(g("5.2")) and rob_no(g("5.3")):  # data for nearly all; no exclusions
        return "low"
    if rob_ni(g("5.1")):
        return ROBINS_NI
    if rob_yes(g("5.5")) or rob_yes(g("5.4")):                   # robust to missing data / similar across arms
        return "moderate"
    if rob_no(g("5.4")):                                   # missingness differs across interventions
        return "serious"
    return "moderate"


def robins_dom_measurement(g):
    if rob_ni(g("6.1")) or rob_ni(g("6.3")):
        return ROBINS_NI
    if rob_no(g("6.3")):                                   # methods not comparable across groups
        return "serious"
    if rob_yes(g("6.4")):                                   # systematic errors related to intervention
        return "serious"
    if rob_no(g("6.1")) and rob_no(g("6.4")):                  # could not be influenced; no systematic error
        return "low"
    if rob_yes(g("6.1")) and rob_yes(g("6.2")):                  # could be influenced AND assessors aware
        return "serious"
    return "moderate"


def robins_dom_reported(g):
    ans = [g("7.1"), g("7.2"), g("7.3")]
    if any(rob_yes(a) for a in ans):                        # selected result from multiple options
        return "serious"
    if any(rob_ni(a) for a in ans):
        return ROBINS_NI
    if all(rob_no(a) for a in ans):
        return "low"
    return "moderate"


def robins_i_domain_judgement(domain, answers):
    """Suggested ROBINS-I domain judgement (Low/Moderate/Serious/Critical/No information).

    NOTE: this is the tool's *recommended* mapping, not a strict algorithm — ROBINS-I
    domain judgements require assessor expertise. Treat the return value as a suggestion
    to confirm or override. 'critical' is reserved for the assessor (a domain so
    problematic the study provides no useful evidence) and is not auto-assigned here.
    """
    d = str(domain).upper().replace("DOMAIN", "").strip()
    if not d.startswith("D"):
        d = "D" + d
    funcs = {"D1": robins_dom_confounding, "D2": robins_dom_selection,
             "D3": robins_dom_classification, "D4": robins_dom_deviations,
             "D5": robins_dom_missing, "D6": robins_dom_measurement,
             "D7": robins_dom_reported}
    fn = funcs.get(d)
    if fn is None:
        raise ValueError("Unknown ROBINS-I domain %r (expected D1-D7)." % (domain,))
    return fn(rob_getter(answers))


def robins_i_overall(domain_judgements):
    """ROBINS-I overall judgement — worst-domain rule (BMJ 2016 Table 2).

    Precedence: critical > serious > no information > moderate > low.
    """
    vals = [normalize_judgement(v) for v in rob_judgement_values(domain_judgements)]
    for level in ("critical", "serious", "no information", "moderate", "low"):
        if level in vals:
            return level
    return "low"


# ============================================================================= #
# Orchestration: answers -> domain judgements -> overall.
# Each domain input may be either a flat answers dict {'1.1':'Y', ...} or a rich
# dict {'answers': {...}, 'rationale': str, 'evidence': str, 'judgement': override}.
# 'judgement' (if present) is the assessor/verifier FINAL and overrides the rule
# suggestion, but the rule suggestion is always reported for auditability.
# ============================================================================= #
def rob_domain_input(v):
    if isinstance(v, dict) and "answers" in v and isinstance(v["answers"], dict):
        extra = {k: v[k] for k in v if k != "answers"}
        return v["answers"], extra
    return (v or {}), {}


def assess_rob2(answers_by_domain, effect="assignment", high_if_multiple_some_concerns=False, meta=None):
    """Full RoB 2 assessment for one result/outcome.

    answers_by_domain : {'D1': {...}, 'D2': {...}, 'D3': {...}, 'D4': {...}, 'D5': {...}}
    effect            : 'assignment' (ITT) or 'adhering' (per-protocol)
    Returns a structured dict with per-domain suggested + final judgements and overall.
    """
    tool = load_tool("rob2")
    domains, dom_finals = {}, {}
    for d in tool["domain_order"]:                     # D1..D5
        raw = answers_by_domain.get(d, answers_by_domain.get(d.lower(), {}))
        answers, extra = rob_domain_input(raw)
        suggested = rob2_domain_judgement(d, answers, effect=effect)
        final = normalize_judgement(extra["judgement"]) if extra.get("judgement") else suggested
        dom_finals[d] = final
        domains[d] = {
            "code": d, "name": tool["domain_short"][d],
            "judgement": final, "rule_suggested": suggested,
            "overridden": final != suggested,
            "answers": {k: normalize_answer(x) for k, x in answers.items()},
            "rationale": extra.get("rationale"), "evidence": extra.get("evidence"),
        }
    overall_suggested = rob2_overall(dom_finals, high_if_multiple_some_concerns)
    overall = normalize_judgement(meta["overall"]) if (meta and meta.get("overall")) else overall_suggested
    out = {"tool": "RoB 2", "effect": effect,
           "domains": domains, "domain_judgements": dom_finals,
           "overall": overall, "overall_rule_suggested": overall_suggested}
    if meta:
        out.update({k: v for k, v in meta.items() if k != "overall"})
    return out


def assess_robins_i(answers_by_domain, meta=None):
    """Full ROBINS-I assessment for one result/outcome.

    answers_by_domain : {'D1': {...}, ..., 'D7': {...}}
    Domain rule outputs are SUGGESTIONS; supply {'judgement': ...} per domain to set the
    assessor FINAL (e.g. to record a 'critical' judgement, which is never auto-assigned).
    """
    tool = load_tool("robins-i")
    domains, dom_finals = {}, {}
    for d in tool["domain_order"]:                     # D1..D7
        raw = answers_by_domain.get(d, answers_by_domain.get(d.lower(), {}))
        answers, extra = rob_domain_input(raw)
        suggested = robins_i_domain_judgement(d, answers)
        final = normalize_judgement(extra["judgement"]) if extra.get("judgement") else suggested
        dom_finals[d] = final
        domains[d] = {
            "code": d, "name": tool["domain_short"][d],
            "judgement": final, "rule_suggested": suggested,
            "overridden": final != suggested,
            "answers": {k: normalize_answer(x) for k, x in answers.items()},
            "rationale": extra.get("rationale"), "evidence": extra.get("evidence"),
        }
    overall_suggested = robins_i_overall(dom_finals)
    overall = normalize_judgement(meta["overall"]) if (meta and meta.get("overall")) else overall_suggested
    out = {"tool": "ROBINS-I",
           "domains": domains, "domain_judgements": dom_finals,
           "overall": overall, "overall_rule_suggested": overall_suggested}
    if meta:
        out.update({k: v for k, v in meta.items() if k != "overall"})
    return out


def results_to_traffic_light_df(results, tool="rob2"):
    """Turn a list of assess_* result dicts (each with a 'trial'/'study' key) into a
    tidy traffic-light DataFrame: one row per study, columns = domain codes + OVERALL."""
    import pandas as pd
    order = load_tool(tool)["domain_order"]
    rows = []
    for r in results:
        name = r.get("trial") or r.get("study") or r.get("id") or r.get("citation") or "?"
        row = {"trial": name}
        for d in order:
            row[d] = r["domain_judgements"].get(d)
        row["OVERALL"] = r.get("overall")
        rows.append(row)
    return pd.DataFrame(rows)


# ============================================================================= #
# Traffic-light plots (robvis-style). Colour + glyph conventions per judgement.
# ============================================================================= #
JUDGEMENT_STYLE = {
    "low":            {"color": "#4caf50", "glyph": "+", "label": "Low"},
    "some concerns":  {"color": "#ffcc29", "glyph": "-", "label": "Some concerns"},
    "moderate":       {"color": "#ffcc29", "glyph": "-", "label": "Moderate"},
    "high":           {"color": "#e4392e", "glyph": "x", "label": "High"},
    "serious":        {"color": "#e4392e", "glyph": "x", "label": "Serious"},
    "critical":       {"color": "#8b0000", "glyph": "!", "label": "Critical"},
    "no information": {"color": "#5b8bd0", "glyph": "?", "label": "No information"},
}
ROB_TOOL_LEGEND = {
    "rob2": ["low", "some concerns", "high"],
    "robins-i": ["low", "moderate", "serious", "critical", "no information"],
}


def rob_coerce_traffic_df(data, tool):
    """Accept a DataFrame, a CSV path, or a list of assess_* result dicts."""
    import pandas as pd
    if isinstance(data, list):
        return results_to_traffic_light_df(data, tool)
    if isinstance(data, str):
        return pd.read_csv(data)
    return data.copy()


def rob_resolve_columns(df, tool, study_col, domain_cols, overall_col):
    order = load_tool(tool)["domain_order"]
    if study_col is None:
        study_col = df.columns[0]
    if domain_cols is None:
        domain_cols = [c for c in df.columns if c in order]
        if not domain_cols:  # fall back to everything between study and overall
            domain_cols = [c for c in df.columns if c not in (study_col, overall_col)]
    if overall_col is None:
        overall_col = next((c for c in df.columns if str(c).lower() in ("overall", "overall bias")), None)
    return study_col, domain_cols, overall_col


def traffic_light_plot(data, tool="rob2", study_col=None, domain_cols=None,
                       overall_col=None, title=None, save_path=None, figsize=None,
                       show_overall=True, dpi=200):
    """robvis-style traffic-light plot: one row per study, one column per domain
    (+ an 'Overall' column). `data` may be a DataFrame, a CSV path, or a list of
    assess_rob2()/assess_robins_i() result dicts. Returns the matplotlib Figure.
    """
    import matplotlib
    import matplotlib.pyplot as plt
    df = rob_coerce_traffic_df(data, tool)
    study_col, domain_cols, overall_col = rob_resolve_columns(df, tool, study_col, domain_cols, overall_col)
    cols = list(domain_cols) + ([overall_col] if (show_overall and overall_col) else [])
    col_labels = [str(c) for c in domain_cols] + (["Overall"] if (show_overall and overall_col) else [])

    n_rows, n_cols = len(df), len(cols)
    if figsize is None:
        figsize = (1.2 * n_cols + 3.0, 0.5 * n_rows + 1.8)
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    studies = list(df[study_col])
    for yi, (_, r) in enumerate(df.iterrows()):
        y = n_rows - 1 - yi
        for xi, c in enumerate(cols):
            try:
                j = normalize_judgement(r[c])
            except Exception:
                continue
            st = JUDGEMENT_STYLE.get(j)
            if not st:
                continue
            ax.scatter([xi], [y], s=430, c=st["color"], edgecolors="black",
                       linewidths=0.8, zorder=3)
            ax.text(xi, y, st["glyph"], ha="center", va="center",
                    color="white", fontsize=11, fontweight="bold", zorder=4)

    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(col_labels, fontsize=10)
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(list(reversed(studies)), fontsize=9)
    ax.set_xlim(-0.6, n_cols - 0.4)
    ax.set_ylim(-0.6, n_rows - 0.4)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(True, color="#dddddd", linewidth=0.7)
    if show_overall and overall_col:                   # separator before Overall column
        ax.axvline(n_cols - 1.5, color="#999999", linewidth=1.0, linestyle="--")

    # legend
    seen, handles = [], []
    for j in ROB_TOOL_LEGEND.get(tool, list(JUDGEMENT_STYLE)):
        st = JUDGEMENT_STYLE[j]
        handles.append(plt.Line2D([0], [0], marker="o", linestyle="", markersize=11,
                       markerfacecolor=st["color"], markeredgecolor="black",
                       label="%s  (%s)" % (st["label"], st["glyph"])))
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0),
              frameon=False, fontsize=9, title="Judgement", title_fontsize=9)
    if title:
        ax.set_title(title, fontsize=12, pad=22)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight", dpi=dpi)
    return fig


def weighted_bar_plot(data, tool="rob2", domain_cols=None, overall_col=None,
                      weights=None, save_path=None, figsize=(9, 4.2), dpi=200,
                      title=None, show_overall=False):
    """robvis-style weighted summary bar plot: for each domain, a horizontal stacked
    bar showing the % of studies (optionally weighted) at each judgement level.
    `weights` is an optional per-study sequence (e.g. sample sizes)."""
    import numpy as np
    import matplotlib.pyplot as plt
    df = rob_coerce_traffic_df(data, tool)
    study_col, domain_cols, overall_col = rob_resolve_columns(df, tool, None, domain_cols, overall_col)
    cols = list(domain_cols) + ([overall_col] if (show_overall and overall_col) else [])
    labels = [str(c) for c in domain_cols] + (["Overall"] if (show_overall and overall_col) else [])
    levels = ROB_TOOL_LEGEND.get(tool, list(dict.fromkeys(JUDGEMENT_STYLE)))
    w = np.asarray(weights, float) if weights is not None else np.ones(len(df))

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    y = np.arange(len(cols))[::-1]
    lefts = np.zeros(len(cols))
    # per-column total weight over rows that carry a recognizable judgement
    totals = np.array([w[np.array([rob_safe_norm(v) is not None for v in df[c]])].sum() for c in cols], float)
    totals = np.where(totals == 0, 1.0, totals)
    for lev in levels:
        vals = []
        for c in cols:
            mask = np.array([rob_safe_norm(v) == lev for v in df[c]])
            vals.append(w[mask].sum())
        pct = 100.0 * np.asarray(vals) / totals
        ax.barh(y, pct, left=lefts, color=JUDGEMENT_STYLE[lev]["color"],
                edgecolor="white", label=JUDGEMENT_STYLE[lev]["label"])
        lefts += pct
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Percentage of studies", fontsize=10)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False,
              fontsize=9, title="Judgement", title_fontsize=9)
    if title:
        ax.set_title(title, fontsize=12)
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight", dpi=dpi)
    return fig


def rob_safe_norm(v):
    try:
        return normalize_judgement(v)
    except Exception:
        return None


# ============================================================================= #
# Reader helper: a fillable answer scaffold for one study/result.
# ============================================================================= #
def answer_template(tool, effect="assignment"):
    """Return a blank, fillable answer scaffold for one result.

    Shape: {domain_code: {'answers': {sq_id: None, ...}, 'rationale': None, 'evidence': None}}
    The agent (reader) fills each `answers[sq_id]` with Y/PY/PN/N/NI/NA, writes a one-line
    `rationale`, and pastes the supporting `evidence` quote(s) with location. The filled
    dict is passed straight to assess_rob2()/assess_robins_i().
    """
    sqs = get_signalling_questions(tool, effect=effect)
    out = {}
    for dom, spec in sqs.items():
        code = "D2" if dom in ("D2_assignment", "D2_adhering") else dom
        entry = out.setdefault(code, {"answers": {}, "rationale": None, "evidence": None})
        for qid in spec["signalling_questions"]:
            entry["answers"][qid] = None
    return out


def question_text(tool, domain, sq_id, effect="assignment"):
    """Return the wording of a single signalling question."""
    sqs = get_signalling_questions(tool, domain=domain, effect=effect)
    spec = next(iter(sqs.values()))
    return spec["signalling_questions"][sq_id]["text"]
