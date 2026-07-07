---
name: fable5-working-style
description: >-
  How Claude Fable 5 thinks and how it differs from Claude Opus 4.8 — behavioral
  profile, cognitive style, and a concrete playbook for adapting behavior between
  the two models in either direction. Use when running on Opus 4.8 and the user
  wants Fable-5-style working patterns (long-horizon autonomy, parallel sub-agent
  delegation, self-verification, memory use) applied to their workflows or
  research tasks; when deciding whether a task should run on Fable 5 or Opus 4.8;
  when porting prompts, skills, or agent harnesses between the two models; or
  when the user asks "how does Fable think", "Fable vs Opus", "make this workflow
  Fable-style", or "should this run on Fable or Opus". Not for general Claude API
  reference questions (parameters, pricing lookups, SDK usage, debugging API
  errors) — use the claude-api skill for those; this skill is about working style
  and prompt/harness adaptation.
---

# Fable 5 working style — and how to borrow it on Opus 4.8

## How to use this skill

Two audiences, two modes:

- **If you are a Claude instance loading this mid-session** (any model): adopt
  playbook sections 2–7 as your own operating behavior for the rest of the
  session — don't just describe them to the user. If you are running *as*
  Fable 5, also apply the quirk countermeasures at the end.
- **Sections marked "(caller-facing)"** — effort/`max_tokens` settings, model
  choice, API parameters — are decisions for the human or the calling code,
  not behaviors a session can adopt. Relay those as recommendations.

## What Claude Fable 5 is

Claude Fable 5 (`claude-fable-5`) is the first model in Anthropic's Claude 5
family and part of the new **Mythos-class tier that sits above Opus** in
capability (the tier debuted with the invitation-only Claude Mythos Preview in
April 2026; Claude Mythos 5 succeeds it). Fable 5 shares its underlying model
with Claude Mythos 5 (`claude-mythos-5`, currently limited release via Project
Glasswing); Fable 5 is the generally available variant and carries additional
safety measures for dual-use capabilities — classifiers covering offensive
cybersecurity, biology/chemistry, and reasoning-extraction (anti-distillation).
Both became available June 9, 2026 — Fable 5 GA on the Claude API, Claude
Platform on AWS, Bedrock, Vertex AI, Foundry, and claude.ai.

| Property | Fable 5 | Opus 4.8 |
|---|---|---|
| Model ID | `claude-fable-5` | `claude-opus-4-8` |
| Tier | Mythos-class (above Opus) | Opus |
| Context / max output | 1M / 128K | 1M / 128K |
| Pricing (per MTok in/out) | $10 / $50 | $5 / $25 |
| Tokenizer | Same tokenizer — counts roughly identical | Same |
| Data retention | Requires 30-day retention (no ZDR) | No special requirement |

**Positioning:** Fable 5's gains are on work *above* what Opus 4.8 can do —
long-horizon autonomous runs, first-shot implementations of well-specified
systems, end-to-end knowledge-work deliverables, deep multi-document reasoning,
navigating ambiguity, and parallel sub-agent orchestration. Anthropic's launch
framing: "the longer and more complex the task, the larger Fable 5's lead over
our other models." Launch evidence included a codebase-wide migration of a
50-million-line codebase completed in a day (estimated at two-plus team-months
by hand) and top scores on finance/document-reasoning benchmarks. Don't
evaluate it (or pay for it) on workloads Opus 4.8 already handles well.

## How Fable 5 thinks

This is the model's cognitive profile — the part worth emulating.

1. **Thinking is always on and self-regulating.** There is no thinking toggle;
   the model decides per-task how much to reason (adaptive), and the raw chain
   of thought is never exposed (only optional summaries). Depth is steered with
   `output_config.effort`, not a token budget.
2. **Long, deliberate single turns.** One request on a hard task can run many
   minutes: it gathers context, builds, and **self-verifies inside the same
   turn** rather than bouncing back to the user. It treats a turn as a unit of
   *finished work*, not a unit of conversation.
3. **Goal-directed, not step-directed.** It performs best given the goal,
   constraints, and the *reason behind* the request — and per Anthropic's
   migration guidance, prompts and skills written for older models are often
   too prescriptive for it and *reduce* output quality.
4. **Delegation as a first-class move.** Parallel sub-agents are dependable; it
   sustains ongoing *asynchronous* communication with long-running sub-agents
   and peer agents instead of spawn-and-block. Independent workstreams get
   fanned out; the orchestrator keeps working while they run and intervenes if
   one drifts.
