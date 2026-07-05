---
name: academic-pptx
description: Use this skill when creating academic presentations — journal clubs, lectures, grand rounds, conference talks, research talks, proposal defenses, fellowship/residency teaching, or any deck for a clinical, scientific, or scholarly audience. The defining requirement is that the deck must look like a careful academic presenter made it — publication-style restraint, a disciplined palette, generous whitespace, message-based slide titles — not like a generic AI-generated deck. Trigger phrases include "journal club", "grand rounds", "academic presentation", "lecture slides", "conference talk", "research talk", "doesn't look AI-generated", "looks academic", and any presentation request that mentions a scientific paper, clinical topic, research finding, or scholarly audience. Builds on the pptx skill.
---

# Academic Presentation Builder

## When to use this skill

Trigger this skill for any presentation request that names an academic, clinical, or scientific context: journal clubs, grand rounds, lectures, residency or fellowship teaching, research talks, lab meetings, conference presentations, proposal defenses, grant talks, scientific review presentations. Also trigger when the user explicitly says "doesn't look AI-generated", "academic style", "publication-quality slides", "restrained design", or similar.

Do **not** use this skill for marketing pitches, sales decks, status updates, or general-purpose internal slides — use the pptx skill alone for those. This skill exists because academic decks have a specific aesthetic (restraint, message-based titles, minimal decoration, color used to encode meaning rather than to decorate) that conflicts with the pptx skill's default "every slide needs a visual element / pick a bold palette" guidance.

## Prerequisites

Read `/mnt/skills/public/pptx/SKILL.md` and `/mnt/skills/public/pptx/pptxgenjs.md` first. This skill assumes you know the pptxgenjs API. The pptx skill's QA workflow (render → inspect → fix) applies in full.

When the pptx skill's design guidance conflicts with this skill, **this skill wins** for academic decks. Specifically: ignore the pptx skill's instructions to use bold color palettes, add a visual element to every slide, or use cream/warm-neutral backgrounds. Academic decks use white backgrounds, a restrained role-based palette, and text-only slides where appropriate.

## Required inputs — gather before building

Confirm these with the user. If something is missing and not inferable from context, ask once and proceed. Do not build a full deck on guesses.

| Input | Notes |
|---|---|
| Topic | The actual subject of the talk |
| Audience | Medical students / residents / fellows / clinicians / journal club / graduate students / conference |
| Duration | 10, 15, 30, 50 min — affects depth of speaker notes |
| Purpose | Teaching / journal club / research talk / proposal defense / conference / grand rounds |
| Key references | Optional — primary papers, DOIs, or citations |
| Presenter & affiliation | For title slide |
| Primary color | Default navy `#1D4E74`. Alternatives: muted teal `#0F766E`, maroon `#7F1D1D`, forest green `#14532D`, slate `#334155` |

If the user is a Mayo Clinic affiliate, default the primary to navy `#1D4E74`. If they specify their institution explicitly, ask whether to match institutional colors.

## Color philosophy — read this before touching the palette

The old version of this skill allowed exactly one accent color. That was too strict: well-made academic decks do use more than one color — but every color earns its place by carrying *meaning*, never decoration. The failure mode this skill prevents is the rainbow deck where each bullet, header, and box is a different hue for no reason. The fix is not "no color." It is **roles**.

There are four legitimate jobs for color in an academic deck. Assign every colored element to one of them:

1. **Primary (anchor).** One color, used for the title's accent word, slide-title emphasis where wanted, table header fills, the key data series, the single title-slide rule, and primary callout numerals. This is the deck's identity. ~60–70% of all non-text color.
2. **Secondary (support).** One color from the same family as the primary but clearly distinct in hue (navy + teal, maroon + dusty-rose, forest + olive). Used for the *second* element in a genuine pairing: the counterpart panel in a two-part schematic, the second series in a two-series chart. Never used just to add variety.
3. **Categorical (data only).** A small ordered set of up to four distinct hues, used **exclusively** to distinguish series or categories inside a chart, legend, or coded diagram. Never for prose, headers, panels, or chrome. The first two categorical hues are the primary and secondary; the rest are reserved sparingly.
4. **Semantic (valence only).** Green / amber / red, used **only** where the color states a true good / caution / bad judgment — readiness chips, up/down deltas, pass/fail flags. If you reach for red and it doesn't mean "bad," you've broken the rule. Whenever semantic color appears, add a one-line footnote stating the encoding.

