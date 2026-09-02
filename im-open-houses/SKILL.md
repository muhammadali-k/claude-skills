---
name: im-open-houses
description: >-
  Daily watch for newly announced VIRTUAL OPEN HOUSES (virtual info sessions,
  meet-and-greets, applicant Q&A webinars) of U.S. Internal Medicine residency
  programs, with a de-duplicated 8 AM digest and on-request registration on the
  applicant's behalf. Use whenever the user asks about IM residency virtual open
  houses / info sessions / meet-the-program events, "any new open houses today",
  "sign me up for #2", "register me for the X open house", "what open houses are
  coming up", or invokes /im-open-houses — even without naming the skill. Two
  modes: `scan` (find + digest; runs daily in a cloud routine on Opus 4.8 and
  emails + calendars the results) and `signup N[,N]|all|EVENT_ID` (browser-driven
  registration with khan.muhammad2@mayo.edu from the local machine). Tags every
  event against the applicant's tiered 568-program list (tier, priority rank,
  visa, grad-year cutoff). Not for interview scheduling, program comparison, or
  general residency advice (see residency-program-finder / new-im-programs).
---

# im-open-houses — IM residency virtual open house watcher + registrar

Programs announce virtual open houses quietly (a program-site banner, an X/Instagram
post, a coordinator email, a Google Form link) and seats or the date pass before an
applicant hears about them. This skill checks the web every morning, reports only what
is **new since the last run**, tags each event against the applicant's own program
tiers, and registers him for the ones he picks.

Two entry points:

| Mode | Where it runs | What it does |
|---|---|---|
| `/im-open-houses scan` | Cloud routine, daily 08:00 America/Phoenix (15:00 UTC), model `claude-opus-4-8`; also runnable locally | Discover → ingest/de-dupe → digest → email + Google Calendar → commit state |
| `/im-open-houses signup 1,3` / `all` / `oh_xxxxxxxxxx` | Local Claude Code with Chrome (bypass-permissions session) | Registers the applicant for chosen events using the local-only profile |

Applicant facts for forms live in **`data/profile.local.json`** (gitignored; contains IDs
and phone). The public repo copy never has it — if it is missing, ask the user for the
fields a form needs and recreate it from `references/registration.md` § Profile schema.

---

## A. `scan` — the daily run (also what the cloud routine executes)

Read `references/sources.md` first: it ranks every source that was live-tested, says
which are fetchable headlessly, and gives the exact search-query bank. Then:

### A1. Anchor the run
```
RUN_DATE=$(TZ=America/Phoenix date +%F)
cd <skill dir>            # ~/.claude/skills/im-open-houses locally; im-open-houses/ in the repo
python3 scripts/openhouse.py status
```
Never trust a date from memory; the routine prompt gives none.

### A2. Discover candidates (the only judgment-heavy step)
Goal: every IM (categorical; also prelim / Med-Peds when clearly IM-run) **virtual** open
house / info session / meet-and-greet / applicant webinar whose date is **today or later**,
or that is announced with the date still to come. In-person-only events are out of scope
(note them only if they also offer a virtual option).

1. **Search bank.** `python3 scripts/openhouse.py queries` prints ~25 queries. Run every one
   with WebSearch (they are cheap). Prefer results dated within the last ~10 days but open
   anything that looks like a current-season announcement — programs post the same page
   every year, so **verify the year in the page text**, not the URL.
2. **Fixed sources.** Fetch each source listed in `references/sources.md` § Fixed sources
   (aggregator pages, calendars, community trackers). Follow the per-source parsing notes.
3. **Open every promising hit** (WebFetch or `curl -sL`) and extract: program (full official
   name + state), event title, date, start/end time **with timezone as printed**, the
   registration URL (Zoom/Google Form/Eventbrite/etc.; if "email the coordinator", record
   `platform: "email"` and the address in `notes`), audience (all applicants / IMGs /
   students), and the source URL you read it on.
4. Drop anything from a previous season (2025 or earlier dates), anything not internal
   medicine (FM, peds, EM, surgery — a common false positive), fellowships, and anything
   that is clearly not virtual. When unsure about the date, keep it with `date_tbd: true`
   and say why in `notes`.
5. Write the candidates to `data/candidates_<RUN_DATE>.json` using the schema in
   `references/candidate-schema.md`. Then `python3 scripts/openhouse.py validate <file>`.

A typical day yields 0–10 new events; a first run of the season may yield 30+. **An empty
day is a valid result** — report it honestly instead of padding with stale events.

### A3. Ingest + digest (deterministic)
```
python3 scripts/openhouse.py ingest data/candidates_$RUN_DATE.json --run-date $RUN_DATE
python3 scripts/openhouse.py digest --run-date $RUN_DATE      # writes data/runs/$RUN_DATE.md, prints it
```
`ingest` de-duplicates by (normalised program name + event date), fuzzy-matches every
program to `references/my_programs.json` (tier 1–5, ★ priority rank, visa, grad-year-cutoff
risk, or ⛔ excluded), and keeps the first registration link it saw. The digest lists **New
since last run** (numbered, with the `/im-open-houses signup N` reply line), **next 7 days**,
**later**, and **date-TBD** sections.

### A4. Deliver
1. **Email** the digest markdown (rendered as simple HTML or plain text — do not paste raw
   `#` headings into an HTML body) via the Gmail connector to **kmuhammadali0224@gmail.com**,
   subject `IM open houses — <RUN_DATE>: N new`. Send it even when N = 0 (say so in one line).
