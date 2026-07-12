# Section playbook

How Khan builds each manuscript section. Read the relevant entry before drafting that section. Section labels and citation style flex to the target journal (see `organization-and-workflow.md`); the architecture below is constant.

## Title

Lead with a descriptive noun phrase naming **disease + intervention**, and set the **study design off after a colon**: *"Differential Efficacy of PARP Inhibitors in Metastatic Castration-resistant Prostate Cancer: A Living Systematic Review and Meta-Analysis."* Put the method label in the title whenever the paper is an SR/MA/NMA or living review — *"Systematic Review and Network Meta-Analysis," "Living Systematic Review," "A Real-World Retrospective Cohort Study"* almost always appear.

For **AI/informatics** work, lead with a coined, Title-Case, parenthetically-defined named system or framework — *"Living Extractor: A Pipeline Leveraging Large Language Models…", "Living Interactive Evidence (LIvE) Synthesis Framework…"* — or a two-part punchy-phrase-colon-descriptive form — *"Governance ahead of strategy: Artificial intelligence adoption at US Comprehensive Cancer Centers and the ONCAIR framework…"*. Prefer a memorable named system when one exists and reuse the brand across papers.

**Conference-abstract titles** increasingly state the headline finding as a claim rather than a neutral topic — *"Perioperative Durvalumab Plus FLOT Is Top-Ranked for Disease-Free and Overall Survival…"*. Default to Title Case. Provide a **Running Title / Short Title** line in front matter.

## Introduction

A **3–4 paragraph funnel, problem-first**.

- **Paragraph 1** opens on a broad field-level pressure or a hard epidemiologic/prognostic statistic *with a citation* — *"Around 30% of all newly diagnosed bladder cancer cases are muscle-invasive…"* — **never** on the specific study object.
- **Middle paragraphs** establish why it matters and survey prior tools/attempts and their gap, frequently enumerating open questions (*"Firstly… Secondly… Thirdly…"*).
- **Final paragraph** is a self-contained **thesis + roadmap**: *"To address this gap, we performed/developed/propose X…"* followed by an explicit aims sentence or *"We hypothesized that…"*, and often a preview (*"Here we showcase…", "Hereby, we outline…"*).
- **AI/methods manuscripts** may insert a grant-style **"BACKGROUND AND SIGNIFICANCE"** section that reviews the technical literature chronologically.

Drafting tip: write the last-paragraph hinge sentence first, then build the three preceding paragraphs *backward* from it (opening statistic → why it matters → prior work and its gap).

## Methods

Broken into **many short labeled subsections in a fixed running order**.

**For SR / MA / NMA** (pair with `manuscript-srma` for the reporting mechanics):
reporting-guideline statement (PRISMA / PRISMA-NMA; *"was conducted using the LIvE synthesis framework"* for living reviews) → search strategy → study selection (inclusion then exclusion) → data extraction + risk of bias → statistical analysis (**pairwise before network**) → sensitivity/subgroup → GRADE / Summary of Findings. The **reviewer workflow is stated identically each time**: two independent reviewers named by initials, discrepancies resolved by a third reviewer.

**For pipeline/informatics work**, subsections are titled as **pipeline stages in processing order** (Data Sources → Data Processing → Sampling and Prompting → Post-processing → Agreement Matching → Evaluation), and each subsection **begins by describing the manual problem, then pivots** with *"To overcome this limitation, we have developed…"*. Name tools with parenthetical version numbers and state model settings as deliberate choices (*"We set temperature of the models to zero for deterministic responses," "in a zero-shot setting"*). Enumerate pipeline components as a numbered/bulleted list.

An **"Ethics" subsection is the last item before Results** (IRB approval, HIPAA, consent waiver). Methods **closes on the significance threshold as its own clause**: *"A p-value of <0.05 indicated a statistically significant association."*

## Results

**Always opens with the denominator/total**: the PRISMA study-flow count for reviews (*"In total, 19 RCTs (4217 patients) were included…"*) or the cohort-accounting sentence for clinical work (total N, per-subtype N, median age, sex, race, disease-specific medians).

Then proceeds in **exactly the same subsection order as Methods, one-to-one**, so a variable can be tracked from method to result by section name. Reviews go baseline characteristics → risk of bias → pairwise → NMA, each outcome under its own subheading in a fixed **OS → PFS/DFS → ORR/CR → adverse-events** order, **overall population before subgroups**.

Use the near-templated results sentence: *"X was associated with statistically significant improvement in [outcome] when compared to Y (HR: …; 95% CI: …; I²: …%; Supplement Figure S…)."* **Every claim ends by pointing to a specifically numbered exhibit**; detailed breakdowns are deferred to a heavily indexed supplement. **Results cite exhibits, never the bibliography.**