Hard rules that still hold: white background always; body text is charcoal, not colored; secondary gray for sub-labels; no colored rule under slide titles; no full-width colored header/footer bars; no edge stripes on cards. The expansion from "one accent" to "roles" buys you legible multi-series charts, a two-tone schematic, and honest readiness coding — and nothing else.

A quick test before adding any colored element: *which of the four roles is this?* If the honest answer is "it just looks nicer," make it charcoal or gray instead.

## Design tokens — use these exact values

```javascript
const C = {
  bg:           "FFFFFF",   // white background — never change
  text:         "1F2937",   // charcoal primary text
  muted:        "6B7280",   // secondary gray (sub-labels, footnotes, trade-offs)
  faint:        "D1D5DB",   // table dividers and hairline rules
  panel:        "F4F6F9",   // very light neutral panel fill (use sparingly)

  primary:      "1D4E74",   // ROLE 1 — anchor (swap for user's choice)
  secondary:    "2E7D8A",   // ROLE 2 — support (recolor to match primary's family)
  primaryFaint: "E3ECF3",   // tint of primary for "selected/important" panel fills

  // ROLE 3 — categorical: charts/legends/coded diagrams ONLY. First two = primary, secondary.
  cat: ["1D4E74", "2E7D8A", "B08400", "7A5195"],

  // ROLE 4 — semantic: use ONLY for genuine good / caution / bad meaning.
  good: "2F7D4F",
  warn: "B45309",
  bad:  "9B2C2C",
};
const FONT = "Arial"; // default. Acceptable alternatives: Helvetica, Calibri, Cambria.
```

When the user picks a non-default primary, recolor `secondary`, `primaryFaint`, and `cat[0..1]` to stay in family. Suggested pairings:

| Primary | Secondary | Categorical 3rd / 4th |
|---|---|---|
| Navy `1D4E74` | Teal `2E7D8A` | `B08400` gold · `7A5195` plum |
| Maroon `7F1D1D` | Dusty rose `B05A6B` | `8A6D00` ochre · `3F6D58` pine |
| Forest `14532D` | Olive `6B8E23` | `9A6A00` amber · `2E6E8A` steel |
| Slate `334155` | Slate-teal `3B6B73` | `97700A` brass · `6B4E7A` mauve |

Keep `good` / `warn` / `bad` as-is regardless of primary — semantic color must stay recognizable.

## Typography

| Element | Size | Weight | Color |
|---|---|---|---|
| Title slide main title | 30 pt | bold | `C.text` (+ `C.primary` for the secondary line) |
| Slide title (every other slide) | 26–28 pt | bold | `C.text` |
| Eyebrow / kicker (optional, sparing) | 11 pt | bold, tracked | `C.primary` |
| Section heading inside a slide | 16–17 pt | bold | `C.primary` |
| Body text | 18–22 pt | regular | `C.text` |
| Secondary / table cell | 13–15 pt | regular | `C.text` or `C.muted` |
| Footnote / citation | 10–11 pt | italic | `C.muted` |

Never use text smaller than 16 pt except for footnote citations, table cells, and kickers.

Arial is wider than Calibri; long titles wrap. Design title boxes to handle 1- or 2-line wrap (see Layout invariants). If a title wraps to 3 lines, shorten it.

## Layout invariants (16:9 slide, 10" × 5.625")

- **Background:** `C.bg` (white). No textures, gradients, or dark themes.
- **Margins:** at least 0.5" from every slide edge.
- **Title box:** `x: 0.5, y: 0.4, w: 9.0, h: 1.0` at 28 pt bold. Sized for 1- or 2-line wrap.
- **Content start:** `y >= 1.55` to clear a one-line title; `y >= 1.6` is safe for two-line titles since content boxes start below the title box.
- **Footnote position:** `y: 5.25, h: 0.25` at 10 pt italic, color `C.muted`.
- **Alignment:** left-align body and lists. Center only the title-slide title and large stat callouts.

Use these helpers for every non-title slide:

```javascript
function addTitle(slide, text, opts = {}) {
  slide.addText(text, {
    x: 0.5, y: 0.4, w: 9.0, h: 1.0,
    fontSize: opts.size || 28, fontFace: FONT, bold: true,
    color: C.text, align: "left", valign: "top", margin: 0,
  });
}

function addFootnote(slide, text) {
  slide.addText(text, {
    x: 0.5, y: 5.25, w: 9.0, h: 0.25,
    fontSize: 10, fontFace: FONT, italic: true,
    color: C.muted, align: "left", margin: 0,
  });
}

// Optional eyebrow above a title — use sparingly, not on every slide.
function addKicker(slide, text) {
  slide.addText(text.toUpperCase(), {
    x: 0.5, y: 0.28, w: 9.0, h: 0.3,
    fontSize: 11, fontFace: FONT, bold: true, charSpacing: 2,
    color: C.primary, align: "left", valign: "top", margin: 0,
  });
}
```

## Slide structure — follow this flow

Build slides in this order. Omit pieces that don't fit, but maintain the flow.

1. **Title slide** — title (mixed coloring: charcoal then primary), small horizontal rule in primary (one only, never under slide titles elsewhere), presenter, affiliation in muted gray, date/venue.
2. **Agenda** — 3–5 numbered items. Two-digit numerals in primary, item text in charcoal.
3. **Why this matters** — opening hook with the clinical or scientific stake. Often paired with a large stat callout in primary.
4. **Background** (1–3 slides) — what is known, what gap remains. Use tables for multi-study comparisons; use schematics for conceptual contrasts (primary vs secondary panels).
5. **Main content / methods / evidence** — vary the layout: comparison table, two-column with schematic, rule-divided list. Do not repeat the same layout more than twice in a row.
6. **Results** — one chart per slide. Single-series charts use primary only; multi-series use the categorical set. Always add an `Interpretation:` line below the chart in 14 pt with primary on the label and charcoal on the sentence.
7. **Discussion / limitations** — 3–4 named limitations, each with a 1-line body in muted gray. Semantic readiness chips are appropriate here *if* color encodes a real judgment (with a footnote stating the encoding).
8. **Take-home points** — 3–5 numbered messages, large primary numerals, generous vertical spacing.
9. **Close** (optional) — thank you, contact, acknowledgments. Spare.

For short talks (10–15 min), skip the agenda and combine background into one slide. For long lectures (30–50 min), expand each section.

## Slide title discipline — the most important rule

Every non-title slide gets a **message-based title** that states the actual finding or argument. Generic section labels are forbidden.

| Forbidden | Required |
|---|---|
| Results | "External validation revealed a 0.07 C-statistic drop across institutions" |
| Methods | "LASSO selected 12 variables from a 67-mutation panel" |
| Background | "Static prognostic scores miss disease progression" |
| Discussion | "Clinical impact depends on workflow integration, not discrimination" |
| Introduction | "Delayed diagnosis remains the dominant barrier to timely treatment" |

The reader should be able to follow the argument by reading only the titles. (Agenda, Take-home points, and the closing slide are the only allowed generic titles.)

## Speaker notes — write how a person actually talks

Every slide gets speaker notes via `slide.addNotes(...)`. These are the single biggest "this was AI-generated" tell in an otherwise good deck, so they get special attention. The goal is notes that sound like the presenter muttering to themselves the night before — cues and reminders, not a polished script read aloud.

**The core problem to avoid: the smooth narrator voice.** AI-written notes are too even. Every sentence is complete and grammatical, every slide is the same length, every note opens with a signpost ("Here's the headline result," "This is the key slide," "Now let's turn to...") and closes with a tidy scripted transition ("...which brings us to," "...so let's look at"). Read four of them in a row and they have an identical rhythm. Real presenters don't talk like that.

Write notes that have these qualities instead:

