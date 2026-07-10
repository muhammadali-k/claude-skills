# Evaluation — abstract-review

Grounded in a real fixture: the **ASH ruxolitinib-combination NMA** review project — the author's original
abstract (`MF_ASH_Umair_V1.docx`), the reviewer's first round with tracked changes + 12 comments
(`MF_ASH_V2_MAK_tracked.docx`), and the author's revision answering those comments
(`MF_ASH_Umair_V4.docx`). The skill was distilled from performing the Version-4 re-review by hand and then
proving the engine reproduces it.

## Mechanical validation (engine correctness) — PASS

Run against the ASH fixture and a synthetic fresh document:

1. **Reproduction.** A declarative edit plan (10 tracked edits + 8 threaded comments) applied to pristine
   `MF_ASH_Umair_V4.docx` via `docx_review.py apply` produces an accepted-text render **byte-identical** to
   the hand-built delivered review, with all 8 new comments threaded to the correct parents
   (`reply->52/39/47/35/62/70` + 2 new anchored comments). ✔
2. **Reject-all invariant.** Rejecting every reviewer change in the output reproduces the original document
   text exactly — proof the review only *adds* reversible markup and never clobbers text. ✔
3. **Comment-range balance.** All 21 comments (13 pre-existing + 8 added) have exactly one
   start/end/reference and a body; no orphans. ✔
4. **Fresh-document path.** On a doc with **no** comment parts, adding a comment creates
   `comments.xml` + `commentsExtended/Ids/Extensible` + `people.xml`, registers all five content-type
   overrides and relationships, and the result opens in `python-docx` and passes both invariants. ✔
5. **Round-trip open.** Every produced `.docx` opens without repair in `python-docx`; zip integrity holds. ✔

These are exercised by `scripts/docx_review.py apply` (which auto-validates) and re-checkable with
`docx_review.py validate OUT.docx ORIG.docx`.

## Behavioral validation (review quality) — the fixture

The V4 re-review is the reference behavior. Against the author's revision the skill should, and the manual
pass did:
- **Catch the two consistency defects the revision introduced** by adding a fourth trial (parsaclisib):
  Introduction still said "Three Phase 3 trials" (→ Four); Conclusion still said "All three combinations
  improved SVR" after the fourth did not (→ "Three of the four... whereas parsaclisib did not"). Both were
  independently confirmed by adversarial refutation agents before editing.
- **Audit each prior comment** as resolved / partial / open / declined and reply in-thread — including
  answering the author's inline "How?" on the TSS sign convention, and accepting the author's reasoned
  decision to omit formal RoB/GRADE for a space-limited abstract.
- **Never edit an unverifiable number** — data-vintage and OS-provenance concerns were raised as comments,
  not tracked edits.
- **Respect the character limit** — accepted body 4,329 / 4,500 characters, reported with headroom.

`evals/evals.json` encodes these as gradeable cases for the skill-creator harness (fixture files are the
three ASH `.docx`; they are not committed — licensed/unpublished author content).

## Known limitations
- Text-anchored edits target a single run; a target spanning a run boundary or an existing tracked change
  raises a clear error (split it). This is a safety feature, not a silent failure.
- Research-type profiles cover evidence-synthesis, RCT, observational, other-clinical, and AI/ML; a design
  outside these falls back to the generic checklist in `references/method.md` (add a profile as needed).
- The engine edits `.docx` only. PDFs/Google Docs must be exported to `.docx` first.
