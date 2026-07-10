# Review method

This is the how-to behind `SKILL.md`. It covers the generic critique checklist (applied on top of the
research-type profile), the two review modes, the edit-vs-comment rule, adversarial verification, and how
to write comments and edits that read like an expert reviewer.

---

## The generic checklist (every review, every research type)

Read the whole document once for sense, then scrutinize:

1. **Internal consistency** — the highest-yield category and the easiest to verify from the document
   itself. Numbers that must agree across sections: trial/patient/sample counts, arithmetic (do the
   subgroup Ns sum to the total?), percentages vs. counts, CIs vs. point estimates vs. stated
   significance, the outcome list in Methods vs. what Results report, and — critically — **does every
   sentence in the Conclusion follow from the Results?** A revision that adds or drops an arm/study but
   doesn't propagate the change is the classic defect (e.g. Intro says "three trials", Results say
   "four"; Conclusion says "all three combinations improved X" after a fourth was added that did not).
2. **Claim calibration** — is each claim as strong as the evidence supports and no stronger? Watch
   "significant" for borderline/one-sided/non-alpha-protected results; "improved/superior" when a CI
   crosses the null; causal verbs on non-randomized data; "first/only/novel" absolutes; and ranking
   language (P-scores/SUCRA) read as effect magnitude.
3. **Design & reporting honesty** — is the design reported straight? Immature/preliminary data labeled as
   such; the right reporting standard's key elements present (profile-specific); limitations that a reader
   needs in order to weigh the result actually stated.
4. **Data plausibility** — do the numbers match what you know of the field / the cited source? You often
   **cannot** verify this from the document alone → flag, don't edit (see below).
5. **Clarity, concision, consistency** — undefined abbreviations at first use; terminology drift (the same
   thing named two ways — "Rux alone" vs "Rux monotherapy"); redundancy; awkward tracked-change residue;
   grammar. These are the bread-and-butter tracked edits.
6. **Venue compliance** — character/word limit, structure, formatting rules, tables/figures policy
   (`venues.md`). Flag limit overruns and note submission-only formatting steps.

The research-type profile sharpens 2–4 for the specific design. Read it before critiquing.

---

## Mode A — fresh review

1. `inspect` and `render ... accept` to load the text and any pre-existing markup.
2. Identify the research type; load the profile.
3. Work the generic checklist + profile. Keep a running list of candidate findings, each tagged
   *edit* or *comment* and *confident* or *needs-verification*.
4. Verify the needs-verification findings (next section). Drop what doesn't survive.
5. Compose the edit plan; apply; validate; sanity-check; deliver + summary.

## Mode B — re-review of a revision against prior comments

The revised `.docx` almost always carries the previous round inline: your prior comments, the author's
replies (threaded), and the author's tracked changes (often already accepted). Use that.

1. `inspect` → get the list of existing comments with `reply->N` threading and `[RESOLVED]` state, and
   `render ... markup` / `render ... accept` to see what changed.
2. **Audit each prior reviewer comment** and classify against the *current* text:
   - **resolved** — the text now addresses it; confirm briefly (a one-line in-thread reply is enough, or
     leave it if the author already marked it resolved).
   - **partially addressed** — part done; reply in-thread with the specific remaining ask.
   - **open** — untouched; reply in-thread, restating the concern concisely and what would resolve it.
   - **declined by author** — the author gave a rationale (often reasonable for an abstract, e.g. omitting
     formal RoB/GRADE for space). Acknowledge; note the low-cost alternative if one exists; respect their
     call.
   - **author asked a question** ("How?") — answer it clearly in-thread. This is a real obligation, not
     optional.
3. **Verify the author's substantive changes.** New data, added studies/arms, updated numbers — check they
   are internally consistent and didn't introduce new errors. Adding a study to a network shifts the
   shared comparator; confirm the counts and every downstream claim were propagated.
4. Reply in-thread (never duplicate the original comment as a new one). Add new comments/edits only for
   genuinely new issues.
5. Apply; validate; deliver + summary that separates *resolved*, *still-open/partial*, *newly-introduced*,
   and *author-decisions-accepted*.

---

## Verify before you assert (and never fabricate)

- **From the document:** internal-consistency and wording findings are verifiable by reading — high
  confidence, safe to edit.
- **About the world:** whether a reported number matches the source trial, whether a method is standard,
  whether a claim is current — you often cannot confirm from the file. For anything non-trivial, verify
  (search/tools), and for a substantive review **verify adversarially**: spin up a small verification pass
  whose agents *try to refute* your top findings, and keep only those that survive. The ASH NMA review ran
  a Workflow with per-finding refute agents before any edit was committed; do the same for consequential
  claims. (Only spin up a workflow when the user has opted into multi-agent orchestration or the task
  clearly warrants it; otherwise verify inline.)
- **The hard rule:** if you cannot verify a data value, do **not** change it and do **not** invent a
  "correct" one. Write a comment that flags it — state what looks off, what the likely source/vintage is,
  and ask the author to confirm. Tag such comments so it's clear you did not edit the number
  ("Data check — flagged, not edited").

---

## Edit vs. comment — the rule of thumb

**Make it a tracked edit** when the fix is objective and you're confident from the document alone:
grammar; a stale count that contradicts the rest of the paper; terminology drift; redundancy/concision; a
conclusion clause that plainly overstates the results; a CI upper bound that must read `1.00` because the
text already calls it non-significant. Keep each edit minimal and inside one run.

**Make it a comment** when it needs the author's judgment or external knowledge: a data value you can't
verify; a methodological addition (software/package, zero-cell handling, an effect modifier, a missing
reporting element); a suggestion whose wording is the author's call; a question; a completeness concern
(a missing study, an un-searched database). And in re-review, all replies to prior comments.

When in doubt between the two, comment. An unwanted comment costs the author ten seconds; an unwanted edit
erodes trust.

---

## Writing the markup

**Comments** — the voice is a senior co-author, not a gatekeeper. Each comment:
- leads with the concern in one clause, then the evidence, then the concrete ask;
- is specific (name the number, the sentence, the standard) and actionable ("add X" / "confirm Y" /
  "soften to Z");
- is proportionate — flag the borderline OS signal, don't lecture; acknowledge what's reassuring
  (double-blind, placebo-controlled) when noting a limitation;
- signs off with the reviewer initials so threads read cleanly (e.g. `- MAK`);
- in re-review, opens by locating itself relative to the prior round ("Confirmed resolved —", "Largely
  addressed —", "Re your question 'How?': ...").

Keep comments plain ASCII where practical (hyphens, `>=`, spelled-out symbols) — it avoids encoding
surprises and reads fine in Word.

**Edits** — the smallest change that fixes the problem. Prefer replacing `All three` → `Three of the four`
and inserting `, whereas parsaclisib did not` over rewriting a whole sentence. Don't restructure a
paragraph to impose your style. Every edit must survive the reject-all invariant (the tool checks it).

---

## Failure modes to avoid

- Editing a number you couldn't verify (fabrication risk) — comment instead.
- A blanket find/replace that also hits a legitimate different use (e.g. `three → four` everywhere, when
  the Conclusion's "three of four" is correct). Scope every edit to the right paragraph and occurrence.
- Re-posting a prior concern as a fresh comment instead of replying in-thread.
- Over-editing a sound draft. If it's ready, say so.
- Stripping working-draft formatting (bold headers) that is only banned *on submission* — note it as a
  submission step.
- Targets that span runs / tracked-change boundaries — the tool errors; split into smaller edits.
