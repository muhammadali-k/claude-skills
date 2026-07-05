export const meta = {
  name: 'outcomes-extraction-os-dfs-rfs',
  description: 'Extract OS/DFS/RFS effect estimates from trial publications into the outcome i-tables (dual extract + independent verify, per paper)',
  phases: [
    { title: 'Extract', detail: 'one extractor agent per paper reads its PDFs/supplements and pulls every required (table,comparison) result with provenance' },
    { title: 'Verify',  detail: 'an independent verifier re-derives every value from the same sources and reconciles' },
  ],
}

// Pass the jobs array (see references/workflow.md) as the Workflow `args`. For a large list or a
// resumable run, bake it in: replace `const jobs = args;` with `const jobs = <the JSON>;` and run via scriptPath.
const jobs = args;

const BRIEF = `
You are extracting survival/recurrence OUTCOME data from a single breast-cancer (or other) adjuvant RCT
publication into a structured evidence table. Three parallel tables exist:
  OS  = Overall Survival   DFS = Disease-Free/Progression-Free Survival   RFS = Recurrence-Free Survival/Interval
You will be told exactly which (table, comparison) results to produce for THIS paper.

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
4. ENDPOINT MATCHING (table = endpoint):
   - OS table: overall survival (death from any cause).
   - DFS table: disease-free / invasive-DFS / PFS composite. Use the paper's DFS-type composite; note endpoint_used.
   - RFS table: a RECURRENCE-specific endpoint. Priority RFS > recurrence-free interval (RFI) > breast
     cancer-free interval (BCFI) > distant-recurrence-free. Use the closest, set endpoint_used to its exact name,
     and flag the substitution. If ONLY a broad composite (DFS/iDFS/EFS) exists, set the RFS effect cells to NA
     and flag "no recurrence-specific endpoint reported" (do NOT copy the DFS HR).
5. SURVIVAL RATE cells (surv_treatment/surv_control): event-free % at the LONGEST/headline landmark for that
   endpoint; put the timepoint in surv_timepoint and cite it. Bare number. If only cumulative INCIDENCE is given,
   report 100 - incidence and flag. NA if not reported.
6. EVENTS/N: et/ec = events in treatment/control (OS=deaths; DFS=DFS events; RFS=recurrence events matching
   endpoint_used). nt/nc = N per arm (prefer ITT/as-randomised; if only as-analysed, use it + flag). Integers; NA
   if not reported. A shared control arm across two comparisons of the same trial must show the SAME control et/nc.
7. MEDIAN survival: almost always "NA" (not reached). Fill only if explicitly reported.
8. Formats: HR/CI/rates as reported (e.g. "0.82", "76.1"); arm names short as the paper names them; literal "NA"
   for anything not reported.
9. FLAG every judgment call: arm/direction changes, HR inversion, endpoint substitution, figure-read values,
   denominator (ITT vs analysed) choices, population caveats (adapted analyses, subgroups), descriptive-only HRs.

PUBLICATION TYPE (O/F): judge whether this is an ORIGINAL/pivotal report ("original" -> "O") or a long-term
FOLLOW-UP / "N-year update" / "follow-up analysis" of an earlier-reported trial ("followup" -> "F").

READING TIPS: PDFs via the Read tool; files >10 pages need a page range (max 20 pages/call). Go to the Results
text, the efficacy summary table, and Kaplan-Meier figures / forest plots / supplementary tables for HRs, CIs,
event counts, and landmark rates. Read the supplement files too.
`;

const FIELDS_DOC = `Per required (table,comparison) item, return one result object: table, comparison (echo the
requested label EXACTLY), endpoint_used, treatment_name, control_name, hr, ci_lower, ci_upper, surv_treatment,
surv_control, surv_timepoint, median_treatment, median_control, et, nt, ec, nc, flags[], provenance[]. "NA" for any
unreported value.`;

