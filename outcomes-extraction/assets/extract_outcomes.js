export const meta = {
  name: 'outcomes-extraction-os-dfs-rfs',
  description: 'Extract OS/DFS/RFS effect estimates into the pairwise / network / subgroup outcome tables via two independent reviewers plus a senior adjudicator who re-derives every value',
  phases: [
    { title: 'Reviewer A', detail: 'first independent reviewer reads the sources and extracts every required result with provenance' },
    { title: 'Reviewer B', detail: 'second independent reviewer, different model, does the same WITHOUT seeing reviewer A' },
    { title: 'Senior adjudication', detail: 'senior reviewer re-derives every value from source, then reconciles against both drafts' },
  ],
}

// ---------------------------------------------------------------------------
// Config. Pass either the bare jobs array (back-compatible) or:
//   { vocabulary: '/abs/..._node_vocabulary.json',
//     jobs: [...], models: { a: 'opus', b: 'sonnet', senior: 'opus' } }
//
// The senior adjudicator is pinned to Opus rather than inheriting the session
// model. Adjudication means reading verbatim clinical trial text and quoting it
// back; models with heavier response filtering can decline or soften that, and a
// senior that hedges is worse than useless because everything downstream trusts
// it. Pin it, don't inherit it.
//
// `vocabulary` is the project's controlled node vocabulary. All three roles are
// given the path and read the file themselves - a workflow script cannot read
// files, the agents it spawns can. Without it the run emits whatever wording each
// agent read off the page, and netmeta turns each spelling into its own node.
// ---------------------------------------------------------------------------
const cfg = Array.isArray(args) ? { jobs: args } : (args || {});
const jobs = cfg.jobs || [];
const VOCAB = cfg.vocabulary || null;
const MODELS = Object.assign({ a: 'opus', b: 'sonnet', senior: 'opus' }, cfg.models || {});

// Fields compared between the two reviewers to compute concordance.
const DATA_FIELDS = [
  'endpoint_used', 'treatment_name', 'control_name',
  'hr', 'ci_lower', 'ci_upper',
  'surv_treatment', 'surv_control', 'surv_timepoint',
  'median_treatment', 'median_control',
  'et', 'nt', 'ec', 'nc', 'extraction_possible',
];

// The node-label rules, in the brief every role reads. They are stated here and in
// references/node-vocabulary.md; the machine-checkable version is scripts/nodes.py, which qc.py runs
// over the finished sheet.
const NODE_RULES = `
*** NODE LABELS ARE A CONTROLLED VOCABULARY - NOT THE PAPER'S WORDING ***
treatment_name and control_name are NODE LABELS. A network meta-analysis joins arms by STRING EQUALITY,
so "Nivolumab + Ipilimumab" and "Nivolumab plus iplimumab" are TWO nodes, not one: the network fragments,
or keeps a connection while an edge silently disappears, or splits one regimen's evidence across two
underpowered nodes and inverts the ranking. NONE of this is visible in the extraction sheet - every cell
looks fine and the failure only surfaces as a wrong league table. Long labels also wreck league tables
and network plots, which are n x n grids of node names.
${VOCAB
  ? `READ THE VOCABULARY FIRST (Read tool), BEFORE you write any arm label:\n    ${VOCAB}\nUse ONLY labels it defines. Its \`aliases\` map translates a paper's own wording (and known\nmisspellings) into the canonical label - use it rather than composing a label yourself.`
  : `NO VOCABULARY FILE WAS SUPPLIED for this run. Apply the rules below, keep labels SHORT and\nUPPERCASE, and FLAG every arm label you emit so a human can canonicalise it. Do not invent an\nabbreviation you are not confident about.`}