- **Uneven length.** A dense results slide might get a short paragraph; a transition slide might get one line — *"Quick orienting slide. Don't belabor."* Don't pad every slide to the same size.
- **Fragments and asides are fine.** *"Pause on the 5× before moving on."* / *"Skip this if running short."* / *"This is the one to slow down on."* These read as human because they are how people actually cue themselves.
- **Cues to self, not prose for the audience.** Notes can include reminders the audience never hears: *"If someone asks about the 58% — the missingness is informative, don't pretend it's MCAR."* / *"Likely pushback here: why not just recalibrate? That's slide 8, defer it."*
- **Drop the signpost openings.** Don't start with "Here's…" / "This slide shows…" / "Now…". Just start with the substance, or with the cue.
- **Don't end every slide on a manufactured transition.** Some notes end mid-thought, some end on a cue, a few have a natural handoff. If you find a transition phrase on every single slide, you've written a script, not notes. Roughly one in three slides ending with a real transition is plenty.
- **Let opinion and emphasis show.** *"I think the gold-standard comparison is unfair, but I'll save that for Q&A."* A real presenter has takes; flat neutrality reads as machine-generated.
- **Vary how slides open across the deck.** Track your opening words — if three notes in a row start the same way, rewrite.

Length by format: 10–15 min talks get 2–4 sentences (or fewer — a one-line cue is allowed and often better). 30–50 min lectures get more room: a mechanism aside, a real example, the occasional audience prompt — but still uneven, still cue-like, never a uniform wall.

**Before/after to calibrate the voice:**

> ❌ *"Here's the headline result. Every machine-learning model beats the genomic benchmark, but the gains are modest — two to six hundredths of a C-statistic. This is the central tension of the talk. Whether that premium is worth it depends on what you give up, which brings us to the harder question of generalization."*

> ✅ *"The win is real but small — 2 to 6 hundredths, and the top three are basically tied. That's the whole tension of the talk in one chart. Don't oversell it. The 'is it worth it' question is really a generalization question, which is next."*

The first is grammatical, signposted, and ends on a scripted handoff — fine prose, obviously written. The second has a fragment, a cue to self ("Don't oversell it"), and a looser transition. Aim for the second.

Still avoid: "this slide shows X" phrasing, reading the bullets back verbatim, and the monologue tone where every slide is a tidy paragraph.

## Anti-patterns — must not appear

Verify the deck contains none of these before declaring complete:

- Accent line, colored rule, or underscore under a slide title (the single horizontal rule on the title slide is the only allowed exception)
- Full-width colored bars at the top or bottom of slides (headers, footers, ribbons)
- Vertical sidebar stripes or single-edge accent stripes on cards or content blocks
- A logo on every slide (title and closing only)
- Decorative icons, especially stethoscopes, DNA helices, doctor figures, "futuristic AI" graphics
- Stock medical photos
- Glow, drop shadow on text, gradient text, 3D effects
- Centered body paragraphs or lists
- More than two consecutive slides with identical layout
- Body text under 16 pt (footnote citations, table cells, kickers excepted)
- Borders around every text box
- Subtitle ribbons or marketing-deck flourishes on the title slide
- **Color used decoratively** — any colored element that doesn't map to one of the four roles (primary / secondary / categorical / semantic). Recolor it charcoal or gray.
- More than four categorical hues in a single chart; categorical hues anywhere outside charts/legends/coded diagrams
- Semantic colors (green/amber/red) used for non-valence purposes
- Cream / beige / pastel backgrounds (the pptx skill warns about these defaults — keep white)
- "Thin colored rule under every slide title" pattern (a hallmark AI tell)

## Working code patterns

The reference deck (`reference/output.pptx`, source in `reference/build.js`) is a 9-slide example demonstrating every pattern below, including the role-based palette. Read `reference/build.js` for full working code and adapt it rather than rewriting from scratch.

### Title slide

Two-color rich-text title block, small primary rule (the only rule in the deck), authorship in muted gray.

```javascript
slide.addText([
  { text: "Main Title Line", options: { color: C.text, breakLine: true } },
  { text: "Secondary Title Line", options: { color: C.primary } },
], {
  x: 0.7, y: 1.55, w: 8.8, h: 1.7,
  fontSize: 30, fontFace: FONT, bold: true,
  align: "left", valign: "top", margin: 0, paraSpaceAfter: 4,
});

// Single small horizontal rule — the only one allowed in the deck (uses primary)
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.7, y: 3.45, w: 0.7, h: 0.03,
  fill: { color: C.primary }, line: { type: "none" },
});

slide.addText([
  { text: "Presenter Name, Credentials", options: { fontSize: 16, color: C.text, breakLine: true } },
  { text: "Department / Affiliation",    options: { fontSize: 14, color: C.muted, breakLine: true } },
  { text: "Institution  ·  Lab / Group", options: { fontSize: 14, color: C.muted } },
], { x: 0.7, y: 3.7, w: 8.6, h: 1.0, fontFace: FONT, align: "left", margin: 0 });
```

