// Workflow: tag studies to guideline clinical questions.
// One classifier agent per study (reads the abstract; opens the full text only when
// the question-fit is ambiguous) -> one adjudicator that compiles the final matrix.
//
// Pass everything via `args` (workflow scripts can't read files; the agents they spawn
// can read the PDFs):
//   args = {
//     questions: [{ key:"CQ10", text:"<verbatim question>", scope:"<optional population/scope note>" }, ...],
//     rules:    "<free-text assignment rules: multi-assign, gatekeepers, direct-evidence standard, when to flag>",
//     studies:  [{ id:"12301", label:"TEXT+SOFT (Pagani 2023)", abstract:"<from sheet>", files:["/abs/a.pdf","/abs/b.pdf"] }, ...]
//   }
// Returns { classifications:[...], adjudication:{ matrix, perAssignmentRationale, judgmentCalls, summary } }.

export const meta = {
  name: 'study-question-tagging',
  description: 'Classify each study against guideline clinical questions, then adjudicate the final per-question assignment matrix',
  phases: [
    { title: 'Classify', detail: 'one agent per study reads its abstract/PDF and assigns questions' },
    { title: 'Adjudicate', detail: 'compile and reconcile the final per-question matrix' },
  ],
}

const Q = args.questions || []
const RULES = args.rules || ''
const STUDIES = args.studies || []

const QUESTION_BLOCK = Q.map(q =>
  `- ${q.key}: ${q.text}${q.scope ? `  [scope: ${q.scope}]` : ''}`).join('\n')

const KEYS = Q.map(q => q.key)

const CLASSIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['id', 'studyLabel', 'population', 'design', 'comparison', 'primaryEndpoint', 'assignedQuestions', 'readFullText', 'notes'],
  properties: {
    id: { type: 'string' },
    studyLabel: { type: 'string' },
    population: { type: 'string', description: 'who was enrolled (e.g. pre/postmenopausal), with brief justification' },
    design: { type: 'string', description: 'RCT design / phase / what was randomized' },
    comparison: { type: 'string', description: 'the randomized arms / contrast' },
    primaryEndpoint: { type: 'string' },
    assignedQuestions: {
      type: 'array',
      description: 'every question key this study provides DIRECT evidence for',
      items: {
        type: 'object', additionalProperties: false, required: ['key', 'rationale'],
        properties: {
          key: { type: 'string', description: 'one of: ' + KEYS.join(', ') },
          rationale: { type: 'string', description: 'one sentence: the specific comparison/finding that answers this question' },
        },
      },
    },
    readFullText: { type: 'boolean', description: 'true if you opened the PDF(s) beyond the abstract' },
    notes: { type: 'string', description: 'questions deliberately EXCLUDED and why; any borderline/ambiguous call to flag' },
  },
}

phase('Classify')
const classifications = (await parallel(STUDIES.map(s => () =>
  agent(
    `You are a systematic-review methodologist tagging ONE study to a guideline's clinical questions.

STUDY: ${s.label || s.id} (id ${s.id})

ABSTRACT (from the included-studies sheet):
${s.abstract || '(none provided — read the publication)'}

PUBLICATION FILES (read these ONLY if the abstract leaves the question-fit ambiguous — e.g. borderline
population, unclear which arm carries the effect, treatment-choice vs duration overlap, adverse-effect/
adherence relevance). Use the Read tool with a pages range for PDFs (these are short articles):
${(s.files && s.files.length) ? s.files.join('\n') : '(no files matched — rely on the abstract and flag this)'}

THE CLINICAL QUESTIONS:
${QUESTION_BLOCK}

ASSIGNMENT RULES:
${RULES}

Decide which question(s) this study provides DIRECT randomized evidence for. Confirm the population,
design, the randomized comparison, and the primary endpoint (these decide the fit). Assign every question
it genuinely answers; in notes, name the questions you deliberately excluded and why, and flag anything
genuinely ambiguous. Set readFullText truthfully.`,
    { label: `classify:${s.id}`, phase: 'Classify', schema: CLASSIFY_SCHEMA }
  )
))).filter(Boolean)

phase('Adjudicate')
const matrixProps = {}
for (const k of KEYS) matrixProps[k] = { type: 'array', items: { type: 'string' } }
const ADJ_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['matrix', 'perAssignmentRationale', 'judgmentCalls', 'summary'],
  properties: {
    matrix: { type: 'object', additionalProperties: false, required: KEYS, properties: matrixProps },
    perAssignmentRationale: {
      type: 'array',
      items: { type: 'object', additionalProperties: false, required: ['key', 'id', 'rationale'],
        properties: { key: { type: 'string' }, id: { type: 'string' }, rationale: { type: 'string' } } },
    },
    judgmentCalls: { type: 'array', items: { type: 'string' },
      description: 'genuinely ambiguous decisions the user should confirm (empty-question placements, near-miss inclusions/exclusions, contradictions between classifiers)' },
    summary: { type: 'string' },
  },
}

const adjudication = await agent(
  `You are the lead reviewer compiling the FINAL assignment of studies to guideline clinical questions.

THE CLINICAL QUESTIONS:
${QUESTION_BLOCK}

ASSIGNMENT RULES:
${RULES}

Per-study classifications (JSON):
${JSON.stringify(classifications, null, 2)}

Build matrix: for each question key, the list of study IDs that answer it. A study appears in EVERY
question it directly answers. Apply the rules strictly and consistently; reconcile any disagreement
between classifiers. A question with no qualifying study gets an empty array (do not force a fit).
Return the matrix, a one-line rationale per assignment, the list of judgment calls the user should
confirm, and a short summary.`,
  { label: 'adjudicate', phase: 'Adjudicate', schema: ADJ_SCHEMA }
)

return { classifications, adjudication }
