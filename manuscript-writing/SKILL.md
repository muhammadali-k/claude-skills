---
name: manuscript-writing
description: Draft, organize, and revise a research manuscript or conference abstract in Muhammad Ali Khan's own academic voice and house organization — across ALL his research types (clinical/epidemiology cohort studies, AI/informatics & LLM-methods papers, and systematic reviews / meta-analyses / network meta-analyses, including living and interactive reviews). Use this whenever the user is writing or structuring their OWN paper and wants it to sound like them and be organized the way they organize — e.g. "draft my introduction", "write up the results for my cohort study", "turn my abstract into a full manuscript", "organize my manuscript", "help me write my discussion", "write the abstract for this analysis", "make this read like my other papers", "structure this paper for European Urology", or "tighten this section". Trigger even when the user does not name a section or the word "skill", and even when they only paste a draft and ask you to edit or continue it. This is the personal writing-voice + manuscript-organization companion: it layers Khan's recognizable voice, section architecture, statistical-reporting fingerprints, and skeleton-first/tables-first organization workflow on top of the content. It COMPOSES with manuscript-srma (which owns the SR/MA/NMA-specific reporting mechanics — GRADE/PRISMA-NMA, journal adapters, evidence-synthesis reporting conventions): for an evidence-synthesis paper, use manuscript-srma for those reporting conventions and THIS skill for the voice and organization. Do NOT use this for reviewing/marking up someone else's .docx with tracked changes — that is abstract-review.
license: Proprietary
---

# Manuscript-Writing — write and organize in Khan's voice

This skill helps draft, organize, and revise the user's (Muhammad Ali Khan's) manuscripts and abstracts so they read as unmistakably his and are structured the way he structures them. It was built by analyzing ~23 of his real submitted manuscripts and abstracts spanning clinical/epidemiology cohort work, AI/LLM-methods papers, and systematic reviews / meta-analyses / network meta-analyses. The goal is not generic "good academic writing" — it is *his* recognizable fingerprint.

## When you're invoked

