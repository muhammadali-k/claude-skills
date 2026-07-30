export const meta = {
  name: 'itable-two-reviewer-extract',
  description: 'Extract evidence-table data from source publications via two independent reviewers plus a senior adjudicator who re-derives every value',
  phases: [
    { title: 'Reviewer A', detail: 'first independent reviewer reads the sources and emits every supportable cell with provenance' },
    { title: 'Reviewer B', detail: 'second independent reviewer, different model, does the same WITHOUT seeing reviewer A' },
    { title: 'Senior adjudication', detail: 'senior reviewer re-derives every value from source, then reconciles against both drafts' },
  ],
}

// ---------------------------------------------------------------------------
// Pass the config via the Workflow tool `args` (workflow scripts can't read
// files; the agents they spawn can). Expected shape:
//   args = {
//     guidePath: "/abs/_work/field_guide.md",
//     conventionsPath: "/abs/_work/conventions.md",
//     studies: [ { id, label, files:[abs...], arm_proposal, calibration? } ],
//     models: { a: 'opus', b: 'sonnet', senior: 'opus' }        // optional
//   }
//
// The senior adjudicator is pinned to Opus rather than inheriting the session
// model. Adjudication means reading verbatim clinical trial text and quoting it
// back; models with heavier response filtering can decline or soften that, and a
// senior that hedges is worse than useless because everything downstream trusts
// it. Pin it, don't inherit it.
// ---------------------------------------------------------------------------
const { guidePath, conventionsPath, studies } = args
// Project controlled node vocabulary. A workflow script cannot read files; the agents it spawns can,
// so all three roles are handed the path and read it themselves. Without it each agent writes whatever
// wording it read off the page and netmeta turns every spelling into its own node.
const vocabularyPath = args.vocabularyPath || null
const MODELS = Object.assign({ a: 'opus', b: 'sonnet', senior: 'opus' }, args.models || {})

const CELL = { type: 'object', additionalProperties: false,
  properties: { col: { type: 'string' }, value: { type: 'string' }, source: { type: 'string' } },
  required: ['col', 'value', 'source'] }

// Both reviewers return exactly the same shape. Neither knows the other exists.
const REVIEW_SCHEMA = { type: 'object', additionalProperties: false,
  properties: {
    id: { type: 'string' }, n_arms: { type: 'integer' },
    arm_mapping: { type: 'object' },
    cells: { type: 'array', items: CELL },
    flags: { type: 'array', items: { type: 'string' } },
  }, required: ['id', 'n_arms', 'arm_mapping', 'cells', 'flags'] }

const SENIOR_SCHEMA = { type: 'object', additionalProperties: false,
  properties: {
    id: { type: 'string' }, n_arms: { type: 'integer' },
    arm_mapping: { type: 'object' },
    cells: { type: 'array', items: CELL },
    flags: { type: 'array', items: { type: 'string' } },
    adjudications: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { col: { type: 'string' }, value_a: { type: 'string' }, value_b: { type: 'string' },
        senior_value: { type: 'string' }, agreed_with: { type: 'string', enum: ['A', 'B', 'both', 'neither'] },
        reason: { type: 'string' } },
      required: ['col', 'value_a', 'value_b', 'senior_value', 'agreed_with', 'reason'] } },
    unresolved: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { col: { type: 'string' }, why: { type: 'string' } },
      required: ['col', 'why'] } },
    confidence: { type: 'string' },
  }, required: ['id', 'n_arms', 'arm_mapping', 'cells', 'flags', 'adjudications', 'unresolved', 'confidence'] }

// ---------------------------------------------------------------------------
// Concordance is computed in plain code, not by an agent. It is a RECORDED
// QUALITY METRIC, not a gate: the senior re-derives every value regardless of
// whether the two reviewers agreed. Agreement between two models tells you how
// legible the value was in the source, not whether it is correct.
// ---------------------------------------------------------------------------
function norm(v) {
  if (v === null || v === undefined) return 'NA'
  const s = String(v).trim()
  if (s === '' || /^(na|n\/a|nr|not reported|none)$/i.test(s)) return 'NA'
  const num = s.replace(/[,\s]/g, '')
  if (/^-?\d*\.?\d+%?$/.test(num)) {
    const f = parseFloat(num.replace('%', ''))
    if (!Number.isNaN(f)) return String(Math.round(f * 1000) / 1000)
  }
  return s.toLowerCase().replace(/[\s.,;:()\[\]-]+/g, ' ').trim()
}