const RESULT_ITEM = {
  type: 'object', additionalProperties: false,
  required: ['table','comparison','endpoint_used','treatment_name','control_name','hr','ci_lower','ci_upper','surv_treatment','surv_control','surv_timepoint','median_treatment','median_control','et','nt','ec','nc','flags','provenance'],
  properties: {
    table: { type: 'string', enum: ['OS','DFS','RFS'] }, comparison: { type: 'string' },
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
const PAPER_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['paper_id','trial_name','nct','pmid','of_recommendation','results','paper_flags'],
  properties: {
    paper_id: { type: 'number' }, trial_name: { type: 'string' }, nct: { type: 'string' },
    pmid: { type: 'string' }, of_recommendation: { type: 'string', enum: ['O','F'] },
    results: { type: 'array', items: RESULT_ITEM }, paper_flags: { type: 'array', items: { type: 'string' } },
  },
};
const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['paper_id','trial_name','nct','pmid','of_recommendation','results','paper_flags','disagreements','confidence'],
  properties: {
    paper_id: { type: 'number' }, trial_name: { type: 'string' }, nct: { type: 'string' },
    pmid: { type: 'string' }, of_recommendation: { type: 'string', enum: ['O','F'] },
    results: { type: 'array', items: RESULT_ITEM }, paper_flags: { type: 'array', items: { type: 'string' } },
    disagreements: { type: 'array', items: { type: 'object', additionalProperties: false,
      required: ['table','comparison','field','extractor_value','verifier_value','resolved_value','reason'],
      properties: { table:{type:'string'}, comparison:{type:'string'}, field:{type:'string'},
        extractor_value:{type:'string'}, verifier_value:{type:'string'}, resolved_value:{type:'string'}, reason:{type:'string'} } } },
    confidence: { type: 'string' },
  },
};

log(`Outcomes extraction: ${jobs.length} papers, ${jobs.reduce((a,j)=>a+j.needed.length,0)} required rows.`);
function neededBlock(job){
  return job.needed.map((n,i)=>`  [${i+1}] table=${n.table} | comparison="${n.comparison}" | default Treatment="${n.treatment}" vs Control="${n.control}" | note: ${n.note}`).join('\n');
}

const results = await pipeline(
  jobs,
  (job) => agent(
`${BRIEF}

PAPER: id=${job.paper_id} | trial="${job.trial}" | NCT=${job.nct} | PMID(approx, verify)=${job.pmid}
DESIGN / ANCHORS: ${job.design}

SOURCE FILES (read all):
${job.files.map(f=>'  - '+f).join('\n')}

REQUIRED RESULTS (produce exactly one result object per item, echoing table+comparison):
${neededBlock(job)}

${FIELDS_DOC}
Return the PAPER object: paper_id, trial_name, nct, pmid (the real PubMed ID printed in the paper if visible, else "NA"), of_recommendation ("O"/"F"), results[], paper_flags[].`,
    { label: `extract:${job.paper_id}`, phase: 'Extract', schema: PAPER_SCHEMA, effort: 'high' }
  ),
  (extract, job) => {
    if (!extract) return null;
    return agent(
`${BRIEF}

You are the INDEPENDENT VERIFIER for paper id=${job.paper_id} (trial "${job.trial}").
Do NOT trust the first extractor. RE-OPEN and RE-READ the source files yourself and RE-DERIVE every value from
scratch, then reconcile against the extractor's draft below.

SOURCE FILES (read all again):
${job.files.map(f=>'  - '+f).join('\n')}
DESIGN / ANCHORS: ${job.design}

REQUIRED RESULTS (one object per item; echo table+comparison exactly):
${neededBlock(job)}

EXTRACTOR DRAFT (JSON to check, not to trust):
${JSON.stringify(extract)}

For each field: if your independent reading confirms the extractor, keep it. If it differs, use the value YOU can
prove with a snippet (record it in resolved_value). Fix HR direction (must be Treatment vs Control; invert if
needed), wrong arm assignment, wrong landmark/timepoint, wrong event/N denominators, and wrong endpoint mapping.
Fill any value the extractor left NA that IS actually reported. Keep "NA" where truly unreported. Re-confirm
of_recommendation (O=original/pivotal, F=long-term follow-up/update).

Return the VERIFY object: the FINAL reconciled paper object (paper_id, trial_name, nct, pmid, of_recommendation,
results[] with final values + provenance + flags, paper_flags[]), PLUS disagreements[] (every field you changed
from the extractor, with reason) and a one-line confidence note.`,
      { label: `verify:${job.paper_id}`, phase: 'Verify', schema: VERIFY_SCHEMA, effort: 'high' }
    );
  }
);

const final = results.filter(Boolean);
log(`Done: ${final.length}/${jobs.length} papers verified.`);
return { papers: final };
