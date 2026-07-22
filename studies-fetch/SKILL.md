---
name: studies-fetch
description: >-
  Daily cross-sectional literature pull for hematology, oncology, and medical AI.
  Queries a curated set of high-impact journals via the PubMed E-utilities API,
  removes any study already shown on a previous day, and produces a ranked,
  grouped markdown digest (Heme / Onc / Medical AI) with relevance notes. Use
  whenever the user wants their daily/new studies update, morning literature
  briefing, "what's new in heme/onc/AI today", "fetch today's papers", "run my
  studies digest", or invokes /studies-fetch. Each run is a self-contained
  snapshot for one day; studies never repeat across days because seen PubMed IDs
  are persisted. Journal list lives in references/journals.json and is easy to edit.
---

# studies-fetch — daily heme/onc + medical-AI literature digest

Pull new studies from ~44 high-impact journals, drop anything already seen on a
prior day, and hand the user a clean, ranked, grouped digest. Source is the
PubMed E-utilities API (free, no key). Everything is stdlib Python — no installs.

## Design guarantees (why it works the way it does)

- **No repeats.** Every PMID ever emitted is recorded in `data/seen_ids.json`
  with the date added. A new run filters candidates against this store, so a
  study appears in exactly one day's digest — even if PubMed re-indexes it.
- **Cross-sectional for one day.** Each run writes one dated snapshot
  (`data/digest_<date>.json` + `.md`). The default rolling window is 2 days so
  that papers whose indexing lagged by a day are still caught, without ever
  duplicating (the seen-store handles that).
- **Curated + validated.** Journals are defined in `references/journals.json`
  by MEDLINE title abbreviation. Dedicated heme/onc/AI journals return *all* new
  papers; broad general journals (NEJM, Lancet, JAMA, Nature, Science, Nature
  Medicine) are topic-filtered to heme/onc/AI content only.

## Standard run (do this when the user asks for their digest)

1. **Fetch.** From the skill directory, run:
   ```
   python scripts/fetch_pubmed.py fetch --days 2
   ```
   It prints a summary line (`NEW STUDIES: N ...`) and the path to the digest
   JSON. Use the absolute path
   `C:\Users\m293811\.claude\skills\studies-fetch\scripts\fetch_pubmed.py`.

2. **Read** the `DIGEST_JSON` file it reports (`data/digest_<date>.json`). Each
   record has: `title, journal, domain, authors, pubdate, doi, url, abstract`.

3. **Compose the digest markdown.** Group into three sections in this order —
   **🩸 Hematology**, **🎗 Oncology**, **🤖 Medical AI**. Rules:
   - `domain` maps directly: `heme`→Hematology, `onc`→Oncology, `medai`→Medical AI.
   - For `genmed` records, read the title/abstract and file each under the single
     best-fitting section (a CAR-T trial in NEJM → Hematology; an LLM triage study
     in JAMA → Medical AI).
   - **Within each section, rank most-important first** using your judgment:
     phase 3 / practice-changing trials, large cohorts, and landmark journals
     above small series, editorials, and correspondence.
   - For each study, one bullet:
     `**[Title](url)** — *Journal* · Authors · date · DOI`
     then a sub-line: a **1–2 sentence relevance note** written from the abstract
     (what's new / why it matters for a heme-onc + AI researcher). Do not just
     restate the title.
   - If a section is empty, print `_No new studies today._`

4. **Save + present.** Write the markdown to
   `data/digest_<date>.md` (same date as the JSON) and also present it inline to
   the user. End with a one-line footer: total new studies, the per-domain
   counts, and the seen-store size (from the script's summary / `stats`).

Keep relevance notes tight and factual — no hype, no invented findings. If an
abstract is missing, say so rather than guessing.

## Options & maintenance commands

- **Catch up after missed days:** `fetch --days 5` (or however many). The
  seen-store still prevents duplicates, so widening the window is always safe.
- **Validate journal abbreviations** after editing the list:
  `python scripts/fetch_pubmed.py check --days 120` — any journal showing `0`
  hits (or `<-- CHECK`) has a wrong `ta`; fix it against
  https://www.ncbi.nlm.nih.gov/nlmcatalog/journals .
- **Status:** `python scripts/fetch_pubmed.py stats` — seen count, last run.
- **Add/remove journals or subtopics:** edit `references/journals.json`
  (`domain`: heme|onc|medai|genmed; `scope`: `all` = take everything, `topic` =
  apply the shared `topic_filter` keyword clause). Re-run `check` afterward.
- **NCBI etiquette:** optionally set env `STUDIES_FETCH_EMAIL` to the user's
  email (recommended by NCBI, not required). Requests are already throttled to
  ~3/sec.

## Files

```
studies-fetch/
  SKILL.md                     this file
  references/journals.json     journal registry + topic filter (edit here)
  scripts/fetch_pubmed.py      fetch | check | stats
  data/                        created on first run
    seen_ids.json              persistent dedup store (do not delete unless resetting)
    digest_<date>.json         raw records for that day
    digest_<date>.md           the human digest you generate
```

## Notes & edge cases

- **Resetting dedup** (e.g. to re-pull a period from scratch): delete
  `data/seen_ids.json`. The next fetch treats everything in the window as new.
- **genmed count of 0** on a given day is normal — those journals are
  topic-filtered and don't publish heme/onc/AI content every day.
- **New journals like NEJM AI** are indexed in PubMed but low-volume; a `0` in a
  short window is expected, not an error (confirm with `check`).
- This skill only *fetches and summarizes*; it does not download full texts. For
  PDFs of specific studies, that is a separate workflow.
