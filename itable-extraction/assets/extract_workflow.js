export const meta = {
  name: 'itable-extract-verify',
  description: 'Dual extract + independent verify of evidence-table data from source publications',
  phases: [
    { title: 'Extract', detail: 'one extractor agent per study reads its sources' },
    { title: 'Verify', detail: 'independent verifier re-derives each value and reconciles' },
  ],
}

// Pass the config via the Workflow tool `args` (workflow scripts can't read files; the agents they
// spawn can). Expected shape:
//   args = {
//     guidePath: "/abs/_work/field_guide.md",
//     conventionsPath: "/abs/_work/conventions.md",
//     studies: [ { id, label, files:[abs...], arm_proposal, calibration? } ]
//   }
const { guidePath, conventionsPath, studies } = args

const CELL = { type: 'object', additionalProperties: false,
  properties: { col: { type: 'string' }, value: { type: 'string' }, source: { type: 'string' } },
  required: ['col', 'value', 'source'] }
const EXTRACT_SCHEMA = { type: 'object', additionalProperties: false,
  properties: {
    id: { type: 'string' }, n_arms: { type: 'integer' },
    arm_mapping: { type: 'object' },
    cells: { type: 'array', items: CELL },
    flags: { type: 'array', items: { type: 'string' } },
  }, required: ['id', 'n_arms', 'arm_mapping', 'cells', 'flags'] }
const VERIFY_SCHEMA = { type: 'object', additionalProperties: false,
  properties: {
    verdicts: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { col: { type: 'string' }, agree: { type: 'boolean' },
        corrected_value: { type: ['string', 'null'] }, note: { type: 'string' } },
      required: ['col', 'agree', 'corrected_value', 'note'] } },
    missing_cells: { type: 'array', items: CELL },
    overall_note: { type: 'string' },
  }, required: ['verdicts', 'missing_cells', 'overall_note'] }

function extractPrompt(s) {
  return [
    `You are a meticulous systematic-review data extractor. Extract data for ONE publication into a fixed`,
    `evidence-table schema.`,
    ``,
    `STUDY: id ${s.id} — ${s.label || ''}`,
    `STEP 1 — Read the rules and the column map (Read tool):`,
    `  - ${conventionsPath}   (value formats, missing-value rule, arm rule, output spec)`,
    `  - ${guidePath}         (column -> meaning, with arm slots)`,
    `STEP 2 — Read the SOURCE documents (the ONLY allowed sources):`,
    ...(s.files || []).map(f => `  - ${f}`),
    `  Use Bash 'pdftotext -layout "<file>" -' for text/tables; PyMuPDF for page-aware tables; the Read`,
    `  tool on specific PDF pages for figures/KM-curves; for .docx unzip word/document.xml and strip tags.`,
    s.calibration ? `STEP 3 — Calibrate conventions against this same-trial example row: ${s.calibration} (Read it).` : ``,
    `STEP ${s.calibration ? 4 : 3} — Determine arm mapping. Proposed (confirm vs the paper, flag changes): ${s.arm_proposal || '(infer from paper)'}`,
    `STEP ${s.calibration ? 5 : 4} — For EVERY value you can support from the sources, emit {col, value, source}.`,
    `  col = the column letter for the right variable AND arm slot. value = formatted per the conventions.`,
    `  source = page/table/figure + a short verbatim snippet. Omit anything not reported (it becomes the`,
    `  column's missing marker). Always fill the identifying/characteristic columns you can.`,
    `Return the StructuredOutput object. Be exhaustive but never fabricate; flag every judgment call.`,
  ].filter(Boolean).join('\n')
}

function verifyPrompt(s, ex) {
  return [
    `You are an INDEPENDENT verifier for systematic-review extraction. A first extractor produced values`,
    `for study ${s.id} (${s.label || ''}). Re-derive each value yourself from the SAME sources — do not`,
    `trust the extractor; check against the documents.`,
    `Read first: ${conventionsPath} and ${guidePath}.`,
    `SOURCES (only allowed):`, ...(s.files || []).map(f => `  - ${f}`),
    `Use pdftotext -layout / PyMuPDF / Read tool for figures / unzip for .docx.`,
    `EXTRACTOR OUTPUT:`, '```json', JSON.stringify(ex, null, 1), '```',
    `TASKS: (1) verify each cell's col (right variable+arm) and value vs source+conventions — emit a`,
    `verdict {col, agree, corrected_value, note}; agree=true & corrected_value=null when right; else give`,
    `the corrected value + cite the source. (2) Add values the extractor MISSED to missing_cells[] with`,
    `sources (esp. baseline tables, efficacy rates, adverse events). (3) overall_note: arm-mapping`,
    `correctness + population/timepoint caveats. Return the StructuredOutput object.`,
  ].join('\n')
}

const results = await pipeline(
  studies,
  (s) => agent(extractPrompt(s), { label: `extract:${s.id}`, phase: 'Extract', schema: EXTRACT_SCHEMA, effort: 'high' })
            .then(ex => ({ s, ex })),
  ({ s, ex }) => {
    if (!ex) { log(`extract failed for ${s.id}`); return null }
    return agent(verifyPrompt(s, ex), { label: `verify:${s.id}`, phase: 'Verify', schema: VERIFY_SCHEMA, effort: 'high' })
      .then(v => {
        const byCol = new Map()
        for (const c of ex.cells) byCol.set(c.col, { col: c.col, value: c.value, source: c.source })
        const changes = []
        if (v) {
          for (const verd of v.verdicts) {
            if (!verd.agree && verd.corrected_value != null && verd.corrected_value !== '') {
              const prev = byCol.get(verd.col)
              byCol.set(verd.col, { col: verd.col, value: verd.corrected_value,
                source: (prev?.source || '') + ' | VERIFIER: ' + verd.note })
              changes.push({ col: verd.col, from: prev?.value, to: verd.corrected_value, note: verd.note })
            }
          }
          for (const mc of v.missing_cells) {
            if (!byCol.has(mc.col)) {
              byCol.set(mc.col, { col: mc.col, value: mc.value, source: 'VERIFIER-ADDED: ' + mc.source })
              changes.push({ col: mc.col, from: null, to: mc.value, note: 'added by verifier' })
            }
          }
        }
        log(`${s.id}: ${ex.cells.length} extracted, ${changes.length} reconciled changes`)
        return { id: s.id, label: s.label, n_arms: ex.n_arms, arm_mapping: ex.arm_mapping,
          cells: [...byCol.values()], flags: ex.flags || [], verify_note: v?.overall_note || null,
          reconcile_changes: changes }
      })
  },
)
const out = results.filter(Boolean)
log(`DONE: ${out.length}/${studies.length} studies extracted+verified`)
return { studies: out }