2. **Google Calendar**: `python3 scripts/openhouse.py calendar-json --run-date $RUN_DATE`
   prints the events not yet on the calendar (excluded programs are omitted). Create each
   with the Google-Calendar connector (summary, description, start/end with the event's own
   timezone; all-day when `start_date` is given), then
   `python3 scripts/openhouse.py mark <id> announced --calendar-added` (or keep the current
   status: `mark <id> registered --calendar-added` if it was already registered).
3. Flip the batch: `python3 scripts/openhouse.py commit-run --run-date $RUN_DATE`
   (new → announced, so tomorrow's digest only shows what is genuinely new).

### A5. Persist state (cloud routine)
The state file **`data/events.json`** is the memory between runs; it must be committed.
```
git add im-open-houses/data/events.json im-open-houses/data/runs/ im-open-houses/data/candidates_*.json
git commit -m "im-open-houses: scan $RUN_DATE (N new)"
git push origin HEAD:main || git push origin HEAD:claude/im-open-houses-state
```
If the push to `main` is refused, push to the `claude/im-open-houses-state` branch and, at
the **start** of every run, do `git fetch origin claude/im-open-houses-state && git checkout
origin/claude/im-open-houses-state -- im-open-houses/data/events.json` (ignore the error if
the branch does not exist) so the newest state wins. Never rewrite history; never touch
files outside `im-open-houses/data/`.

### A5b. Local-only extras (`scan --local`, from the laptop with Chrome)
- **OpenHouse aggregator** (`residency-open-house.vercel.app`, community-sourced, ~100 new
  listings/week): open it in a new Chrome tab. If the listings render (the user is signed in),
  filter Specialty = Internal Medicine and add upcoming rows to the candidates file
  (`source_kind: "aggregator"`). If it shows the sign-in landing page, skip it and say so —
  **never sign in, accept terms, or call its API on his behalf.**
- Google search with `tbs=qdr:d` and X/Instagram search in Chrome for the query bank.
- Then continue with A3–A4 (email/calendar via connectors) and commit as in A5.

### A6. Final message of the run
Print the digest verbatim, then a 3-line run note: sources checked (counts), anything that
failed to fetch, and whether email/calendar/commit succeeded. That final message is what the
user sees in the routine session.

---

## B. `signup` — register on the applicant's behalf (local, browser)

Only after the user has said which events. Never register for an event he did not pick.

1. `python3 scripts/openhouse.py status` and read `data/events.json`; map the user's numbers
   (from today's digest order) or `oh_` ids to events. Skip events already `registered`.
2. Load `data/profile.local.json`. If absent, ask for the fields in
   `references/registration.md` § Profile schema and write the file (gitignored).
3. Follow **`references/registration.md`** — it has the per-platform playbooks (Zoom
   webinar/meeting registration, Google Forms, Microsoft Forms, Eventbrite, Qualtrics,
   REDCap, Calendly, mailto) and the field-mapping table (which profile value goes in
   which question, how to answer "Are you an IMG?", "visa sponsorship needed?", "questions
   for the panel", etc.).
4. **Google Forms: use the headless POST recipe in `references/registration.md` first** (the
   Chrome tool cannot toggle Google Forms radio buttons — verified 2026-09-01). For everything
   else use Chrome (`mcp__claude-in-chrome__*`): open the registration URL in a **new tab**, fill
   the form, screenshot the filled form **before** submitting, submit, screenshot the
   confirmation, and record it:
   `python3 scripts/openhouse.py mark <id> registered --confirmation "<what the page said>"`.
5. If a form asks something not in the profile (e.g. a program-specific question, an ID
   he has not shared), **stop and ask** — do not invent. If it needs an email confirmation
   click, tell the user to check the Mayo inbox.
6. For `platform: "email"` events, draft the email (Gmail connector or `mailto:`) from the
   template in `references/registration.md`, show it, and send only on approval.
7. Report: one line per event — registered / needs-your-input / failed, with the
   confirmation text and screenshot path.

---

## Files

- `scripts/openhouse.py` — stdlib CLI: `ingest`, `validate`, `digest`, `commit-run`,
  `calendar-json`, `mark`, `match`, `queries`, `status`.
- `references/sources.md` — live-tested source ranking, fetchability, query bank, pitfalls.
- `references/candidate-schema.md` — JSON schema the discovery step must produce.
- `references/registration.md` — per-platform registration playbooks + profile schema + email template.
- `references/my_programs.json` — the applicant's 568-program tiered list (2026-07-19 sweep;
  name/city/state/tier/priority/visa/grad-cutoff only — no personal data).
- `data/events.json` — state (committed). `data/runs/<date>.md` — daily digests.
  `data/candidates_<date>.json` — what discovery found that day (audit trail).
- `data/profile.local.json` — **gitignored** registration profile.
- `ROUTINE.md` — the exact cloud-routine prompt and configuration, for re-creating it.

## Guarantees
- **No repeats:** an event is "new" exactly once; `events.json` remembers everything seen.
- **No silent filtering:** excluded/no-visa programs still appear in the digest (tagged ⛔),
  only the calendar skips them.
- **No fabrication:** every event carries the URL it was read from; dates come from the
  page text, and TBD is allowed.
- **No unrequested sign-ups:** registration only for events the user named, with the
  Mayo email, never storing IDs in git.