### Agenda numerals

Two-digit numerals in primary, item text in charcoal.

```javascript
items.forEach((item, i) => {
  const y = 1.7 + i * 0.62;
  slide.addText(String(i + 1).padStart(2, "0"), {
    x: 0.8, y, w: 0.6, h: 0.5, fontSize: 16, fontFace: FONT, bold: true,
    color: C.primary, align: "left", valign: "middle", margin: 0,
  });
  slide.addText(item, {
    x: 1.5, y, w: 7.7, h: 0.5, fontSize: 20, fontFace: FONT,
    color: C.text, align: "left", valign: "middle", margin: 0,
  });
});
```

### Stat callout with supporting body

For a "Why this matters" slide. Body text left, large stat right in primary. No border — typography carries the weight.

```javascript
slide.addText([
  { text: "First sentence stating a fact.", options: { breakLine: true } },
  { text: " ", options: { fontSize: 10, breakLine: true } },
  { text: "Second sentence.", options: { breakLine: true } },
  { text: " ", options: { fontSize: 10, breakLine: true } },
  { text: "Third sentence.", options: {} },
], { x: 0.7, y: 1.6, w: 5.3, h: 3.4, fontSize: 19, fontFace: FONT,
     color: C.text, align: "left", valign: "top", paraSpaceAfter: 6, margin: 0 });

slide.addText("> 5×", {
  x: 6.3, y: 1.75, w: 3.1, h: 1.6,
  fontSize: 88, fontFace: FONT, bold: true,
  color: C.primary, align: "left", valign: "middle", margin: 0,
});
slide.addText("short label for the stat", {
  x: 6.3, y: 3.4, w: 3.1, h: 1.2,
  fontSize: 14, fontFace: FONT, color: C.muted, align: "left", valign: "top", margin: 0,
});
```

### Comparison table

Primary-filled header row, light-gray dividers, no heavy borders. Bold names, italic muted trade-offs.

```javascript
const headerOpts = { fill: { color: C.primary }, color: "FFFFFF", bold: true,
                     fontSize: 14, fontFace: FONT, align: "left", valign: "middle" };
const cellB = { fontSize: 13, fontFace: FONT, color: C.text, bold: true, align: "left", valign: "middle" };
const cell  = { fontSize: 13, fontFace: FONT, color: C.text, align: "left", valign: "middle" };
const cellM = { fontSize: 13, fontFace: FONT, color: C.muted, italic: true, align: "left", valign: "middle" };

const rows = [
  [{ text: "Model", options: headerOpts }, { text: "How it handles risk", options: headerOpts }, { text: "Trade-off", options: headerOpts }],
  [{ text: "Penalized Cox", options: cellB }, { text: "Linear hazards, LASSO selection", options: cell }, { text: "Interpretable; misses interactions", options: cellM }],
  // ... more rows
];

slide.addTable(rows, {
  x: 0.5, y: 1.6, w: 9.0,
  colW: [2.3, 3.9, 2.8], // sum should equal w
  rowH: 0.62,
  border: { type: "solid", pt: 0.5, color: C.faint },
  align: "left", valign: "middle",
});
```

### Two-column schematic (primary vs secondary roles)

For a conceptual contrast or an input→output flow. The neutral side uses `C.panel`; the "selected / important" side uses `C.primaryFaint` with a `C.primary` border. This is the canonical use of the secondary role — a genuine pairing, not variety for its own sake.

