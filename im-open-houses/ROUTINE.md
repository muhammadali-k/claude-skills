# Cloud routine — "IM virtual open houses — daily 8 AM scan"

Created 2026-09-01 via the Claude Code remote-trigger API. Re-create with the same values if
it is ever deleted (routines can be deleted only at https://claude.ai/code/routines).

| Setting | Value |
|---|---|
| Name | IM virtual open houses — daily 8 AM scan |
| Schedule | `0 15 * * *` (UTC) = **08:00 America/Phoenix every day** (Arizona has no DST, so this never drifts) |
| Model | `claude-opus-4-8` |
| Environment | Default Anthropic cloud (`env_01UnLGxvEXW88TxLRLjxDq6T`) |
| Repository | https://github.com/muhammadali-k/claude-skills (cloned; the skill lives at `im-open-houses/`) |
| Connectors | Gmail (permitted: send_message, create_draft, search_threads, get_message), Google-Calendar (permitted: create_event, list_calendars, search_events, list_events, get_event, update_event) |
| Tools | routine default set (Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, …) + the two connectors |
| Routine id | `trig_011fmRM5qt8BQbFDzfGzYvRZ` |

## Prompt (verbatim)

```
You are running the daily scan of the `im-open-houses` skill. The repository is checked out; the skill is the folder `im-open-houses/` (read `im-open-houses/SKILL.md` first, then `references/sources.md` and `references/candidate-schema.md`). Work only inside `im-open-houses/`.

Goal: find every U.S. Internal Medicine residency VIRTUAL open house / virtual information session / meet-and-greet / applicant webinar that has been announced for today or later, report only what is new since the last run, email the digest, put the events on Google Calendar, and commit the state.

Steps — do all of them, in order:
1. `cd im-open-houses` and set `RUN_DATE=$(TZ=America/Phoenix date +%F)`. Then sync state: `git fetch origin claude/im-open-houses-state 2>/dev/null && git checkout origin/claude/im-open-houses-state -- data/events.json data/watch_state.json 2>/dev/null || true` (ignore errors if that branch does not exist). Run `python3 scripts/openhouse.py status`.
2. Run `python3 scripts/harvest.py --run-date $RUN_DATE` (takes 3–5 minutes; it is rate-limit aware). Read `data/harvest_$RUN_DATE.json`: `auto_candidates`, `leads`, `watch_changes`, `errors`.
3. Run `python3 scripts/openhouse.py queries --run-date $RUN_DATE` and execute EVERY printed query with WebSearch. Open every promising result with WebFetch (also every `lead` and every `watch_changes` page whose passage mentions a date). Extract: full official program name + state, event title, date, start/end time with the timezone as printed, registration link (or the coordinator email), audience, and the page URL you read it on. Verify the YEAR from the page text (programs leave last year's announcement up; a weekday+date must match the current year). Drop in-person-only events, non-IM specialties, fellowships, events already past, and interview-invitee-only sessions. Date unknown but clearly announced → keep with `date_tbd: true`.
4. Write `data/candidates_$RUN_DATE.json` (schema: `references/candidate-schema.md`) containing the reviewed auto_candidates plus everything you found. Run `python3 scripts/openhouse.py validate data/candidates_$RUN_DATE.json`, fix any error, then `python3 scripts/openhouse.py ingest data/candidates_$RUN_DATE.json --run-date $RUN_DATE` and `python3 scripts/openhouse.py digest --run-date $RUN_DATE`. Zero new events is a valid, honest result — never pad the digest.
5. Email the digest with the Gmail connector to kmuhammadali0224@gmail.com. Subject: `IM open houses — $RUN_DATE: <N> new`. Body: the digest converted to simple HTML (headings, numbered list, links clickable) — never raw markdown `#` characters. Send even when N = 0 (one line saying nothing new + what was checked).
6. Calendar: `python3 scripts/openhouse.py calendar-json --run-date $RUN_DATE` prints the events not yet on the calendar. Create each one on the user's primary Google Calendar with the Google-Calendar connector's create_event tool (load it with ToolSearch `select:mcp__Google-Calendar__create_event`): use `summary`, `description`, and `start`/`end` with the event's own `timezone` (or `start_date`/`end_date` for all-day). After each successful creation run `python3 scripts/openhouse.py mark <id> announced --calendar-added` (if the event's current status is `registered`, use `registered` instead of `announced`). If no create tool exists, say so in the run note and leave the events queued.
7. `python3 scripts/openhouse.py commit-run --run-date $RUN_DATE`.
8. Commit and push state: `git config user.email noreply@anthropic.com && git config user.name Claude && git add data/events.json data/watch_state.json data/runs/ data/candidates_$RUN_DATE.json data/harvest_$RUN_DATE.json && git commit -m "im-open-houses: scan $RUN_DATE (<N> new)"` then `git push origin HEAD:main || git push origin HEAD:claude/im-open-houses-state`. Never force-push, never touch files outside `im-open-houses/data/`. If both pushes are refused (403), say so in the run note; do not retry.
9. Final message: paste the digest verbatim, then a run note with: number of WebSearch queries run, pages opened, harvest errors, and whether email / calendar / push each succeeded or failed (say which command failed and why). If Gmail or Calendar refused, say so plainly — do not claim delivery.