THE RULES
  1. AGENT labels are UPPERCASE, 3-5 characters, no punctuation:
        SUN SOR PAZO AXI EVE PEM NIVO IPI ATEZO BELZ GIREN DURVA TREME
  2. COMBINATIONS join with a bare "+" and NO SPACES:
        NIVO+IPI      never "NIVO + IPI", never "NIVO plus IPI", never "Nivo+Ipi"
     Whitespace is FORBIDDEN, not normalised: a trailing or non-breaking space pasted out of a PDF is
     visually identical in a spreadsheet cell, so nobody can see it - not you, not a reviewer.
  3. COMPONENT ORDER is fixed by the vocabulary's \`combinations\` list. It is NOT derived from a rule -
     "backbone first" and "alphabetical" disagree. Look the string up; do not compose it.
  4. The POOLED COMPARATOR is ONE label (default NOADJ) whatever the trial actually used - placebo,
     observation, surgery alone. What it actually was goes in the separate control_actual field, so a
     blinding/control-type sensitivity analysis can still separate them. ONE EXCEPTION: a trial whose
     control arm is an ACTIVE REGIMEN (an add-on design) does NOT get NOADJ - it gets that regimen's
     own label, because it genuinely is a different node.
  5. DOSE, DURATION and SETTING variants are HYPHEN-SUFFIXED and the suffix is PART OF THE NODE IDENTITY:
        SOR-1Y  SOR-3Y  SOR-NEO  PAZO-600  PAZO-800  NIVO-PERI
     Never reuse the base label for a variant - that silently merges two nodes.