function compareReviews(a, b) {
  const out = { total_fields: 0, concordant: 0, discordant: 0, rate: null,
    cols_only_in_a: [], cols_only_in_b: [], discordant_items: [],
    n_arms: { a: a?.n_arms ?? null, b: b?.n_arms ?? null, concordant: false },
    arm_mapping_concordant: false }
  if (!a || !b) { out.note = !a && !b ? 'both reviewers failed' : `only reviewer ${a ? 'A' : 'B'} returned`; return out }

  out.n_arms.concordant = a.n_arms === b.n_arms
  out.arm_mapping_concordant = JSON.stringify(Object.entries(a.arm_mapping || {}).map(([k, v]) => [k, norm(v)]).sort())
    === JSON.stringify(Object.entries(b.arm_mapping || {}).map(([k, v]) => [k, norm(v)]).sort())

  const ma = new Map((a.cells || []).map(c => [c.col, c]))
  const mb = new Map((b.cells || []).map(c => [c.col, c]))
  for (const k of ma.keys()) if (!mb.has(k)) out.cols_only_in_a.push(k)
  for (const k of mb.keys()) if (!ma.has(k)) out.cols_only_in_b.push(k)

  // A cell one reviewer emitted and the other omitted is a real disagreement:
  // one of them read a value the other declared absent.
  const allCols = new Set([...ma.keys(), ...mb.keys()])
  for (const col of allCols) {
    const va = norm(ma.get(col)?.value), vb = norm(mb.get(col)?.value)
    out.total_fields++
    if (va === vb) out.concordant++
    else { out.discordant++; out.discordant_items.push({ col, a: ma.get(col)?.value ?? '(omitted)', b: mb.get(col)?.value ?? '(omitted)' }) }
  }
  out.rate = out.total_fields ? Math.round((out.concordant / out.total_fields) * 1000) / 1000 : null
  return out
}

// ---------------------------------------------------------------------------
function reviewerPrompt(s) {
  return [
    `You are a meticulous systematic-review data extractor and an INDEPENDENT REVIEWER. Extract data for ONE`,
    `publication into a fixed evidence-table schema.`,
    ``,
    `Another reviewer is extracting this same publication separately. You will never see their work and they`,
    `will never see yours. Do not try to guess what they would say or hedge toward a "safe" answer - report`,
    `exactly what YOU can prove from these sources. Your independence is the entire point: if you converge on`,
    `a wrong value because you were anchored, the check fails.`,
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
    vocabularyPath ? `STEP ${s.calibration ? 6 : 5} — ARM LABELS ARE A CONTROLLED VOCABULARY. Read ${vocabularyPath} and emit ONLY canonical labels: UPPERCASE 3-5 chars, combinations joined by a bare '+' with NO SPACES (NIVO+IPI, never 'NIVO + IPI' or 'NIVO plus IPI'), component order exactly as the vocabulary's combinations list gives it, the pooled comparator as its single label whatever the trial called it, and dose/duration/setting variants hyphen-suffixed (SOR-1Y, PAZO-600, NIVO-PERI). An ACTIVE control arm takes that regimen's own label, not the comparator label. Where the paper's wording differs, use the vocabulary's aliases. Where no alias exists, FLAG it - never invent a label. netmeta joins arms by string equality, so one invented spelling becomes a second node and the network fault is invisible in the sheet.` : ``,
    `Return the StructuredOutput object. Be exhaustive but never fabricate; flag every judgment call.`,
  ].filter(Boolean).join('\n')
}

function seniorPrompt(s, a, b, conc) {
  const disc = conc.discordant_items.length
    ? conc.discordant_items.map(d => `  - ${d.col}:  A="${d.a}"  vs  B="${d.b}"`).join('\n')
    : '  (none - the two reviewers agreed on every cell; this does NOT mean they are right)'
  const notes = [
    conc.n_arms.concordant ? '' : `  Arm-count disagreement: A=${conc.n_arms.a} vs B=${conc.n_arms.b}`,
    conc.arm_mapping_concordant ? '' : `  Arm-mapping disagreement - resolve this FIRST, it re-slots every per-arm value.`,
  ].filter(Boolean).join('\n')

  return [
    `You are the SENIOR REVIEWER for study ${s.id} (${s.label || ''}). Two reviewers extracted this study`,
    `independently. Your job is NOT to pick a winner between them.`,
    ``,
    `WORK IN THIS ORDER, AND DO NOT DEVIATE:`,
    `STEP 1. Read ${conventionsPath} and ${guidePath}, then open and read EVERY source file below IN FULL,`,
    `        from scratch, BEFORE you look at either draft. Render and read figures - many values exist only`,
    `        as images that a text dump cannot surface.`,
    `STEP 2. Derive EVERY value yourself from what you just read, with its own provenance. Every value,`,
    `        including ones the two reviewers agreed on. Agreement between two models means a value was easy`,
    `        to read, not that it is correct - two readers can make the same mistake for the same reason.`,
    `STEP 3. ONLY THEN compare your own derivation against the two drafts below, and record an adjudication`,
    `        for every cell where any of the three of you differ.`,
    ``,
    `SOURCES (only allowed, read all again in full):`, ...(s.files || []).map(f => `  - ${f}`),
    `Proposed arm mapping (confirm against the paper): ${s.arm_proposal || '(infer from paper)'}`,
    ``,
    `--- Reviewer A draft (evidence about legibility, NOT an authority) ---`, '```json', JSON.stringify(a, null, 1), '```',
    `--- Reviewer B draft (same status) ---`, '```json', JSON.stringify(b, null, 1), '```',
    `--- Where the two reviewers disagreed (${conc.discordant}/${conc.total_fields} cells; concordance ${conc.rate}) ---`,
    disc, notes,
    ``,
    `OUTPUT`,
    `- cells[]: YOUR final values, each with your own provenance. These are what get written to the sheet.`,
    `  Include values BOTH reviewers missed - being exhaustive is part of the job, not just adjudicating.`,
    `- arm_mapping / n_arms: your own determination.`,
    `- adjudications[]: one entry for EVERY cell where you differ from A, from B, or where A and B differed`,
    `  from each other. Record value_a, value_b, your senior_value, agreed_with ("A", "B", "both" when all`,
    `  three match and you are logging it anyway, or "neither" when you overrode both), and a reason citing`,
    `  the source. Use "(omitted)" for a value a reviewer did not emit.`,
    `- unresolved[]: any cell you CANNOT settle from these sources - genuinely ambiguous printing, a figure`,
    `  too coarse to read, a contradiction between main text and supplement. Do NOT invent a resolution and`,
    `  do NOT split the difference; list it here so a human decides, and omit the cell from cells[].`,
    `  An honest unresolved entry is a correct outcome. A fabricated resolution is the worst outcome.`,
    `- confidence: one line on how much of this study's data you consider settled.`,
  ].join('\n')
}