Occasionally (e.g. the NCCN survey) Results uses **thematic, thesis-bearing headers** (*"Finding 1: A governance-strategy paradox"*) instead of neutral variable names — good for a narrative/survey paper.

### Results describe; they do not interpret — this is a hard rule

The Results section is a **pure, descriptive transcription of the exhibits into prose**: report what was measured, in whom, and the value with its exhibit pointer, then stop. Interpretation is quarantined entirely to the Discussion. In Results, **do not**:

- explain *why* a result occurred or propose a mechanism;
- say a result "suggests," "indicates," "likely reflects," "is consistent with," "may be due to," "because," or "as expected";
- state clinical significance, importance, or implications;
- compare a finding to prior literature or to what was hypothesized;
- editorialize ("notably," "strikingly," "importantly," "surprisingly" belong in the Discussion, not here).

A useful test: **if a Results sentence would still read as a claim with all the numbers deleted, it is interpretation — move it to the Discussion.** Results state the number; the Discussion says what the number means.

### Template-and-swap for parallel strata

This is exactly how he writes multi-stratum results. When the same measure recurs across **subgroups, arms, or disease subtypes**, write the sentence **once and reuse it verbatim** for each stratum — **change only the stratum name and its numbers**, and keep the sentence structure, verb, clause order, and punctuation identical. The strata should line up so the reader could read them column-wise. Report the **overall population first**, then the strata in the **same fixed order every time** they recur — and reuse that same order across the sentence, the table rows, and the figure panels (e.g. the PV → ET → MF order is recycled word-for-word throughout his MPN papers).

**Example of the pattern** (structure held constant, only name + values swapped):
> "Among patients with **PV**, [predictor] was associated with [outcome] (B: …; p=…). Among patients with **ET**, [predictor] was associated with [outcome] (B: …; p=…). Among patients with **MF**, [predictor] was associated with [outcome] (B: …; p=…)."

When editing a Results draft, enforce this: if two strata are described with differently-shaped sentences, rewrite them onto one shared template so only the name and numbers differ.

## Discussion

A fixed arc:

1. **One self-referential summary sentence** — *"Our work demonstrates…", "This meta-analysis offers a comprehensive overview…"*.
2. A brief **"We conducted…" recap** paragraph.
3. **Enumerated implications/observations** — *"First/Second/Third"* or *"Three principal implications emerge", "Several observations warrant comment."*
4. **Mechanistic/clinical interpretation** via the signature move *"One possible explanation is… / Numerous mechanisms have been proposed…"*, then **comparison to prior literature**.
5. **Explicit novelty restatement** — contrast *"our approach"* against *"current approaches / existing frameworks."*
6. An **enumerated Strengths inventory** — *"This study has several strengths. First… Second…"*.
7. A **quarantined Limitations block** (see below).
8. A **forward-looking vision paragraph** — *"the future lies in… / Future work will focus on…"*.

## Limitations

Quarantined into their **own labeled paragraph or subheading** (*"Strengths and Limitations", "4.1"*), flagged by a near-verbatim opener: *"However, the findings of this study should be interpreted in the context of some limitations."* or *"A potential limitation of our approach is…"*. **Enumerated** First/Second/Third. **Each limitation is immediately neutralized with a mitigation or future-work rebuttal in the same breath** (*"However… We aim to…"; "This limitation could be addressed through longitudinal studies…"*), so limitations read as a roadmap rather than an admission. This mitigation-pairing is non-negotiable in his voice.

## Conclusion

A **discrete header, separate from Discussion**. A compact recap — one dense summative sentence for informatics work that re-lists every main finding in parallel clauses and ends on an aspirational note; 2–4 sentences for clinical work. Restate the headline effect direction, then **close on the reflexive caveat**: prospective/longitudinal/multi-site validation is needed, or NMA rankings complement rather than replace RCTs. Frame the takeaway as **utility/impact** (*"shows the utility of collaborative LLMs to streamline living evidence synthesis"*) rather than a numeric recap.

## Front and back matter

He prints housekeeping at the top of drafts and maintains full back matter. Include as applicable: word counts vs limits (abstract + manuscript), figure/table/reference counts, Running Title, Short Title, Key Points bullets, Keywords, and — at the back — Conflicts of Interest, Funding, Acknowledgments (librarian + PI credited), Authorship Contributions, and Data/Code Availability. Author byline lists **Khan first** with superscript institutional affiliations. **Senior authorship is shared** (co-senior, star-marked) between **Irbaz Bin Riaz** and, on the hematology/MPN papers, **Jeanne M. Palmer** — one of them takes the last slot (Palmer is last on the MPN/heme papers; Irbaz on the GU/AI papers). Match whichever senior author owns the project.
