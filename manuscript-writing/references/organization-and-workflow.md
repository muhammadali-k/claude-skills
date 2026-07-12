# Organization and workflow

How Khan organizes a manuscript project — the artifact-level and process-level habits, not the prose. Read this when setting up a new manuscript, structuring an existing draft, or preparing a draft for submission. The user asked specifically for "manuscript organization AND writing" — this file is the organization half.

## The build order (skeleton → tables → prose → abstract)

1. **Start from a reserved-space skeleton, not prose.** Lay down all top-level headers as empty blocks — `INTRODUCTION`, `[BACKGROUND AND SIGNIFICANCE]` (AI/methods only), `MATERIALS AND METHODS`, `RESULTS`, `DISCUSSION`, `CONCLUSION`, `LIMITATIONS`, `REFERENCES`, `TABLES`, `FIGURES` — plus front/back-matter blocks: Running Title, Short Title, Key Points, Keywords, Conflicts of Interest, Funding, Acknowledgments, Authorship Contributions, Data/Code Availability. **Print the housekeeping targets at the top**: abstract word count vs limit, manuscript word count, figure/reference counts, required citation format.

2. **Pick the section-label scheme and citation style up front, to match the target journal.** This is journal-dependent, not personal — decide once so the whole draft stays consistent:
   - Plain bold **Background / Methods / Results / Conclusions**, **or**
   - European Urology **numbered decimal sections** (`1.`, `2.1`, `2.2`, …), **or**
   - the venue's own set.
   - Citation format: AMA superscript vs bracketed numerals vs Vancouver parenthetical — commit and hold it. Don't switch citation style mid-draft.

3. **Version-stamp the filename**, and embed the venue where relevant: `…_V6`, `_V11`, `EHA24`, `ASCOGU25`, `TXGI2026`. Each new pass is a new version so iteration is legible in the file list. (This matches his actual Dropbox habit — `mUC_Manuscript_V6_PS_revised`, `V11_PARPi`, `TXGI2026_abstract_Khan`.)

4. **Build tables and exhibits first, then write prose against them.** Draft Table 1 (baseline/cohort), the results/effects tables, and the Summary-of-Findings tables **before** the Results narrative, so every quantitative sentence can be tethered to a specifically numbered exhibit as you write. Push detailed breakdowns into a **heavily indexed supplement** (Supplementary Tables/Figures S1–Sn).

5. **Write Methods as an ordered pipeline and make Results run exactly parallel to it.** Give each Methods step its own labeled subsection in fixed order (guideline statement → search → selection → extraction + RoB → statistics [pairwise before network] → subgroup/sensitivity → GRADE/SoF; or the informatics processing stages), then **title each Results subsection identically** so a variable is trackable from method to result by name.

6. **Draft the Introduction funnel last-paragraph-first.** Write the *"To address this gap, we…"* thesis+roadmap sentence, then build the three preceding paragraphs **backward** from it (opening statistic/pressure → why it matters → prior work and its gap). Enumerate open questions *Firstly/Secondly/Thirdly*.

7. **Write the Discussion to its fixed arc** (see `section-playbook.md`): one-sentence self-summary → *"We conducted…"* recap → enumerated implications with mechanistic context → literature comparison → enumerated Strengths → quarantined Limitations (each paired with a mitigation) → Future Directions vision paragraph. Then write the standalone **Conclusion** as a compact recap ending on the validation/NMA caveat.

8. **Derive the abstract from the finished manuscript, last** — not before it. The abstract Conclusion paraphrases the manuscript Conclusion; the standing caveat must match. Choose the abstract heading set for the venue and, for conferences, append one results Table with a full caption and abbreviation key. (See `abstracts.md`.)

## Placeholder discipline while drafting

Mark gaps with his own tokens and **never fabricate**: pending citations `(X)`, pending numbers `XX%` / `$XX` / `202X`, pending IRB `IRBXX-XXXX`, and inline `NOTE TO ED:` annotations for verification tasks. **Keep a running checklist of every placeholder** and clear them all (verify each reference, fill each number) before submission. Listing outstanding placeholders at the end of a drafted section is the expected hand-off.

## Legends and exhibits

Write figure/table legends as **full explanatory paragraphs that re-state the takeaway in prose** (not just describe the graphic). Define every abbreviation in an **alphabetized `Abbreviations:` line**. Note calculation conventions (e.g. how absolute risk per 1000 was derived). Use **lettered sub-panels** `(a)/(b)` with matching lettered footnotes.

## Provenance and collaboration scaffolding — state it explicitly

- **Reviewer workflow:** two independent reviewers by initials with a named third-reviewer tiebreak.
- **Credits:** librarian and PI credited in the search sentence.
- **Exact provenance:** software version numbers, PMIDs, cohort counts, model settings (temperature, zero-shot), and search cutoff dates.
- **For living reviews:** foreground the interactive website URL, the weekly auto-update, and an *"as of [date]"* currency statement.
- **Collaboration reality:** he works in shared Dropbox/Word with co-authors, so expect tracked-changes/conflicted-copy artifacts and reviewer-initialed filenames; keep a single clean master and reconcile deliberately.

## End-of-draft copyedit pass

Do a **dedicated copyedit pass at the end** targeting his recurring slips — these survive many versions unless hunted deliberately:

- Doubled words (*"ATM mutations ATM mutations"*), run-together words (*"performednetwork", "withing"*), dropped articles.
- Duplicated pasted paragraphs or figure legends.
- Mixed *Fig.* vs *Figure* cross-references.
- Inconsistent CI delimiters (semicolon vs comma) → standardize on semicolons.
- Mixed dispersion notation (*± SD* vs *(SD = )*) → one per manuscript.
- Recurring misspellings (*Certainity → Certainty, continuosly → continuously*).
- **Left-in scaffolding**: clear all `(X)`, `XX%`/`$XX`/`202X`, `IRBXX-XXXX`, and `NOTE TO ED` annotations; verify every reference; confirm citation style is uniform throughout.

## Quick project checklist

- [ ] Skeleton with all headers + front/back matter + housekeeping targets at top
- [ ] Journal section-label scheme + citation style chosen and applied throughout
- [ ] Filename version-stamped (`_Vn`, venue tag)
- [ ] Tables/exhibits + supplement built before Results prose
- [ ] Methods subsections in fixed order; Results subsections titled identically
- [ ] Results are purely descriptive — zero interpretation (every "suggests / because / likely reflects / consistent with / importantly" moved to the Discussion)
- [ ] Parallel strata (subgroups/arms/subtypes) written by template-and-swap — one shared sentence shape, only names + numbers differ, same fixed order across prose, table, and figure
- [ ] Intro funnel written last-paragraph-first; open questions enumerated
- [ ] Discussion arc complete; every limitation paired with a mitigation
- [ ] Standalone Conclusion lands on the standing validation/NMA caveat
- [ ] Abstract derived from finished manuscript; venue heading set; one results Table
- [ ] All effect estimates report the inline triple + absolute per-1000 translation
- [ ] Placeholder checklist cleared; references verified
- [ ] Copyedit-slip pass done