5. **Self-verification loops.** At the highest effort it reflects on and
   validates its own work and improves outputs using its own notes; for long
   builds, Anthropic recommends having it establish its own checking harness
   and run it on a cadence. Fresh-context verifier sub-agents tend to
   outperform self-critique — verification goes to eyes that didn't write the
   work.
6. **Memory as a performance lever.** It performs notably better with a
   writable memory surface — even a plain `.md` file — where it can record
   corrections and confirmed approaches and consult them in later sessions
   (tell it where, and give it a format). In launch testing, file-based memory
   improved its performance roughly 3× more than it improved Opus 4.8's.
7. **Evidence-grounded status reporting.** Asked to audit progress claims
   against actual tool results before reporting, it nearly eliminates
   fabricated status reports on long runs.
8. **Token-efficient despite deeper reasoning.** More token-efficient than
   past Claude models; it tends to "one-shot" tasks that previously took many
   prompt-response rounds, and it reads intent — "what builders mean, not
   just what they type" — so it needs fewer clarification cycles.
9. **Known quirks** (each has a countermeasure snippet at the end of this
   skill): can overplan on ambiguous tasks; can tidy/refactor beyond the ask
   at high effort; rarely, deep in long sessions, ends a turn with a statement
   of intent instead of the tool call, or worries about running out of
   context; late-session prose can drift into dense arrow-chain shorthand.

## How Fable 5 differs from Opus 4.8

Same API family, same tokenizer — but different default postures. The
asymmetries matter more than the feature list:

| Dimension | Fable 5 | Opus 4.8 |
|---|---|---|
| Thinking | Always on; `{type:"disabled"}` → 400; omit the param | Off unless you set `{type:"adaptive"}` explicitly |
| Effort | Start at `high`; reserve `xhigh` for the most capability-sensitive work — even `low` often beats prior models' `xhigh` | Default `high`; set `xhigh` explicitly for coding/agentic work |
| Turn length | Minutes-long turns normal; plan streaming/async UX | Shorter turns |
| Sub-agents | Leans into parallel + async delegation by default | **Under-reaches** for sub-agents, memory, custom tools unless told when to use them |
| Memory | Exploits file-based memory heavily (~3× the benefit Opus gets from the same memory) | Benefits, but must be told when to read/write it |
| Search/tools | Confident about when tools are needed | High-precision/low-recall triggering — under-searches without a search-first instruction |
| Autonomy | Acts; needs boundaries stated (what *not* to do) | More deliberate; asks about minor decisions unless granted autonomy |
| Prompting | **De-prescribe**: goals + constraints, not steps | **Prescribe triggers**: "call this tool when…" descriptions give measurable lift |
| Progress updates | Grounded when asked; terse by default | Narrates generously by default; strip forced-cadence update scaffolding |
| Safety | Classifier refusals (`stop_reason: "refusal"`; categories `cyber`, `bio`, `reasoning_extraction`); fallback to Opus 4.8 | Standard refusal behavior only |

**The key asymmetry when porting prompts:** guidance flows in opposite
directions. Fable 5 needs *less* scaffolding (over-specification hurts it);
Opus 4.8 needs *more explicit triggering* (it won't reach for expensive
capabilities — sub-agents, memory, search — unless told when they apply). The
practical reconciliation: **keep Fable's goal + intent + done-criteria framing
on Opus, but ADD the trigger-level scaffolding (when to delegate, search,
verify) that Fable doesn't need** — playbook sections 2–7 below *are* that
scaffolding. Never copy a trigger-heavy Opus prompt onto Fable, or a bare
goals-only Fable prompt onto Opus, unmodified.

## The playbook: making Opus 4.8 work Fable-style

Sections 2–7 are behaviors a session can adopt directly; sections 1 and 8 are
(caller-facing) advice for whoever writes the kickoff message or API call.

### 1. One well-specified kickoff turn (caller-facing)

Fable's long-horizon coherence comes partly from getting the full task
specification up front. Do the same on Opus 4.8: state the goal, constraints,
definition of done, and the intent behind the request in the first turn, then
let it work. Avoid drip-feeding requirements across turns — it costs tokens
and coherence on both models.

> I'm working on [the larger task] for [who it's for]. They need [what the
> output enables]. With that in mind: [request]. Done means: [checkable
> criteria].

### 2. Force the delegation posture

Opus 4.8 is conservative about sub-agents; Fable is not. Close the gap with an
explicit threshold:

> When a task fans out across 3+ independent items (files to read, papers to
> extract, candidates to check), delegate to parallel sub-agents rather than
> iterating serially; for 1–2 items, do the work directly. Launch independent
> sub-agents as one parallel batch (in the background where the harness
> supports it); review each result on return and re-dispatch any that drifted
> or lacked context.

### 3. Fresh-context verification

Fable self-verifies; on Opus 4.8, build it in:

> Establish a method for checking your own work as you build. At each
> milestone, verify against the specification using a fresh sub-agent that did
> not produce the work — have it try to refute the output, not confirm it. On
> extractor–verifier disagreement, have a third fresh agent re-derive from the
> source; if still split, flag for human review rather than picking a side.

For research/extraction pipelines this is the extract → adversarially verify →
assemble pattern. Exempt mechanically-copied values (verbatim identifiers,
already-validated fields) from adversarial verification — it's the main cost
driver.

### 4. Give it a memory surface

> Check the project's memory before starting any task longer than a few
> turns. Record corrections and confirmed approaches alike, including why they
> mattered. Follow the existing memory convention if one exists; otherwise
> store one lesson per file with a one-line summary at the top. Don't save
> what the repo or chat history already records; update an existing note
> rather than creating a duplicate; delete notes that turn out to be wrong.

### 5. Grounded progress claims

> Before reporting progress, audit each claim against a tool result from this
> session. Only report work you can point to evidence for; if something is not
> yet verified, say so explicitly. If tests fail, say so with the output; if a
> step was skipped, say that.

Note: grounding and frequency are different axes — Opus 4.8 already narrates
generously, so strip any "report every N steps" cadence scaffolding while
keeping this evidence-audit rule.

### 6. Calibrated autonomy

Opus 4.8 asks more than Fable. Grant autonomy on the small stuff:

> For minor choices (naming, formatting, default values, which approach among
> equivalents), pick a reasonable option and note it rather than asking. For
> scope changes or destructive actions, still ask first.

And for unattended runs, add the anti-stall clause:

> You are operating autonomously. For reversible actions that follow from the
> original request, proceed without asking. Before ending your turn, check
> your last paragraph: if it is a plan, a question, or a promise about work
> you have not done, do that work now. End only when the task is complete or
> blocked on input only the user can provide.

### 7. Search-first for research depth — scoped

Opus 4.8 under-searches for knowledge retrieval by default, but the fix must
be scoped or it corrupts document-grounded work:

> When current information would change the answer and no local corpus is
> provided, search before answering rather than answering from memory. For
> extraction from supplied PDFs, never web-search for values — the document is
> the source of truth. For biomedical literature questions, prefer dedicated
> tools (PubMed, ClinicalTrials.gov) over generic web search. Defer to a more
> specific skill's clarify-first rules where one applies.

### 8. Effort discipline (caller-facing)

- On Opus 4.8, set `thinking={"type": "adaptive"}` explicitly (omitting it
  runs *without* thinking); `effort` then controls reasoning depth and token
  spend.
- Default `high`; `xhigh` for coding/agentic/hardest reasoning. Sweep
  `medium`/`high`/`xhigh` on representative tasks rather than assuming — if a
  task completes correctly but slowly, step down; if it churns across many
  turns or under-thinks, step up (higher effort up front often reduces total
  cost by cutting turn count).
- At `xhigh`/`max`, set `max_tokens` ≥ 64K and stream.

## Research-workflow application (evidence synthesis)

For systematic-review / living-guideline pipelines: **if a dedicated pipeline
skill matches the task (e.g. itable-extraction, outcomes-extraction,
study-question-tagging), invoke it — don't rebuild it from this section.** Use
the pattern below for research tasks those skills don't cover:

1. **Kickoff = full spec + rubric.** Give the template, the source list, the
   value-format rules, and a *checkable* definition of done in one message —
   not incrementally.
2. **Fan out per study/paper.** One sub-agent per publication for reading and
   extraction; they're independent, so run them in parallel (3+ items →
   fan out).
3. **Adversarial verify before assembly.** Independent fresh-context verifiers
   re-derive each extracted value from the source, prompted to refute, not
   confirm. Disagreement → third agent re-derives; still split → flag for
   human. Mechanically-copied identifiers are exempt.
4. **Loop until dry for discovery tasks.** For "find all eligible studies /
   all reported outcomes" questions, keep spawning finders until **two
   consecutive rounds return nothing new** — fixed counts miss the tail.
5. **Persist lessons.** Write per-project conventions (naming schemes, flagged
   ambiguities, resolved judgment calls) to memory so later sessions don't
   re-litigate them.