Rules: everything in the digest must carry the URL it was read from; never invent dates or links; if you could not open a page (egress blocked, 403, timeout) do NOT assign a date from search snippets — record the event with `date_tbd: true` and say in `notes` which URL could not be opened; never register the user for anything (registration is done separately from his laptop); do not edit the skill's scripts or references. The applicant is a non-US IMG applying Internal Medicine in ERAS 2027 who needs visa sponsorship, so IMG-specific sessions and visa-sponsoring programs matter most, but report all IM open houses.
```

## Test run 2026-09-01 (session cse_01XoTH94ZyjSpr3wypHZei5o) — what worked and what the user must fix
- Worked: clone, scripts, 25 WebSearch queries, Gmail send (digest delivered), commit-run, push notification.
- **Egress proxy blocked every program website** (harvest.py: 39× "Tunnel connection failed: 403"; WebFetch: EGRESS_BLOCKED). Only WebSearch (server-side) worked, so the run assigned a wrong tentative date to Carilion from a search snippet. **Fix (user):** in the Default cloud environment settings at claude.ai/code → Environments, set *Network access* to **Full** (the default "Trusted" allowlist only covers package registries/GitHub). Until then, discovery is search-snippet-only and the prompt rule above forces `date_tbd`.
- **Google Calendar connector exposed only `search_events`** inside the routine (no create). The routine's `mcp_connections` now lists `permitted_tools` including `create_event`; re-test. If it still cannot create, calendar entries are added from the laptop (`/im-open-houses scan --local`), and `calendar-json` keeps queueing them.
- **GitHub push denied (403)**: "Claude doesn't have GitHub access to muhammadali-k/claude-skills". **Fix (user):** install the Claude GitHub App for the `muhammadali-k` account with access to `claude-skills` (https://github.com/apps/claude/installations/select_target) or reconnect GitHub at https://claude.ai/customize/connectors?auth_start=github. Until then the state file is not persisted by the cloud run, so a newly found event will be re-reported each morning until it is ingested from the laptop.

## Notes
- The routine's run history is at https://claude.ai/code/routines/trig_011fmRM5qt8BQbFDzfGzYvRZ; each run is a session the user can open and continue.
- State persistence relies on `git push` from the cloud session. Pushes to `main` are expected to work (the repo is the user's own, unprotected); if they are refused, the fallback branch `claude/im-open-houses-state` is used and read back at the start of every run, so nothing is lost. Merge it into `main` occasionally from the laptop: `git fetch && git checkout origin/claude/im-open-houses-state -- im-open-houses/data && git commit -am "merge open-house state"`.
- To run it now: `/schedule` → Run, or RemoteTrigger `{action:"run", trigger_id:"trig_011fmRM5qt8BQbFDzfGzYvRZ"}`.
