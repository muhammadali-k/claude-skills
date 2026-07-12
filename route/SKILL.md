---
name: route
description: >-
  On-demand two-model build loop: the Claude session (Fable 5 today; Opus 4.8 or any
  Claude works identically) is the BOSS — it plans, dispatches, and reviews. OpenAI's
  GPT-5.6 Sol, driven headlessly through the codex CLI, is the WORKER — it builds and
  fixes. The loop repeats build → review → fix until the boss approves. Works for any
  buildable task, not just code: analysis scripts, data-extraction pipelines, document
  or file generation — anything where Sol writes files and the boss can verify the
  result against a plan. Trigger ONLY when the user types /route, says "route this",
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
     `--skip-git-repo-check`; review layer 2 uses its file-snapshot variant and
     layer 3 is skipped (`codex exec review` needs a repo).
   - Git repo → run `git status --porcelain`. If the tree is dirty, tell the user
     and recommend committing or stashing first — a clean baseline is the only
     reliable way to attribute changes to Sol. If they choose to proceed dirty,
     save the baseline (`git status --porcelain` output plus
     `git diff > "<scratchpad>/pre-route.diff"`); attribution then happens by file
     (see review layer 2) and layer 3 is skipped.
5. **Worker model:** `gpt-5.6-sol`. Model failures surface only when a dispatch
   actually runs — don't spend a billed probe upfront; let the first build surface
   them. Two failure modes, different fixes:
   - `"requires a newer version of Codex"` → the CLI is stale for this model. Run
     `codex update` (self-updater, no sudo) and retry.
   - Model id genuinely rejected (ids rotate as OpenAI ships releases) → try
     `-m gpt-5.6` (alias routing to Sol). If that is also rejected, run
     `codex update` once (if you haven't already) and retry `gpt-5.6-sol`. Still
     failing → read the `model =` line in `~/.codex/config.toml`; if it names an id
     you have NOT already tried, try that; otherwise STOP and ask the user for a
     current model id (free local check: `codex doctor`; the user can also open
     interactive `codex` and use the `/model` picker). Never just omit `-m` as a
     fallback: the config default is typically `gpt-5.6-sol` — the exact id that
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

Dispatch the build (add `--skip-git-repo-check` outside a git repo):

```bash
cd "<project-dir>" && codex exec -m gpt-5.6-sol -s workspace-write \
  -c model_reasoning_effort=high \
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
3. **Optional second opinion (clean git trees only).** For risky or large changes,
   run Codex's built-in reviewer against the uncommitted work:

   ```bash
   cd "<project-dir>" && codex exec review --uncommitted \
     -c model_reasoning_effort=xhigh
   ```

   It reviews ALL uncommitted changes and cannot be scoped to Sol's delta, so skip
   it when the tree was dirty at preflight. Treat its findings as leads to verify,
   not verdicts.

### 4. Fix (Sol, same session)

If anything is wrong, send the specific findings back — resume the build session by
id (add `--skip-git-repo-check` outside a git repo; `<N>` = 1, 2, 3 per round):

```bash
cd "<project-dir>" && codex exec resume <SESSION_ID> \
  -c sandbox_mode=workspace-write \
  -c model_reasoning_effort=high \
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
kill-then-resume-or-split, expired-session fresh restart). The model fallback chain
is walked once. When a cap is exhausted, stop and report honestly what passes, what
still fails, and why — do not keep billing rounds at a failure that is not
improving, and do not quietly finish the work yourself.

### 5. Report (you)

- The one-line task and the plan you wrote.
- What Sol built, what you sent back each round, and what the final state is (the
  per-round `sol-*.txt` / `sol-*.log` files in the scratchpad are the evidence
  trail).
- Verification evidence: which acceptance criteria you checked and how.
- Which worker model actually ran (preflight step 5).
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

- You (the boss) never write the implementation. Sol does. You plan and review.
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
- **Cost awareness:** each build/fix round bills the user's ChatGPT/OpenAI account.
  Keep the plan tight so one build round usually suffices; don't dispatch
  exploratory busywork to Sol.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `requires a newer version of Codex` | Stale CLI — `codex update`, then retry the same dispatch |
| `model not found` / id rejected | Fallback chain in preflight step 5. Free local check: `codex doctor` (prints config default model, auth, connectivity); user can list valid ids via the `/model` picker in interactive `codex`. To probe a candidate: `cd "<project-dir>" && codex exec -m <id> --skip-git-repo-check -o "<scratchpad>/probe.txt" "reply OK"` — the id works only if the log has no `ERROR:` lines AND the `-o` file was written (exit code is always 0). Never probe by omitting `-m` |
| `not logged in` | User runs `! codex login` |
| `Not inside a trusted directory` | Add `--skip-git-repo-check` — needed on every call outside a git repo, including resumes; note it exits 0 with no `ERROR:` line, so the missing `-o` file is the tell |
| Sol says it cannot write files | Build: you forgot `-s workspace-write`. Fix round: you forgot `-c sandbox_mode=workspace-write` (resume has no `-s` flag and can revert to read-only) |
| Network errors during build | Sandbox blocks network by default — see escalation rules |
| Build stalls (log unchanged ~10 min) | Kill it, resume the session by id with a narrower instruction, or split the plan (counts against the 2-retry infrastructure cap) |
| Review findings reference code Sol never wrote | Tree was dirty at start — re-check against the preflight baseline (`pre-route.diff`); only send Sol findings on files it actually touched |