```javascript
// Left panel — neutral
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.7, y: 1.7, w: 3.9, h: 2.9,
  fill: { color: C.panel }, line: { color: C.faint, width: 0.75 },
});
slide.addText("INPUT", { x: 0.95, y: 1.95, w: 3.4, h: 0.3, fontSize: 12, fontFace: FONT,
  bold: true, charSpacing: 2, color: C.muted, align: "left", margin: 0 });
// ... left content

// Arrow in primary
slide.addShape(pres.shapes.RIGHT_ARROW, {
  x: 4.75, y: 2.85, w: 0.55, h: 0.55, fill: { color: C.primary }, line: { type: "none" },
});

// Right panel — emphasized
slide.addShape(pres.shapes.RECTANGLE, {
  x: 5.45, y: 1.7, w: 3.85, h: 2.9,
  fill: { color: C.primaryFaint }, line: { color: C.primary, width: 1 },
});
slide.addText("RETAINED", { x: 5.7, y: 1.95, w: 3.4, h: 0.3, fontSize: 12, fontFace: FONT,
  bold: true, charSpacing: 2, color: C.primary, align: "left", margin: 0 });
// ... right content
```

### Single-series bar chart with interpretation

Single-color bars (primary), no 3D, light value-axis gridlines, data labels on bars. Always followed by an `Interpretation:` line.

```javascript
slide.addChart(pres.charts.BAR, [{
  name: "C-statistic (validation)",
  labels: ["MIPSS70+ v2.0", "Penalized Cox", "Random Survival Forest", "XGBoost-Cox", "DeepSurv"],
  values: [0.72, 0.74, 0.76, 0.77, 0.78],
}], {
  x: 0.7, y: 1.6, w: 8.6, h: 2.9,
  barDir: "col",
  chartColors: [C.primary],
  chartArea: { fill: { color: C.bg }, border: { color: C.bg, pt: 0 } },
  plotArea:  { fill: { color: C.bg }, border: { color: C.bg, pt: 0 } },
  catAxisLabelFontSize: 11, catAxisLabelColor: C.text, catAxisLabelFontFace: FONT,
  valAxisLabelFontSize: 10, valAxisLabelColor: C.muted, valAxisLabelFontFace: FONT,
  valAxisMinVal: 0.65, valAxisMaxVal: 0.82, valAxisMajorUnit: 0.05,
  valGridLine: { color: "E5E7EB", size: 0.5, style: "solid" },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd",
  dataLabelColor: C.text, dataLabelFontSize: 11, dataLabelFontFace: FONT,
  dataLabelFormatCode: "0.00",
  barGapWidthPct: 55, showLegend: false,
});

slide.addText([
  { text: "Interpretation:  ", options: { bold: true, color: C.primary } },
  { text: "absolute gains are modest...", options: { color: C.text } },
], { x: 0.7, y: 4.6, w: 8.6, h: 0.6, fontSize: 14, fontFace: FONT, align: "left", valign: "top", margin: 0 });
```

### Multi-series chart (categorical role)

For comparing two or three series — the genuine reason to go beyond one color. Use `C.cat` in order, a bottom legend, and no data labels (they collide when series overlap). Two series → use `cat[0..1]` (= primary, secondary). Three or four → add `cat[2..3]`. Never exceed four.

```javascript
slide.addChart(pres.charts.LINE, [
  { name: "Internal CV",    labels: ["A","B","C","D","E"], values: [0.74,0.78,0.81,0.82,0.83] },
  { name: "Site A (n=402)", labels: ["A","B","C","D","E"], values: [0.72,0.75,0.76,0.77,0.76] },
  { name: "Site B (n=331)", labels: ["A","B","C","D","E"], values: [0.71,0.73,0.74,0.74,0.73] },
], {
  x: 0.7, y: 1.6, w: 8.6, h: 2.85,
  chartColors: [C.cat[0], C.cat[1], C.cat[2]],
  lineSize: 2.5, lineSmooth: false,
  chartArea: { fill: { color: C.bg }, border: { color: C.bg, pt: 0 } },
  plotArea:  { fill: { color: C.bg }, border: { color: C.bg, pt: 0 } },
  catAxisLabelFontSize: 11, catAxisLabelColor: C.text, catAxisLabelFontFace: FONT,
  valAxisLabelFontSize: 10, valAxisLabelColor: C.muted, valAxisLabelFontFace: FONT,
  valAxisMinVal: 0.68, valAxisMaxVal: 0.85, valAxisMajorUnit: 0.05,
  valGridLine: { color: "E5E7EB", size: 0.5, style: "solid" },
  catGridLine: { style: "none" },
  showLegend: true, legendPos: "b", legendColor: C.text, legendFontSize: 11, legendFontFace: FONT,
  showValue: false,
});
// Follow with the same Interpretation: line pattern as the bar chart.
```