A LABEL YOU CANNOT RESOLVE IS A FLAG, NEVER A GUESS. If the paper's wording matches no label and no
alias, put the paper's wording in a flag, say what you think it should be, and let the reviewer who owns
the vocabulary decide. Do not invent a label and do not extend the vocabulary yourself - inventing a
label at extraction time and backfilling later is exactly how the second spelling of a regimen gets in.
NOT a node label: the "comparison" label you are given for each item (e.g. "Primary", "3 year
Sorafenib") is the sheet's ROW KEY. Echo it verbatim; never canonicalise it.
`;

const BRIEF = `
You are extracting survival/recurrence OUTCOME data from a single randomized controlled trial publication
into a structured evidence table. Endpoints: OS = Overall Survival, DFS = Disease-Free/Progression-Free
Survival, RFS = Recurrence-Free Survival/Interval. You will be told exactly which results to produce for
THIS paper, and for each one WHICH TEMPLATE FAMILY it belongs to.

TEMPLATE FAMILIES - read this before you read a single number
  family "pwma"          -> a pairwise meta-analysis row. OVERALL (ITT / full) POPULATION ONLY.
                            One row per treatment-vs-control comparison. Feeds the primary and
                            sensitivity pairwise analyses.
  family "nma"           -> a network meta-analysis row. OVERALL (ITT / full) POPULATION ONLY.
                            T1 = the TREATMENT arm, T2 = the ACTIVE COMPARATOR (usually the trial's
                            control arm). Feeds the primary and secondary network analyses.
  family "pwma_subgroup" -> a SUBGROUP row. You are given a SUBGROUP LABEL; extract the result WITHIN
                            THAT SUBGROUP ONLY, with that subgroup's own denominators - NOT the overall
                            population. One row per (comparison x subgroup level). Feeds subgroup
                            analysis and tests for interaction between subgroups.
NEVER put an overall-population estimate on a subgroup row, and never put a subgroup estimate on a
"pwma"/"nma" row. If a required subgroup result is not reported, or is reported only pooled with
another level, or only as an interaction p-value, set extraction_possible="No", set every data field
to "NA", and flag it. An honest "No" is a finding (the analyst learns the interaction test cannot
include that level); an invented number is the worst possible answer. On "pwma"/"nma" rows set
extraction_possible="NA".

*** THE Ec/Et TRAP - the single most damaging error you can make here ***
The two sheet layouts use the SAME LETTERS for OPPOSITE things:
  pwma / pwma_subgroup sheet:  Et = EVENTS in treatment, Nt = N in treatment,
                               Ec = EVENTS in control,   Nc = N in control
  nma sheet:                   Ec T1 = EVENT COUNT in T1, Et T1 = EVENT TOTAL (participants) in T1
                               Ec T2 = EVENT COUNT in T2, Et T2 = EVENT TOTAL (participants) in T2
So "Et" is an EVENT COUNT on one sheet and a PARTICIPANT TOTAL on the other. A swap looks completely
plausible and nothing downstream catches it.
YOU NEVER RESOLVE THIS. In your JSON output the four count fields ALWAYS carry the pwma meaning, in
EVERY family:
    et = events in the treatment arm (T1)        nt = N in the treatment arm (T1)
    ec = events in the control/comparator arm (T2)   nc = N in that arm (T2)
The relabelling into the nma sheet's Ec/Et columns happens later, in code. Do not pre-swap anything.
Denominators are INTENTION-TO-TREAT / as-randomised (or the subgroup's ITT N on subgroup rows); if only
an as-analysed set is reported, use it and FLAG it. Before you return: check et <= nt and ec <= nc in
every result. An event count above its denominator means you crossed the conventions.
${NODE_RULES}
GOLDEN RULES
1. SOURCES ONLY. Use only the provided files (main text + supplements). Never use outside knowledge or other
   papers. If a value is not in these files, return "NA" (do NOT guess). The design/anchor numbers in your task
   only help you LOCATE values - you must still CONFIRM each value against the actual text/table/figure and cite it.
2. PROVENANCE. For every non-NA value, add {field, source (page/table/figure), snippet (short verbatim quote)}.
   No snippet -> return NA for that field.
3. HR DIRECTION. hr/ci_lower/ci_upper = hazard ratio of TREATMENT vs CONTROL (treatment in numerator). A default
   treatment/control is given (experimental = Treatment, standard = Control). CONFIRM against the paper; if the
   paper reports the HR the other way, INVERT (HR'=1/HR, new_lower=1/old_upper, new_upper=1/old_lower) and flag.
   If you change the arm assignment, set treatment_name/control_name accordingly and flag.
4. CONFIDENCE-INTERVAL LEVEL. Most trials report 95% CIs, but multi-arm trials that split alpha across
   comparisons often report 97.5% (or other) limits. Read what the paper actually states. If the level is NOT
   95%, still report the limits AS PRINTED, and FLAG the level explicitly (e.g. "97.5% CI as printed") so the
   downstream standard-error derivation uses the right z. Never silently relabel a non-95% interval as 95%.
5. ENDPOINT MATCHING (table = endpoint):
   - OS table: overall survival (death from any cause).
   - DFS table: disease-free / invasive-DFS / PFS composite. Use the paper's DFS-type composite; note endpoint_used.
   - RFS table: a RECURRENCE-specific endpoint. Priority RFS > recurrence-free interval (RFI) > breast
     cancer-free interval (BCFI) > distant-recurrence-free. Use the closest, set endpoint_used to its exact name,
     and flag the substitution. If ONLY a broad composite (DFS/iDFS/EFS) exists, set the RFS effect cells to NA
     and flag "no recurrence-specific endpoint reported" (do NOT copy the DFS HR).
6. SURVIVAL RATE cells (surv_treatment/surv_control): event-free % at the LONGEST/headline landmark for that
   endpoint; put the timepoint in surv_timepoint and cite it. Bare number. If only cumulative INCIDENCE is given,
   report 100 - incidence and flag. NA if not reported.
7. EVENTS/N: et/ec = events in treatment/control (OS=deaths; DFS=DFS events; RFS=recurrence events matching
   endpoint_used). nt/nc = N per arm (prefer ITT/as-randomised; if only as-analysed, use it + flag). Integers; NA
   if not reported. A shared control arm across two comparisons of the same trial must show the SAME control et/nc.
   These four keys keep the pwma meaning in EVERY family - see THE Ec/Et TRAP above. et <= nt and ec <= nc, always.
8. MEDIAN survival: almost always "NA" (not reached). Fill only if explicitly reported.
9. Formats: HR/CI/rates as reported (e.g. "0.82", "76.1"); treatment_name/control_name = the CANONICAL NODE
   LABEL from the vocabulary (e.g. "NIVO+IPI", "SOR-1Y", "NOADJ"), never the paper's prose - see NODE LABELS
   above; literal "NA" for anything not reported.
10. FLAG every judgment call: arm/direction changes, HR inversion, non-95% CI levels, endpoint substitution,
   figure-read values, denominator (ITT vs analysed) choices, population caveats, descriptive-only HRs.

PUBLICATION TYPE (O/F): judge whether this is an ORIGINAL/pivotal report ("original" -> "O") or a long-term
FOLLOW-UP / "N-year update" / "follow-up analysis" of an earlier-reported trial ("followup" -> "F").

READING TIPS: PDFs via the Read tool; files >10 pages need a page range (max 20 pages/call). Go to the Results
text, the efficacy summary table, and Kaplan-Meier figures / forest plots / supplementary tables for HRs, CIs,
event counts, and landmark rates. Read the supplement files too. Many HRs and CIs exist ONLY inside KM-curve or
forest-plot IMAGES that a text dump cannot surface - render and read those figures rather than concluding
"not reported".
`;

const FIELDS_DOC = `Per required item, return one result object: table (echo the requested key), family (echo:
"pwma" | "nma" | "pwma_subgroup"), comparison (echo the requested label EXACTLY), subgroup (echo the requested
subgroup label EXACTLY on pwma_subgroup items; "NA" on main-sheet items), extraction_possible ("Yes"/"No" on
pwma_subgroup items; "NA" on main-sheet items), endpoint_used, treatment_name, control_name, hr, ci_lower,
ci_upper, surv_treatment, surv_control, surv_timepoint, median_treatment, median_control, et, nt, ec, nc,
flags[], provenance[]. "NA" for any unreported value. The comparison + subgroup labels are the row key - echo
them verbatim; a re-worded label orphans the row. treatment_name and control_name are CANONICAL NODE LABELS
from the vocabulary (not the paper's wording, no spaces, "+" for combinations); an unresolvable one is a flag.`;

const RESULT_ITEM = {
  type: 'object', additionalProperties: false,
  required: ['table','family','comparison','subgroup','extraction_possible','endpoint_used','treatment_name','control_name','hr','ci_lower','ci_upper','surv_treatment','surv_control','surv_timepoint','median_treatment','median_control','et','nt','ec','nc','flags','provenance'],
  properties: {
    table: { type: 'string' },
    family: { type: 'string', enum: ['pwma','nma','pwma_subgroup'] },
    comparison: { type: 'string' }, subgroup: { type: 'string' },
    extraction_possible: { type: 'string', enum: ['Yes','No','NA'] },
    endpoint_used: { type: 'string' }, treatment_name: { type: 'string' }, control_name: { type: 'string' },
    hr: { type: 'string' }, ci_lower: { type: 'string' }, ci_upper: { type: 'string' },
    surv_treatment: { type: 'string' }, surv_control: { type: 'string' }, surv_timepoint: { type: 'string' },
    median_treatment: { type: 'string' }, median_control: { type: 'string' },
    et: { type: 'string' }, nt: { type: 'string' }, ec: { type: 'string' }, nc: { type: 'string' },
    flags: { type: 'array', items: { type: 'string' } },
    provenance: { type: 'array', items: { type: 'object', additionalProperties: false,
      required: ['field','source','snippet'],
      properties: { field: {type:'string'}, source: {type:'string'}, snippet: {type:'string'} } } },
  },
};

// Both reviewers return exactly the same shape. Neither knows the other exists.
const REVIEW_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['paper_id','trial_name','nct','pmid','of_recommendation','results','paper_flags'],
  properties: {
    paper_id: { type: 'number' }, trial_name: { type: 'string' }, nct: { type: 'string' },
    pmid: { type: 'string' }, of_recommendation: { type: 'string', enum: ['O','F'] },
    results: { type: 'array', items: RESULT_ITEM }, paper_flags: { type: 'array', items: { type: 'string' } },
  },
};

const SENIOR_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['paper_id','trial_name','nct','pmid','of_recommendation','results','paper_flags','adjudications','unresolved','confidence'],
  properties: {
    paper_id: { type: 'number' }, trial_name: { type: 'string' }, nct: { type: 'string' },
    pmid: { type: 'string' }, of_recommendation: { type: 'string', enum: ['O','F'] },
    results: { type: 'array', items: RESULT_ITEM }, paper_flags: { type: 'array', items: { type: 'string' } },
    adjudications: { type: 'array', items: { type: 'object', additionalProperties: false,
      required: ['table','comparison','subgroup','field','value_a','value_b','senior_value','agreed_with','reason'],
      properties: { table:{type:'string'}, comparison:{type:'string'}, subgroup:{type:'string'},
        field:{type:'string'},
        value_a:{type:'string'}, value_b:{type:'string'}, senior_value:{type:'string'},
        agreed_with: { type:'string', enum: ['A','B','both','neither'] }, reason:{type:'string'} } } },
    unresolved: { type: 'array', items: { type: 'object', additionalProperties: false,
      required: ['table','comparison','subgroup','field','why'],
      properties: { table:{type:'string'}, comparison:{type:'string'}, subgroup:{type:'string'},
        field:{type:'string'}, why:{type:'string'} } } },
    confidence: { type: 'string' },
  },
};

// ---------------------------------------------------------------------------
// Concordance is computed in plain code, not by an agent. It is a RECORDED
// QUALITY METRIC, not a gate: the senior re-derives every value regardless of
// whether the two reviewers agreed. Agreement between two models tells you how
// legible the value was in the source, not whether it is correct.
// ---------------------------------------------------------------------------
function norm(v) {
  if (v === null || v === undefined) return 'NA';
  const s = String(v).trim();
  if (s === '' || /^(na|n\/a|nr|not reported|none)$/i.test(s)) return 'NA';
  const num = s.replace(/[,\s]/g, '');
  if (/^-?\d*\.?\d+%?$/.test(num)) {
    const f = parseFloat(num.replace('%', ''));
    if (!Number.isNaN(f)) return String(Math.round(f * 1000) / 1000);
  }
  return s.toLowerCase().replace(/[\s.,;:()\[\]-]+/g, ' ').trim();
}

// Row identity includes the subgroup level: on a pwma_subgroup sheet the same (table, comparison)
// legitimately appears once per level, so comparing without it would collapse distinct rows.
function keyOf(r) { return `${r.table}||${r.comparison}||${r.subgroup ?? 'NA'}`; }

function compareReviews(a, b) {
  const out = {
    total_fields: 0, concordant: 0, discordant: 0, rate: null,
    of_recommendation: { a: a?.of_recommendation ?? 'NA', b: b?.of_recommendation ?? 'NA', concordant: false },
    rows_only_in_a: [], rows_only_in_b: [], discordant_items: [], by_field: {},
  };
  if (!a || !b) { out.note = !a && !b ? 'both reviewers failed' : `only reviewer ${a ? 'A' : 'B'} returned`; return out; }

  out.of_recommendation.concordant = norm(a.of_recommendation) === norm(b.of_recommendation);
  const ma = new Map((a.results || []).map(r => [keyOf(r), r]));
  const mb = new Map((b.results || []).map(r => [keyOf(r), r]));
  for (const k of ma.keys()) if (!mb.has(k)) out.rows_only_in_a.push(k);
  for (const k of mb.keys()) if (!ma.has(k)) out.rows_only_in_b.push(k);

  for (const [k, ra] of ma) {
    const rb = mb.get(k);
    if (!rb) continue;
    for (const f of DATA_FIELDS) {
      const va = norm(ra[f]), vb = norm(rb[f]);
      out.total_fields++;
      out.by_field[f] = out.by_field[f] || { concordant: 0, discordant: 0 };
      if (va === vb) { out.concordant++; out.by_field[f].concordant++; }
      else {
        out.discordant++; out.by_field[f].discordant++;
        const [table, comparison, subgroup] = k.split('||');
        out.discordant_items.push({ table, comparison, subgroup, field: f,
          a: String(ra[f] ?? 'NA'), b: String(rb[f] ?? 'NA') });
      }
    }
  }
  out.rate = out.total_fields ? Math.round((out.concordant / out.total_fields) * 1000) / 1000 : null;
  return out;
}

// ---------------------------------------------------------------------------
log(`Outcomes extraction: ${jobs.length} papers, ${jobs.reduce((a, j) => a + j.needed.length, 0)} required rows.`);
log(`Reviewers: A=${MODELS.a}, B=${MODELS.b}, senior=${MODELS.senior || 'session model'}. Senior re-derives every value.`);
if (VOCAB) log(`Node vocabulary: ${VOCAB} - all three roles read it and emit canonical labels only.`);
else log(`WARNING: no node vocabulary supplied. Arm labels will be whatever wording each agent read off the page, and netmeta turns each spelling into a separate node. Pass { vocabulary: '/abs/..._node_vocabulary.json', jobs: [...] } and validate with qc.py --vocabulary.`);

// Shape check for a node label, mirroring CANON_RE in scripts/nodes.py. Shape only: whether a label is
// actually IN the vocabulary is checked by nodes.py via qc.py, which can read the file. This catches the
// failures that need no vocabulary to spot - whitespace, lowercase, word joiners, prose.
const CANON_RE = /^[A-Z0-9]{2,6}(-[A-Z0-9]{1,5})?(\+[A-Z0-9]{2,6}(-[A-Z0-9]{1,5})?)*$/;
function labelProblem(v) {
  const s = String(v ?? '').trim();
  if (s === '' || /^(na|n\/a|nr)$/i.test(s)) return null;      // genuine missingness, not a label error
  if (CANON_RE.test(s)) return null;
  if (/\s/.test(s)) return 'contains whitespace';
  if (/\bplus\b|\band\b|\/|&|,/i.test(s)) return 'uses a word or symbol joiner instead of a bare "+"';
  if (s !== s.toUpperCase()) return 'is not uppercase';
  return 'is not a canonical label shape';
}

// Each item announces its FAMILY (and, for subgroup rows, the exact level) so the role filling it
// knows whether it is extracting the ITT population or one stratum, and which arm semantics apply.
function neededBlock(job) {
  return job.needed.map((n, i) => {
    const fam = n.family || 'pwma';
    const pop = fam === 'pwma_subgroup'
      ? `SUBGROUP="${n.subgroup}" (extract WITHIN this subgroup only; answer extraction_possible Yes/No)`
      : (fam === 'nma'
          ? 'OVERALL ITT population; T1=Treatment, T2=Control/active comparator'
          : 'OVERALL ITT population');
    return `  [${i + 1}] table=${n.table} | family=${fam} | comparison="${n.comparison}" | ${pop}\n` +
           `      default Treatment="${n.treatment}" vs Control="${n.control}" (canonical node labels - ` +
           `confirm/flip against the paper, but emit them in this canonical form) | note: ${n.note || ''}`;
  }).join('\n');
}

function reviewerPrompt(job) {
  return `${BRIEF}

You are an INDEPENDENT REVIEWER extracting this paper on your own. Another reviewer is extracting the same
paper separately; you will never see their work and they will never see yours. Do not try to guess what they
would say or hedge toward a "safe" answer - report exactly what YOU can prove from these sources. Your
independence is the entire point: if you converge on a wrong value because you were anchored, the check fails.

PAPER: id=${job.paper_id} | trial="${job.trial}" | NCT=${job.nct} | PMID(approx, verify)=${job.pmid}
DESIGN / ANCHORS: ${job.design}

SOURCE FILES (read all, including every supplement):
${job.files.map(f => '  - ' + f).join('\n')}

REQUIRED RESULTS (produce exactly one result object per item, echoing table+family+comparison+subgroup):
${neededBlock(job)}

${FIELDS_DOC}
Return the PAPER object: paper_id, trial_name, nct, pmid (the real PubMed ID printed in the paper if visible,
else "NA"), of_recommendation ("O"/"F"), results[], paper_flags[].`;
}

function seniorPrompt(job, a, b, conc) {
  const discordantBlock = conc.discordant_items.length
    ? conc.discordant_items.map(d => `  - [${d.table} | ${d.comparison}${d.subgroup && d.subgroup !== 'NA' ? ' | ' + d.subgroup : ''}] ${d.field}:  A="${d.a}"  vs  B="${d.b}"`).join('\n')
    : '  (none - the two reviewers agreed on every field; this does NOT mean they are right)';
  const rowNotes = [
    conc.rows_only_in_a.length ? `  Rows only reviewer A produced: ${conc.rows_only_in_a.join(', ')}` : '',
    conc.rows_only_in_b.length ? `  Rows only reviewer B produced: ${conc.rows_only_in_b.join(', ')}` : '',
    conc.of_recommendation.concordant ? '' : `  O/F disagreement: A="${conc.of_recommendation.a}" vs B="${conc.of_recommendation.b}"`,
  ].filter(Boolean).join('\n');

  return `${BRIEF}

You are the SENIOR REVIEWER for paper id=${job.paper_id} (trial "${job.trial}"). Two reviewers extracted this
paper independently. Your job is NOT to pick a winner between them.

WORK IN THIS ORDER, AND DO NOT DEVIATE:
STEP 1. Open and read EVERY source file below IN FULL, from scratch, before you look at either draft. Read the
        results text, every efficacy table, every Kaplan-Meier figure, every forest plot, and every supplement.
        Render and read figures - many hazard ratios and confidence intervals exist only as images.
STEP 2. Derive EVERY required value yourself from what you just read, with its own provenance. Every value,
        including ones the two reviewers agreed on. Agreement between two models means a value was easy to
        read, not that it is correct - two readers can make the same mistake for the same reason.
STEP 3. ONLY THEN compare your own derivation against the two drafts below, and record an adjudication for
        every field where any of the three of you differ.
STEP 4. Before returning, run the family checks on YOUR results: every "pwma"/"nma" row is the OVERALL ITT
        population (no subgroup estimate smuggled in); every "pwma_subgroup" row is that named level only,
        with its own denominators, and answers extraction_possible; et <= nt and ec <= nc everywhere (an
        event count above its denominator means the Ec/Et conventions were crossed - see the brief).
STEP 5. ADJUDICATE THE ARM LABELS - this is part of the job, not a formatting afterthought. Check every
        treatment_name and control_name against the vocabulary: exact canonical string, "+" with NO spaces,
        component order as the \`combinations\` list has it, the single pooled comparator label unless the
        control is an ACTIVE regimen, the right hyphen variant suffix. A reviewer's prose wording is an
        ERROR TO CORRECT, not a value to carry through - log it as an adjudication. A label that neither the
        vocabulary nor its aliases resolve goes to unresolved[] with the cell "NA"; do not guess one.
        netmeta joins arms by string equality, so a variant spelling silently becomes a second node and
        nothing in the finished sheet shows it.

SOURCE FILES (read all again, in full):
${job.files.map(f => '  - ' + f).join('\n')}
DESIGN / ANCHORS: ${job.design}

REQUIRED RESULTS (one object per item; echo table+family+comparison+subgroup exactly):
${neededBlock(job)}

--- Reviewer A draft (evidence about the paper's legibility, NOT an authority) ---
${JSON.stringify(a)}

--- Reviewer B draft (same status) ---
${JSON.stringify(b)}

--- Where the two reviewers disagreed (${conc.discordant}/${conc.total_fields} fields; concordance ${conc.rate}) ---
${discordantBlock}
${rowNotes}

OUTPUT
- results[]: YOUR final values, each with your own provenance and flags. These are what get written to the sheet.
- adjudications[]: one entry for EVERY field where you differ from A, from B, or where A and B differed from
  each other. Record value_a, value_b, your senior_value, agreed_with ("A", "B", "both" when all three match
  and you are logging it anyway, or "neither" when you overrode both), and a reason citing the source.
- unresolved[]: any field you CANNOT settle from these sources - genuinely ambiguous printing, a figure too
  coarse to read, a contradiction between main text and supplement. Do NOT invent a resolution and do NOT
  split the difference; list it here so a human decides. Set the corresponding value in results[] to "NA".
  An honest unresolved entry is a correct outcome. A fabricated resolution is the worst outcome.
  (Note the difference from a subgroup that the PAPER simply does not report: that is not "unresolved",
  it is extraction_possible="No" with the row NA'd - a settled finding, not a question for a human.)
- confidence: one line on how much of this paper's data you consider settled.`;
}

const papers = await pipeline(
  jobs,
  (job) => parallel([
    () => agent(reviewerPrompt(job), { label: `A:${job.paper_id}`, phase: 'Reviewer A', schema: REVIEW_SCHEMA, effort: 'high', model: MODELS.a }),
    () => agent(reviewerPrompt(job), { label: `B:${job.paper_id}`, phase: 'Reviewer B', schema: REVIEW_SCHEMA, effort: 'high', model: MODELS.b }),
  ]),
  (pair, job) => {
    const [a, b] = pair || [];
    if (!a && !b) { log(`${job.paper_id}: BOTH reviewers failed - no senior pass, paper dropped`); return null; }
    const conc = compareReviews(a, b);
    if (!a || !b) log(`${job.paper_id}: only one reviewer returned - senior runs as a single independent extraction`);
    else log(`${job.paper_id}: concordance ${conc.concordant}/${conc.total_fields} (${conc.rate}), ${conc.discordant} discordant fields`);
    const opts = { label: `senior:${job.paper_id}`, phase: 'Senior adjudication', schema: SENIOR_SCHEMA, effort: 'high' };
    if (MODELS.senior) opts.model = MODELS.senior;
    return agent(seniorPrompt(job, a, b, conc), opts)
      .then(s => {
        if (!s) { log(`${job.paper_id}: senior failed`); return null; }
        log(`${job.paper_id}: senior logged ${s.adjudications.length} adjudications, ${s.unresolved.length} unresolved`);
        return Object.assign({}, s, { concordance: conc, reviewer_a: a || null, reviewer_b: b || null });
      });
  },
);

const final = papers.filter(Boolean);

// Run-level metrics, so a living review can track whether agreement tracks truth over time.
const totals = final.reduce((acc, p) => {
  acc.fields += p.concordance.total_fields;
  acc.concordant += p.concordance.concordant;
  acc.discordant += p.concordance.discordant;
  acc.adjudications += p.adjudications.length;
  acc.senior_overrode_both += p.adjudications.filter(x => x.agreed_with === 'neither').length;
  acc.unresolved += p.unresolved.length;
  for (const r of p.results || []) {
    acc.rows_by_family[r.family || 'pwma'] = (acc.rows_by_family[r.family || 'pwma'] || 0) + 1;
    if (r.extraction_possible === 'No') acc.subgroups_not_extractable++;
    // arithmetic tripwire for a crossed Ec/Et convention; the sheet-level check lives in qc.py
    const n = (v) => { const f = parseFloat(String(v).replace(/[,\s]/g, '')); return Number.isNaN(f) ? null : f; };
    const [et, nt, ec, nc] = [n(r.et), n(r.nt), n(r.ec), n(r.nc)];
    if ((et !== null && nt !== null && et > nt) || (ec !== null && nc !== null && ec > nc)) {
      acc.events_exceed_denominator.push(`${p.paper_id}|${r.table}|${r.comparison}|${r.subgroup ?? 'NA'}`);
    }
    // node-label shape tripwire; membership in the vocabulary is enforced by qc.py --vocabulary
    for (const f of ['treatment_name', 'control_name']) {
      acc.labels_checked++;
      const why = labelProblem(r[f]);
      if (why) acc.non_canonical_labels.push(`${p.paper_id}|${r.table}|${r.comparison}|${f}="${r[f]}" ${why}`);
    }
  }
  return acc;
}, { fields: 0, concordant: 0, discordant: 0, adjudications: 0, senior_overrode_both: 0, unresolved: 0,
     rows_by_family: {}, subgroups_not_extractable: 0, events_exceed_denominator: [],
     labels_checked: 0, non_canonical_labels: [] });
totals.concordance_rate = totals.fields ? Math.round((totals.concordant / totals.fields) * 1000) / 1000 : null;

log(`DONE: ${final.length}/${jobs.length} papers. Rows by family: ${JSON.stringify(totals.rows_by_family)}.`);
log(`Reviewer concordance ${totals.concordant}/${totals.fields} (${totals.concordance_rate}).`);
log(`Senior overrode BOTH reviewers on ${totals.senior_overrode_both} field(s) - these are the values a two-reviewer-only design would have gotten wrong.`);
if (totals.unresolved) log(`${totals.unresolved} field(s) need a human decision - see unresolved[] per paper.`);
if (totals.subgroups_not_extractable) log(`${totals.subgroups_not_extractable} subgroup row(s) marked extraction_possible="No" - a finding, not a gap.`);
if (totals.events_exceed_denominator.length) log(`WARNING: ${totals.events_exceed_denominator.length} row(s) have an event count above its denominator - the Ec/Et conventions were crossed: ${totals.events_exceed_denominator.join(', ')}`);
if (totals.non_canonical_labels.length) log(`WARNING: ${totals.non_canonical_labels.length}/${totals.labels_checked} arm label(s) are not canonical node labels - each one becomes its own node in netmeta: ${totals.non_canonical_labels.join('; ')}`);
else log(`Node labels: ${totals.labels_checked} checked, all canonical in shape (membership is verified by qc.py --vocabulary).`);

return { papers: final, run_metrics: totals };
