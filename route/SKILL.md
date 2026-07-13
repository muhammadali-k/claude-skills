---
name: route
description: >-
  On-demand two-model build loop: the Claude session (Fable 5 today; Opus 4.8 or any
  Claude works identically) is the BOSS — it plans, dispatches, and reviews. OpenAI's
  GPT-5.6 Sol, driven headlessly through the codex CLI, is the WORKER — it builds and
  fixes. The loop repeats build → review → fix until the boss approves. Works for any
  buildable task, not just code: analysis scripts, data-extraction pipelines, document
  or file generation — anything where Sol writes files and the boss can verify the
  result against a plan. Chain of command: the Claude session plans and orchestrates
  first; every delegated build reroutes to Sol in Ultra Mode (instead of Claude
  subagents), falling back to an Opus 4.8 subagent only when Sol's usage limit
  is hit. The boss reviews everything either way. Trigger ONLY when the user types /route, says "route this",
  "run the route loop", "hand this to Sol", or explicitly asks for the Claude+Sol /
  Claude+Codex two-model loop. Do NOT use for ordinary single-model coding, planning,
  refactors, or chat.
---

# Route: Claude runs GPT-5.6 Sol

You are the boss. You PLAN and you REVIEW. You do not write the implementation
yourself — GPT-5.6 Sol builds and fixes, driven through `codex exec`. Work travels
around the loop until you approve it.

This skill is manual: it runs only when explicitly invoked (see the trigger rules in
the description), never on an ordinary prompt.

Placeholders used throughout: `<project-dir>` is defined in preflight step 3;
`<scratchpad>` is the session scratchpad directory if your harness lists one, else
`$TMPDIR` (both are writable under the workspace-write sandbox). Use per-round file
names for logs and `-o` files — never reuse one, or a stale file from round 1 blinds
the round-2 success check.

## Worker triage (who plans, who builds)

Chain of command, in order:

1. **The Claude session — Fable 5 (or Opus 4.8) — plans and orchestrates, always
   first.** The boss role never moves: you write PLAN.md, you dispatch, you
   review, you approve. Triage below governs only where delegated build work goes;
   it never demotes you from orchestrating.
2. **Every delegation of implementation goes to GPT-5.6 Sol in Ultra Mode first**
   (`-m gpt-5.6-sol -c model_reasoning_effort=ultra`). The moment you would hand
   build work to one of your own subagents — e.g. an Opus 4.8 agent via the Agent
   tool — that handoff reroutes to Sol via `codex exec` instead. Never split the
   build across Claude subagents while Sol is available. (`ultra` is live-verified
   on codex-cli 0.144.1 with gpt-5.6-sol; if a model/CLI combo ever rejects it with
   a "Supported values are: … 'xhigh'" error, use `xhigh`, the next tier down.)
3. **Opus 4.8 subagent** (see "The Opus worker path" below) — only when Sol is
   unavailable: usage limit hit (window not yet reset), auth outage (see
   "Detecting an auth failure" below), or the model-fallback chain in preflight
   step 5 exhausted. Announce the switch to the user the moment it happens, and
   say why in the report.
4. **The boss never builds.** If both workers are unavailable, stop and report.

The boss reviews everything, whichever worker built it. A worker never acts as the
final review gate on its own work.

**Detecting a Sol usage limit:** the dispatch log contains a line like "You've hit
your usage limit. … try again at <time>" — grep the log case-insensitively for
`usage limit`, `rate limit`, `429`, or `Too Many Requests`. Codex usage pools are
windowed (typically 5-hour), so the message usually names a reset time — record it.
If the limit hits mid-loop (after a successful Sol build), move the remaining fix
rounds to the Opus worker path, handing the Opus agent PLAN.md, the review
findings, and the changed-file list (mechanics: the "Mid-loop takeover" case in
the Opus worker path); only wait out the window instead if the reset time is
within ~15 minutes. A usage-limit switch does not consume an infrastructure-retry
or a fix round by itself.

**Detecting an auth failure:** a dispatch log showing `401`, `unauthorized`, or an
authentication/login prompt — with no usage-limit message — is an auth problem,
not a usage limit. Run `codex login status` (free, local) to discriminate. Logged
OUT → the token expired or was revoked mid-run: ask the user to run
`! codex login` once and resume with Sol — a quick fix, not a worker switch, and
it consumes no fix round or retry. Logged IN but dispatches keep failing with
auth/server errors → service-side outage: Sol is unavailable, switch to the Opus
worker path and say why in the report. (Preflight step 2 is unchanged:
not-logged-in BEFORE the run always goes to the user.)