1. **Scope in one pass** (don't interrogate). Infer and state your assumptions: (a) document type — full manuscript vs conference abstract vs grant deliverable; (b) research type — clinical/epi cohort, AI/informatics-methods, or evidence synthesis (SR / MA / NMA, living/interactive?); (c) target venue if stated (sets section labels + citation style); (d) which section(s) the user wants. Only ask if genuinely blocked.
2. **If it's an SR / MA / NMA**, also load `manuscript-srma` for the reporting mechanics (PRISMA/PRISMA-NMA, GRADE/SoF, journal adapters). This skill supplies the voice and organization on top; that skill supplies the evidence-synthesis reporting rules. They are designed to stack. If `manuscript-srma` isn't installed, apply the SR/MA reporting conventions inline from `references/statistical-reporting.md` and `references/section-playbook.md` — don't block on it.
3. **Draft or edit** using the moves below. For anything section-specific, read the matching reference file — don't work from this summary alone when you're actually writing that section.
4. **Never fabricate.** If a number, citation, cohort count, IRB number, or date is missing, drop in Khan's own placeholder tokens (`(X)` for a citation, `XX%` / `$XX` / `202X` for numbers, `IRBXX-XXXX`, an inline `NOTE TO ED:` for a verification task) and list every placeholder you left at the end so he can clear them. This mirrors how he actually drafts.

## Reference files — read the one you need

Progressive disclosure: this file holds the always-true core. Open the relevant reference before drafting that part.

- **`references/voice-and-phrasing.md`** — the full voice signature, sentence/grammar rules, the phrase bank (his actual connectors, pivots, closers), and 25 verbatim example sentences. Read before drafting ANY prose.
- **`references/section-playbook.md`** — how he builds each manuscript section (Title, Introduction, Methods, Results, Discussion, Conclusion, Limitations). Read before writing that section.
- **`references/abstracts.md`** — the conference-abstract and grant-abstract playbook (heading sets, two-sentence Background funnel, dense Methods paragraph, inline effect triples, the Table close). Read before writing an abstract.
- **`references/statistical-reporting.md`** — his quantitative fingerprints: the inline effect triple, the `(coefficient; p)` compact pair, the absolute "N per 1000" translation, heterogeneity/GRADE/NMA-ranking conventions, ML-metric reporting. Read before writing any Results or reporting any number.
- **`references/organization-and-workflow.md`** — the skeleton-first / tables-first project workflow, Methods↔Results parallelism, journal-adapter selection, versioned file naming, legend conventions, and the end-of-draft copyedit checklist. Read when organizing a project or preparing a draft for submission.

---

## The voice in one paragraph

Khan writes in a rigorously scaffolded, methods-forward register. Every piece opens on a broad field-level pressure (evidence outpacing clinicians; a disease's burden; AI outrunning governance) and **funnels**, paragraph by paragraph, to one unresolved gap, then pivots on a fixed hinge — *"To address this gap, we..."* — into a first-person-plural statement of what the work does. He owns the work in the active voice (**we developed, we found, our approach**) and uses agentless passive only for procedures (*Data were abstracted*). He defines every abbreviation on first use and reuses it relentlessly, often coining a Title-Case branded framework (LIvE, LISR, ONCAIR) or a compact study nickname (dFLOT, aIO) and reusing it across papers. Two temperamental signatures run through everything: **constructive humility** (limitations are quarantined and each is paired, in the same breath, with a mitigation or future-work rebuttal, so they read as a roadmap; work closes on a standing caveat — prospective/multi-site validation before deployment; NMA rankings complement, not replace, RCTs) and **ambition** (first-in-class, paradigm shift from reactive to proactive, an expansive vision sentence to close). He is reproducibility-minded: exact software versions, PMIDs, cohort counts, model temperature/zero-shot settings, search cutoff dates, reviewer initials.

## The core moves (true in every document type)

These recur across clinical, AI, evidence-synthesis, and abstract writing — they ARE the voice. Apply them by default.

1. **The problem-first funnel.** Open on a broad pressure or a hard epidemiologic/prognostic statistic *with a citation* — never on the specific study object. Narrow over 3–4 paragraphs (manuscript) or two sentences (abstract) to the single gap. Put the study object only in the last intro paragraph. *("Around 30% of all newly diagnosed bladder cancer cases are muscle-invasive in nature…")*
2. **The fixed hinge.** Pivot from problem to your work with *"To address this gap, we…"* / *"To overcome this limitation, we have developed…"* / *"To this end, we…"*, then end the intro with a thesis+roadmap sentence and an explicit aim or *"We hypothesized that…"*.
3. **First-person-plural ownership.** Every authorial action and claim is **we/our**, active voice (*we performed, we found, our analysis clearly indicates*). Never first-person singular. Passive only for procedures. Contrast *"our approach"* against *"current approaches / existing frameworks"* to stake the novelty claim.
4. **Define-and-brand.** Spell out every abbreviation in parentheses on first use, then use the short form. Where warranted, coin a memorable Title-Case, parenthetically-acronymed framework and reuse the brand across papers; for AI systems, name the modules (The Watcher, The Scanner, The Extractor).
5. **Explicit enumeration.** Enumerate open questions, implications, strengths, and limitations with *Firstly/Secondly/Thirdly/Lastly* or *First/Second/Third*.
6. **Methods↔Results parallelism.** Write Methods as an ordered pipeline with short labeled subsections; title each Results subsection *identically* so a variable is trackable from method to result by name. Results always opens with the total N/denominator.
7. **Exhibit-tethered claims.** Every quantitative claim ends by pointing to a specifically numbered exhibit (*Table 2; Supplement Figure S11*). Results cite exhibits, never the bibliography. Push detail into a heavily indexed supplement.
8. **Effect-estimate triple + absolute translation.** Report estimates inline as `(HR: 0.72; 95% CI: 0.56–0.94; I²: 87%; Supplement Figure S11)` and *always* also translate relative effects into absolute *"N fewer/more events per 1000 patients"* with its own CI. (See `references/statistical-reporting.md`.)
9. **Mitigation-attached limitations.** Never state a weakness without immediately attaching a mitigation or future-work rebuttal in the same breath. Quarantine limitations into their own block, opened with *"However, the findings of this study should be interpreted in the context of some limitations."*
10. **The reflexive close.** Land on the standing caveat (prospective/multi-site validation warranted before deployment; NMA rankings complement not replace RCTs), then an ambitious impact/utility sentence.

## Connectors and tics — use, but don't autopilot

His fixed connector set opens sentences and paragraphs: *However, Moreover, Furthermore, In addition/Additionally, Notably, Importantly, Interestingly, Conversely, Taken together, Of note, It should be noted that.* Use them — they're his voice — but **don't start several consecutive sentences with "However," / "In addition,"**; that tips from characteristic into mechanical. The full phrase bank (pivots, novelty claims, the templated results verb-frame, the standing caveats, the limitations opener+rebuttal, the strengths formula) is in `references/voice-and-phrasing.md`.

## Watch his recurring slips (fix, don't reproduce)

His voice is worth imitating; his copyedit slips are not. When editing or before "finishing," hunt these — they survive many of his versions unless deliberately targeted:

- Doubled words (*"ATM mutations ATM mutations"*), run-together words (*"performednetwork", "withing"*), dropped articles, subject–verb disagreement, double negatives.
- Recurring misspellings: *Certainity → Certainty*, *continuosly → continuously*.
- Duplicated pasted paragraphs or figure legends; mixed *Fig.* vs *Figure* cross-references.
- Inconsistent CI delimiters (semicolon vs comma) — standardize on semicolons.
- Mixed dispersion notation in one paper (*mean ± SD* vs *mean (SD = )*) — pick one per manuscript.
- Left-in draft scaffolding: `(X)` citation placeholders, `XX%`/`$XX`/`202X`, `IRBXX-XXXX`, `NOTE TO ED` — clear all before submission and verify every reference.

## Editing vs drafting

- **Drafting a section**: read the matching reference file, then write it to the architecture and voice there. Match section labels and citation style to the target venue up front (decide once; keep the whole draft consistent).
- **Editing his draft toward his voice**: preserve his content and claims; restructure toward the funnel/parallelism, tighten runaway sentences, enforce the effect-triple + absolute translation, pair limitations with mitigations, and run the copyedit-slip hunt. Don't sand off the voice — keep the enumeration, the branded terms, the ambition. The failure mode is over-neutralizing him into generic journal prose.
- **Organizing a project**: follow `references/organization-and-workflow.md` — lay a reserved-space skeleton, build tables/exhibits first, write prose against them, derive the abstract from the finished manuscript last.