const results = await pipeline(
  studies,
  (s) => parallel([
    () => agent(reviewerPrompt(s), { label: `A:${s.id}`, phase: 'Reviewer A', schema: REVIEW_SCHEMA, effort: 'high', model: MODELS.a }),
    () => agent(reviewerPrompt(s), { label: `B:${s.id}`, phase: 'Reviewer B', schema: REVIEW_SCHEMA, effort: 'high', model: MODELS.b }),
  ]),
  (pair, s) => {
    const [a, b] = pair || []
    if (!a && !b) { log(`${s.id}: BOTH reviewers failed - no senior pass, study dropped`); return null }
    const conc = compareReviews(a, b)
    if (!a || !b) log(`${s.id}: only one reviewer returned - senior runs as a single independent extraction`)
    else log(`${s.id}: concordance ${conc.concordant}/${conc.total_fields} (${conc.rate}), ${conc.discordant} discordant cells`)
    const opts = { label: `senior:${s.id}`, phase: 'Senior adjudication', schema: SENIOR_SCHEMA, effort: 'high' }
    if (MODELS.senior) opts.model = MODELS.senior
    return agent(seniorPrompt(s, a, b, conc), opts).then(sr => {
      if (!sr) { log(`${s.id}: senior failed`); return null }
      log(`${s.id}: senior emitted ${sr.cells.length} cells, ${sr.adjudications.length} adjudications, ${sr.unresolved.length} unresolved`)
      return { id: s.id, label: s.label, n_arms: sr.n_arms, arm_mapping: sr.arm_mapping,
        cells: sr.cells, flags: sr.flags || [], confidence: sr.confidence,
        adjudications: sr.adjudications, unresolved: sr.unresolved,
        concordance: conc, reviewer_a: a || null, reviewer_b: b || null }
    })
  },
)

const out = results.filter(Boolean)

const totals = out.reduce((acc, p) => {
  acc.fields += p.concordance.total_fields
  acc.concordant += p.concordance.concordant
  acc.discordant += p.concordance.discordant
  acc.adjudications += p.adjudications.length
  acc.senior_overrode_both += p.adjudications.filter(x => x.agreed_with === 'neither').length
  acc.unresolved += p.unresolved.length
  return acc
}, { fields: 0, concordant: 0, discordant: 0, adjudications: 0, senior_overrode_both: 0, unresolved: 0 })
totals.vocabulary_enforced = Boolean(vocabularyPath)
totals.concordance_rate = totals.fields ? Math.round((totals.concordant / totals.fields) * 1000) / 1000 : null

log(`DONE: ${out.length}/${studies.length} studies.`)
log(`Reviewer concordance ${totals.concordant}/${totals.fields} (${totals.concordance_rate}).`)
log(`Senior overrode BOTH reviewers on ${totals.senior_overrode_both} cell(s) - these are the values a two-reviewer-only design would have gotten wrong.`)
if (totals.unresolved) log(`${totals.unresolved} cell(s) need a human decision - see unresolved[] per study.`)
if (!vocabularyPath) log(`WARNING: no vocabularyPath supplied - arm labels are UNVALIDATED. Run qc.py with --vocabulary before these labels reach any analysis sheet.`)

return { studies: out, run_metrics: totals }