## Preflight (fast, before planning)

1. `codex --version` — if the CLI is missing, stop and tell the user to install it
   (`npm i -g @openai/codex` or `brew install --cask codex`), then re-run `/route`.
2. `codex login status` — if not logged in, ask the user to run `! codex login`.
3. **Fix `<project-dir>`.** The narrowest existing directory that contains everything
   the task reads and writes — the repo root for repo work, the task's folder for
   folder-scoped work. This is a sandbox decision, not a convenience: it becomes
   Sol's writable root. Never point it at a broad directory (`~`, `~/Documents`,
   `~/Desktop`, a drive root); if the task's files live loose in one, ask the user
   whether to narrow to (or create) a subfolder first. Everywhere this skill says
   "project directory" or "project root", it means this directory — PLAN.md goes at
   its top level.
4. **Git state of `<project-dir>`.**
   - Not a git repo → every `codex exec` call (including fix-round resumes) gets
     `--skip-git-repo-check`; review layer 2 uses its file-snapshot variant, and
     layer 3's `codex exec review` variant is unavailable (needs a repo) — a
     second opinion, if taken, uses the Opus-subagent variant scoped to the
     snapshot file lists (see layer 3).
   - Git repo → run `git status --porcelain`. If the tree is dirty, tell the user
     and recommend committing or stashing first — a clean baseline is the only
     reliable way to attribute changes to Sol. If they choose to proceed dirty,
     save the baseline (`git status --porcelain` output plus
     `git diff > "<scratchpad>/pre-route.diff"`); attribution then happens by file
     (see review layer 2), and layer 3's `codex exec review` variant is
     unavailable (it cannot be scoped to the worker's delta) — use the
     Opus-subagent variant scoped to the attributed file set instead.
5. **Worker model:** `gpt-5.6-sol`. Model failures surface only when a dispatch
   actually runs — don't spend a billed probe upfront; let the first build surface
   them. Two failure modes, different fixes:
   - `"requires a newer version of Codex"` → the CLI is stale for this model. Run
     `codex update` (self-updater, no sudo) and retry.
   - Model id genuinely rejected (ids rotate as OpenAI ships releases) → try
     `-m gpt-5.6` (alias routing to Sol). If that is also rejected, run
     `codex update` once (if you haven't already) and retry `gpt-5.6-sol`. Still
     failing → read the `model =` line in `~/.codex/config.toml`; if it names an id
     you have NOT already tried, try that; otherwise switch this run to the Opus
     worker path (announce it) and ask the user in your report to supply a current
     Sol id for future runs (free local check: `codex doctor`; the user can also
     open interactive `codex` and use the `/model` picker). Never just omit `-m` as
     a fallback: the config default is typically `gpt-5.6-sol` — the exact id that
     just failed — so that silently retries the dead model.

   Walk this chain once, in order, never restart it. Always state in the final
   report which model actually ran.

**`codex exec` exits 0 even when the model call fails** (verified live). Never trust
the exit code. A dispatch succeeded only if all three hold: no `ERROR:` lines in its
log, its `-o` last-message file was written, and the expected files actually changed
on disk. This applies to every dispatch — build, fix rounds, and probes.

## The loop

### 1. Plan (you)

Restate the task in one line. Write a concrete, step-by-step plan and save it as
`PLAN.md` at the project root. A good PLAN.md has three sections:

- **Task** — the one-line restatement.
- **Steps** — numbered, specific, implementation-ready.
- **Acceptance criteria** — observable checks you will verify at review time
  (files that must exist, tests that must pass, behaviors that must hold). This
  section is the review contract; write it before Sol starts. Two hard rules:
  - For data or document artifacts, include at least one **content-level**
    criterion — a specific value, row, or decision the output must get right,
    checkable against the source inputs — not just file existence or schema.
  - If the deliverable **mutates existing files** (deletes, moves, renames,
    overwrites), the criteria MUST require a dry-run/preview mode or verification
    against a copy, and must state that nothing runs against the user's real files
    before approval.

Only ask the user clarifying questions if the task is genuinely ambiguous.

### 2. Build (Sol)

If `<project-dir>` is not a git repo, snapshot it first (re-run both lines before
every later fix round too):

```bash
find "<project-dir>" -type f | sort > "<scratchpad>/route-files-before.txt"
touch "<scratchpad>/route-marker"
```

Exception — if the previous dispatch died mid-round (usage limit, stall kill,
crash), do NOT re-snapshot immediately: first run the review-layer-2 `find` and
`comm` against the EXISTING marker and before-list, and fold anything the dead
round touched (or deleted) into the current round's review scope; only then re-run
the two snapshot lines. Re-touching the marker first would erase the dead round's
tracks from every later inventory.

Dispatch the build (add `--skip-git-repo-check` outside a git repo):

```bash
cd "<project-dir>" && codex exec -m gpt-5.6-sol -s workspace-write \
  -c model_reasoning_effort=ultra \
  -o "<scratchpad>/sol-build.txt" \
  "Read PLAN.md at the root of this directory and implement it exactly.
   Do not touch files unrelated to the plan.
   Do not run git commit or any destructive git command (no commit, no push,
   no reset --hard, no force ops) — leave all changes uncommitted for review.
   If your implementation mutates existing files, test it only against copies
   under \$TMPDIR, never against the real data in this directory.
   When done, list every file you created or modified." \
  > "<scratchpad>/sol-build.log" 2>&1
```

- `-s workspace-write` is required — without it Sol runs read-only and cannot
  write files.
- Builds can take many minutes. Run the command in the background (never
  foreground — a foreground timeout would kill a healthy long build), with output
  redirected to a per-round log as shown: the codex banner — including the session
  id — goes to **stderr**, so the `2>&1` is load-bearing.
- After it exits, judge it from the log: `grep -m1 'session id:' <log>` — **save
  this uuid**, fix rounds resume it; `grep -c 'ERROR:' <log>` must be 0; then apply
  the full three-part success check. Never use `codex exec resume --last`: the user
  also runs Codex through the ChatGPT desktop app, so the newest session on disk
  may not be yours.
- Stall detection is by **silence, not elapsed time**: codex streams activity
  continuously while working, so poll the log every couple of minutes and treat the
  run as hung only if the log has not grown for ~10 minutes. A slow build that
  keeps producing output is healthy — do not kill it.

### 3. Review (you — the quality gate)

Adversarial by default: your job is to catch what Sol missed. Never accept the
first pass without checking. Three layers, strongest first:

1. **Run it.** Behavior beats diff-reading — but never mutate the user's real data
   before approval. Read-only deliverables: run on real input. Mutating
   deliverables (delete/move/rename/overwrite): copy the real data into the
   scratchpad and exercise it there, and/or run the dry-run mode against the real
   target and verify the planned actions line by line; the real run happens only
   after approval. If a fix round follows, re-verify on a FRESH copy — never on the
   mangled output of the previous round. For data or document artifacts, "running
   it" means verifying content against ground truth you derive independently: open
   a sample of the source inputs yourself and confirm the corresponding output
   values/rows/decisions are correct. Exists + parses + right columns is not
   verification. Every acceptance criterion in PLAN.md gets checked, not assumed.
2. **Read the diff yourself.** Hunt for correctness bugs, unhandled edge cases,
   security problems, silent scope creep, and files touched outside the plan.
   - Clean git tree: `git diff` is authoritative.
   - Dirty git tree (user chose to proceed): attribute by file. Sol's changes are
     files that are dirty now but were clean in the preflight baseline, plus files
     Sol listed in its final message — cross-check the two lists and treat a
     mismatch as a finding. For files already dirty at baseline, compare against
     `pre-route.diff` before attributing anything in them to Sol; never send Sol
     findings about edits that predate the run.
   - Non-git: derive the changed-file set yourself — never rely on Sol's
     self-report as the inventory:

     ```bash
     find "<project-dir>" -type f -newer "<scratchpad>/route-marker" | sort \
       > "<scratchpad>/route-files-changed.txt"
     find "<project-dir>" -type f | sort \
       | comm -23 "<scratchpad>/route-files-before.txt" - \
       > "<scratchpad>/route-files-deleted.txt"
     ```

     Read every changed file and diff both lists against Sol's self-reported list:
     changed-but-unlisted files are a finding (scope creep or dishonest reporting);
     listed-but-unchanged files mean the build didn't do what it claims. Caveat: in
     synced folders (Dropbox/iCloud) background sync can bump mtimes on unrelated
     files — treat unexpected entries as leads to inspect, not automatic failures.
3. **Optional second opinion.** For risky or large changes. Which variant depends
   on git state and worker availability:
   - **Clean git tree AND Sol available** → Codex's built-in reviewer against the
     uncommitted work:

     ```bash
     cd "<project-dir>" && codex exec review --uncommitted \
       -c model_reasoning_effort=ultra
     ```

     It reviews ALL uncommitted changes and cannot be scoped to the worker's
     delta — that is why it is clean-tree-only. If preflight step 5 fell back to
     a different model id, add `-m <that id>` (`codex exec review` accepts `-m`;
     with no `-m` it inherits the config-default model — typically the dead
     `gpt-5.6-sol` — and fails with exit 0 and no output). Judge this dispatch
     like any other: no review text in the output means the dispatch failed, not
     that there were no findings.
   - **Any other state** — non-git, dirty tree, or the run is on the Opus worker
     path → a FRESH Opus 4.8 subagent (never the builder), handed PLAN.md plus
     the attributed change set from layer 2 (the git diff on a clean tree; the
     attributed file list on a dirty tree; the changed/deleted snapshot lists on
     non-git), instructed to review only those files.

   Either way, treat its findings as leads to verify, not verdicts.

### 4. Fix (Sol, same session)

If anything is wrong, send the specific findings back — resume the build session by
id (add `--skip-git-repo-check` outside a git repo; `<N>` = 1, 2, 3 per round):

```bash
cd "<project-dir>" && codex exec resume <SESSION_ID> \
  -c sandbox_mode=workspace-write \
  -c model_reasoning_effort=ultra \
  -o "<scratchpad>/sol-fix-<N>.txt" \
  "Fix these review findings, nothing else: <numbered findings>" \
  > "<scratchpad>/sol-fix-<N>.log" 2>&1
```

- **`resume` accepts NO `-s`, `-C`, or `--add-dir` flags** (hard parse error), and
  it takes its working directory from your shell cwd — hence the `cd` in the same
  command. Whether it inherits the build's sandbox and effort proved unreliable in
  live tests, so always re-assert both via `-c` exactly as shown; a fix round that
  silently runs read-only replies "workspace is read-only", writes nothing, and
  still exits 0. If the build needed `--add-dir`, skip resume for that round and
  use a fresh `codex exec` with the full build flags instead.
- A resume that hits the git-repo check prints "Not inside a trusted directory…"
  and exits 0 with **no** `ERROR:` line — the missing `-o` file is what exposes it.
- Pass `-m` only if preflight fell back to a different id; the session already
  routes to the build's model.
- Apply the same three-part success check to every fix round, using that round's
  `-o` file and log.

If the resume fails (expired/missing session), start a fresh `codex exec` with the
same flags as the build, pointing at PLAN.md plus the findings — this replacement
consumes the fix round it replaces, it never adds one.

Repeat build → review → fix. **Caps:** 3 fix rounds; and at most 2 retries per
infrastructure-failure type per run (stale-CLI update-and-retry, stall
kill-then-resume-or-split — either worker, expired-session fresh restart). The model fallback chain
is walked once. When a cap is exhausted, stop and report honestly what passes, what
still fails, and why — do not keep billing rounds at a failure that is not
improving, and do not quietly finish the work yourself.

### The Opus worker path (fallback)

When Worker triage sends the build (or the remaining fix rounds) to Opus 4.8, the
loop is identical — plan, review layers, caps, and report all stand. Only the
dispatch mechanics change:

- **Build:** spawn ONE `general-purpose` subagent via the Agent tool with
  `model: "opus"`. Its prompt is the same contract as the codex build prompt:
  implement PLAN.md exactly; touch nothing unrelated to the plan; no `git commit`
  or destructive git commands — leave all changes uncommitted for review; test
  mutating code only against copies under the scratchpad, never the real data; end
  by listing every file created or modified. There is no OS-level sandbox on this
  path — **the prompt is the sandbox** — so state the writable root explicitly:
  "Write only inside `<project-dir>` and `<scratchpad>`, using absolute paths for
  every write (relative paths stray when your cwd resets between calls); if you
  touched ANY path outside those two roots, even accidentally, say so explicitly
  in your final report." Add: "Do not access the network" unless the user approved
  network for this run. This full contract goes into EVERY fresh Opus spawn —
  build, takeover, or replacement. **Save the agent id** the Agent tool returns —
  write it to `<scratchpad>/opus-agent-id.txt` immediately (the codex session id
  survives in its log file; this id has no disk artifact unless you make one).
- **Execution and stalls, adapted:** run the subagent in the background (the
  harness default) — never synchronously, for the same reason the codex build is
  never foregrounded — and let the completion notification end the wait. There is
  no log file to poll here, so the codex silence rule does not apply: if the build
  has run far longer than the plan warrants, check the agent via TaskGet/TaskList
  and treat it as stalled only if it shows no progress across two checks ~10
  minutes apart. Then TaskStop it and either SendMessage the same agent a narrower
  instruction (the analogue of kill-then-resume) or spawn a fresh agent on a split
  plan — either way it counts against the same 2-retry stall cap.
- **Mid-loop takeover (Sol built, Opus fixes):** when triage moves remaining fix
  rounds here, there is no existing subagent to continue — spawn ONE fresh agent
  under the full build contract above, but frame it as a fix, not a build: hand it
  PLAN.md, the changed-file list, and the numbered findings, and instruct it to
  "apply these numbered findings to the existing implementation only — do not
  re-implement PLAN.md or rewrite files with no findings against them." This
  dispatch IS the fix round being retried; the worker switch never adds a round.
  From then on this agent is the "same subagent" that later fix rounds continue.
- **Fix rounds:** continue the SAME subagent by its saved id via SendMessage with
  the numbered findings — the Agent-tool analogue of `codex exec resume`, and it
  keeps the worker's context. If the agent is gone, spawn a fresh one under the
  full build contract with PLAN.md plus the findings (this replacement consumes
  the fix round it replaces, it never adds one — same as a codex fresh restart).
- **Success check, adapted:** no `-o` file or ERROR-line grep here; instead
  require the subagent's final report to list its changed files, confirm the
  expected files actually changed on disk, and save each round's final report
  verbatim to a per-round scratchpad file (`opus-build.txt`, `opus-fix-<N>.txt`)
  the moment it returns — the Opus analogue of the `-o` files, and the evidence
  trail the report cites. The non-git snapshot mechanics and dirty-tree
  attribution rules carry over as-is, but their COVERAGE does not: under codex
  the sandbox physically confined writes to `<project-dir>` (plus
  `/tmp`/`$TMPDIR`), so the snapshot was a complete inventory; the Opus agent has
  no OS sandbox, so out-of-tree writes are possible and the snapshot or `git
  diff` will never show them. Compensate at review time: treat any out-of-tree
  write — self-reported or discovered — as a review finding, and run a cheap
  sweep of the likely stray zone (`find "$HOME" -maxdepth 2 -type f -newer
  "<scratchpad>/route-marker" 2>/dev/null | grep -v -e "<project-dir>" -e
  "<scratchpad>" -e "/Library/"`); on git runs, `touch "<scratchpad>/route-marker"`
  before each Opus dispatch so the sweep has a reference point. Treat hits as
  leads to inspect (background processes bump mtimes), not automatic failures.
- **Second opinion:** a FRESH Opus subagent (never the builder) reviewing the
  attributed changed-file set adversarially — the diff where one exists, otherwise
  the changed-file lists per layer 3's scoping rules. Leads to verify, not
  verdicts.
- If the Opus path is also unavailable, stop and report — the boss still does not
  build.

### 5. Report (you)

- The one-line task and the plan you wrote.
- What the worker built, what you sent back each round, and what the final state
  is — the per-round `sol-*.txt` / `sol-*.log` files (Sol rounds) and `opus-*.txt`
  reports (Opus rounds) in the scratchpad are the evidence trail, alongside the
  run's attribution artifacts (`git diff`, or `route-files-*.txt` /
  `pre-route.diff` on non-git / dirty-tree runs).
- Verification evidence: which acceptance criteria you checked and how.
- Which worker built each round — Sol (and which model id, per preflight step 5) or
  the Opus 4.8 fallback — and, if triage switched mid-run, why (quote the
  usage-limit message and its reset time if that was the trigger).
- PLAN.md: after approval, delete it if this run created it (its content lives in
  your report); keep it if it existed before this run or the user asked to keep
  it. If Sol committed it despite instructions, revert that commit (or ask the
  user) rather than deleting a tracked file.

## Sandbox and escalation rules

- Default sandbox is `workspace-write` with **no network**. If the task genuinely
  needs network (package installs, downloads), **ask the user first**, then add
  `-c sandbox_workspace_write.network_access=true` for that run only (fix rounds
  included, since resume settings are re-asserted per round).
- Never use `-s danger-full-access` or `--dangerously-bypass-approvals-and-sandbox`.
- Sol writes only inside `<project-dir>` (plus `/tmp` and `$TMPDIR`, which the
  sandbox always allows); pass extra writable paths explicitly with `--add-dir` on
  the build if the task requires them (and say so in the report).

## Rules

- You (the boss) never write the implementation. A worker does. You plan and review.
- The chain of command is fixed: you plan and orchestrate first; delegated builds
  go Sol (Ultra Mode) → Opus 4.8 subagent → stop and report. Never hand build work
  to your own subagents while Sol is available, and never build it yourself when
  both workers are unavailable.
- Loop until you approve. Never accept the first pass unverified.
- Treat your review as adversarial: assume Sol missed something and go find it.
- Report failures honestly — a capped-out loop with open findings is a valid
  outcome; silently patching Sol's work yourself is not.
- One exception: after final approval, you may make a purely cosmetic touch-up
  (typo in a comment, trailing whitespace) yourself — flag it in the report.

## Notes

- **Orchestrator model:** written for Fable 5 but runs identically under Opus 4.8
  or any Claude — nothing here is Fable-specific. On Opus 4.8, the
  `fable5-working-style` skill (if installed) has useful delegation-discipline
  patterns, but it is not required.
- **Codex plugin (optional):** the `openai/codex-plugin-cc` plugin for Claude Code
  adds user-facing commands like `/codex:review` and `/codex:rescue`. This skill
  does not depend on it — everything runs through the codex CLI directly.
- **Cost awareness:** each build/fix round bills the user's ChatGPT/OpenAI account,
  and Ultra Mode draws hard on the windowed (typically 5-hour) Codex usage pool —
  GPT-5.6-class models are reported to drain it fast. Keep the plan tight so one
  build round usually suffices; don't dispatch exploratory busywork to Sol. The
  Opus fallback bills the user's Anthropic side instead.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `requires a newer version of Codex` | Stale CLI — `codex update`, then retry the same dispatch |
| `model not found` / id rejected | Fallback chain in preflight step 5. Free local check: `codex doctor` (prints config default model, auth, connectivity); user can list valid ids via the `/model` picker in interactive `codex`. To probe a candidate: `cd "<project-dir>" && codex exec -m <id> --skip-git-repo-check -o "<scratchpad>/probe.txt" "reply OK"` — the id works only if the log has no `ERROR:` lines AND the `-o` file was written (exit code is always 0). Never probe by omitting `-m` |
| `not logged in` | User runs `! codex login` |
| `You've hit your usage limit` / `429` / rate limit | Sol's usage window is exhausted — switch to the Opus worker path (Worker triage), record the reset time, and note the switch in the report. Later runs go back to Sol first |
| `Supported values are: … 'xhigh'` (ultra rejected) | This model/CLI combo lacks `ultra` — re-dispatch with `-c model_reasoning_effort=xhigh` |
| `Not inside a trusted directory` | Add `--skip-git-repo-check` — needed on every call outside a git repo, including resumes; note it exits 0 with no `ERROR:` line, so the missing `-o` file is the tell |
| Sol says it cannot write files | Build: you forgot `-s workspace-write`. Fix round: you forgot `-c sandbox_mode=workspace-write` (resume has no `-s` flag and can revert to read-only) |
| `401` / `unauthorized` / auth error mid-run | Run `codex login status` (free, local). Logged out → user runs `! codex login`, then resume Sol — no round or retry consumed. Logged in but dispatches still fail → service-side auth outage: switch to the Opus worker path (Worker triage) and say why in the report |
| Network errors during build | Sandbox blocks network by default — see escalation rules |
| Codex build stalls (log unchanged ~10 min) | Kill it, resume the session by id with a narrower instruction, or split the plan (counts against the 2-retry infrastructure cap) |
| Opus build never returns | No log exists on this path — the codex stall row above does not apply. Check the agent via TaskGet/TaskList; stalled = no progress across two checks ~10 min apart. TaskStop it, then SendMessage a narrower instruction or spawn a fresh agent on a split plan (counts against the 2-retry stall cap) |
| Opus agent's report mentions paths outside `<project-dir>`/`<scratchpad>` | No sandbox enforced the writable root — inspect each path, decide keep/revert with the user, and record it as a finding in the report |
| Review findings reference code Sol never wrote | Tree was dirty at start — re-check against the preflight baseline (`pre-route.diff`); only send Sol findings on files it actually touched |