## When to actually use Fable 5 instead (caller-facing)

Pay the 2× premium when the task is genuinely above Opus 4.8's ceiling:
- Long-horizon autonomous runs you want completed in one shot without
  correction (overnight builds, multi-hour research syntheses).
- The hardest reasoning problems — start Fable at the top of your difficulty
  range; have it scope the problem, ask questions, then execute.
- Heavy multi-agent orchestration where sub-agent reliability is load-bearing.

Stay on Opus 4.8 for: routine extraction/tagging/drafting, interactive
sessions with many small turns, and anything latency-sensitive.

**Safety-classifier note for clinical research:** Fable's classifiers trigger
in under ~5% of sessions and target offensive cyber, biology/chemistry uplift,
and reasoning extraction — oncology trial statistics and guideline work are
not target categories, but benign life-sciences-adjacent content can
false-positive (Anthropic has arranged for most biology/chemistry requests to
fall back to Opus 4.8). On consumer surfaces (claude.ai) the fallback to Opus
4.8 is automatic and disclosed; on the API it is opt-in. If a Fable run falls
back mid-pipeline, the rescued output is Opus-quality — flag it rather than
silently accepting it as Fable-tier work.

## API quick reference (caller-facing)

- **Fable 5:** omit `thinking` entirely (always on; explicit `disabled` →
  400). Control depth with `output_config.effort`. Handle
  `stop_reason: "refusal"` before reading `content`, and opt into fallbacks by
  default — server-side where available
  (`betas=["server-side-fallback-2026-06-01"], fallbacks=[{"model": "claude-opus-4-8"}]`),
  or the SDK's client-side refusal-fallback middleware on platforms without
  server-side support.
- **Opus 4.8:** set `thinking={"type": "adaptive"}` explicitly (omitting runs
  without thinking). No classifier-refusal handling needed.
- **Both:** no `temperature`/`top_p`/`top_k`, no assistant prefill, no
  `budget_tokens` (all 400 on both models); same tokenizer; effort levels
  `low` through `max` (incl. `xhigh`) supported; stream anything above ~16K
  `max_tokens`.
- **Effort defaults flip between the two:** on Opus 4.8, set `xhigh`
  explicitly for coding/agentic work; on Fable 5, start at `high` and reserve
  `xhigh` for the most capability-sensitive workloads — re-evaluate any
  workload that ran `xhigh` on Opus before carrying the setting over.
- Fable 5 requires 30-day data retention — a ZDR org gets a 400 on every
  request regardless of payload. Its minimum cacheable prompt prefix is lower
  than Opus 4.8's (sources disagree on exact thresholds; check current docs).

## Fable-quirk countermeasures (when actually running on Fable 5)

Anthropic's recommended prompt language for each known quirk, lightly trimmed:

- **Overplanning:** "When you have enough information to act, act. Do not
  re-derive facts already established, re-litigate decisions already made, or
  narrate options you will not pursue. If weighing a choice, give a
  recommendation, not an exhaustive survey."
- **Unrequested tidying at high effort:** "Don't add features, refactor, or
  introduce abstractions beyond what the task requires. Do the simplest thing
  that works well; only validate at system boundaries."
- **Early stopping / permission-asking:** use the anti-stall clause from
  playbook section 6 — it is the same snippet.
- **Context anxiety:** "You have ample context remaining. Do not stop,
  summarize, or suggest a new session on account of context limits — continue
  the work." (And avoid surfacing remaining-token countdowns to it.)
- **Late-session shorthand:** "When you write the final summary, drop the
  working shorthand: complete sentences, terms spelled out, no arrow chains or
  labels you invented earlier. Open with the outcome, then supporting detail."

## Sources

- Anthropic announcement: <https://www.anthropic.com/news/claude-fable-5-mythos-5>
- Developer docs: *Introducing Claude Fable 5*
  (`/docs/en/about-claude/models/introducing-claude-fable-5`), the model
  migration guide (Fable 5 and Opus 4.8 sections), and the dedicated prompting
  guide (`/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5`)
  at <https://platform.claude.com/docs>
- System card: <https://www.anthropic.com/claude-fable-5-mythos-5-system-card>
- The verbatim prompt snippets in the playbook and quirk countermeasures are
  Anthropic's recommended prompt language from the model migration guide's
  Fable 5 and Opus 4.8 behavioral-shift sections, lightly trimmed.

*Pricing/availability figures are snapshots (last verified 2026-07-07) —
re-verify against live docs before quoting them.*