### Named limitations with semantic chips (semantic role — optional)

For discussion/limitations. Each row gets a readiness chip whose color states a real judgment, plus a footnote making the encoding explicit. **Only use this when color genuinely means good/caution/bad** — otherwise use plain bold labels in `C.primary`.

```javascript
const limits = [
  { tag: "Calibration",     color: C.warn, body: "Predicted risks drifted at external sites; needs recalibration." },
  { tag: "Data capture",    color: C.bad,  body: "Full panels available for only 58% of the cohort; missingness not random." },
  { tag: "Actionability",   color: C.warn, body: "A sharper estimate only matters at a transplant or trial decision point." },
  { tag: "Reproducibility", color: C.good, body: "Code and weights released, so external recalibration is feasible." },
];
limits.forEach((l, i) => {
  const y = 1.65 + i * 0.83;
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.7, y: y + 0.02, w: 1.85, h: 0.42, rectRadius: 0.06,
    fill: { color: l.color }, line: { type: "none" },
  });
  slide.addText(l.tag, { x: 0.7, y: y + 0.02, w: 1.85, h: 0.42, fontSize: 12, fontFace: FONT,
    bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
  slide.addText(l.body, { x: 2.75, y: y - 0.02, w: 6.55, h: 0.7, fontSize: 14, fontFace: FONT,
    color: C.text, align: "left", valign: "top", margin: 0, lineSpacingMultiple: 1.05 });
});
addFootnote(slide, "Chip color reflects readiness: amber = needs work, red = blocking gap, green = addressed.");
```

If a limitations slide isn't a readiness judgment, drop the chips and use plain bold `C.primary` labels with muted-gray bodies — color is not mandatory here.

### Numbered take-home points

Large primary numerals, body text wraps in charcoal.

```javascript
const points = ["Message one.", "Message two.", "Message three.", "Message four if needed."];
points.forEach((p, i) => {
  const y = 1.6 + i * 0.85;
  slide.addText(String(i + 1), {
    x: 0.7, y, w: 0.6, h: 0.6, fontSize: 28, fontFace: FONT, bold: true,
    color: C.primary, align: "left", valign: "top", margin: 0,
  });
  slide.addText(p, {
    x: 1.4, y: y + 0.04, w: 8.0, h: 0.75, fontSize: 18, fontFace: FONT,
    color: C.text, align: "left", valign: "top", margin: 0, lineSpacingMultiple: 1.05,
  });
});
```

## Build workflow

1. **Gather inputs.** Confirm topic, audience, duration, purpose, primary color. Ask once for anything missing.
2. **Outline first.** Before generating code, write the slide sequence: title → agenda → ... → take-homes. Show the user message-based titles for each slide and confirm before building, unless the request is short or the topic is unambiguous.
3. **Generate the .pptx** using pptxgenjs and the patterns above. Drop in the full `const C` token block; recolor `secondary` / `primaryFaint` / `cat[0..1]` to match a non-default primary.
4. **Render to images** via the pptx skill's QA workflow (`soffice` → `pdftoppm`).
5. **Visually inspect every slide.** Common defects, in order of frequency:
   - **Title-content collision** when a 28 pt title wraps to 2 lines in Arial. Fix by keeping content `y >= 1.6`, or shortening the title.
   - **Text overflow** past container bounds — most often on the title slide. Fix by sizing the text box for wrap.
   - **Element overlap** when adjusting spacing without re-checking neighbors.
   - **Color-role violations** — scan for any colored element that isn't primary/secondary/categorical/semantic, and for categorical hues leaking outside charts. Recolor to charcoal/gray.
6. **One fix-and-verify cycle.** Don't chase sub-pixel polish.
7. **Save to `/mnt/user-data/outputs/`** and call `present_files`.

## Reference example

`reference/build.js` is a complete 9-slide deck on "Machine Learning for Risk Stratification in Myeloproliferative Neoplasms." It demonstrates every pattern in this skill under the role-based palette — title slide, agenda, stat callout, comparison table, two-column schematic (primary/secondary), single-series chart, multi-series chart (categorical), named limitations with semantic chips, numbered take-homes. Read it as a working template and adapt rather than rewriting from scratch.

`reference/output.pptx` is the rendered file from that code.
