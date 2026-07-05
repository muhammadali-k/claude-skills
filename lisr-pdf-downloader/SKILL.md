---
name: lisr-pdf-downloader
description: >-
  Bulk-download full-text PDFs (and supplementary materials) for a list of LISR study IDs,
  using LibKey + institutional (Mayo, library 964) access driven through Chrome. Use this
  whenever the user has a spreadsheet or list of LISR study/reference IDs (e.g. a
  "pending_studies" / reference list for a systematic review or living evidence project) and
  wants the actual article PDFs pulled down and organized — phrasings like "download the full
  texts for these studies", "get the PDFs for my reference list", "fetch the full text + supplements
  for these LISR IDs", "pull these papers from the screening list", or pointing at the LISR
  dashboard (app.lisr.org) and an Excel of IDs. Triggers even when the user doesn't say "LibKey"
  or "skill" — the signal is a set of LISR numeric IDs plus a desire for downloaded full-text
  files. Also handles resolving Embase/Ovid/PMID identifiers to DOIs, open-access fetching,
  per-publisher quirks (Wiley, Atypon, Cloudflare walls), and producing a download-status sheet.
---

# LISR full-text + supplement downloader

Download full-text PDFs — and their supplementary files — for a list of LISR study IDs, then
produce a status spreadsheet. This codifies a workflow proven on a 197-study breast-cancer
living review (≈85 auto-downloaded; the rest cleanly categorized as Cloudflare-blocked,
conference-abstract-only, or not in the library's holdings).

The hard part of this task is not "find a PDF URL" — it's getting a real PDF onto disk through a
browser that fights automated downloads, across dozens of publishers with different page shapes
and bot-walls. Most of this skill is about doing that reliably. Read
`references/browser-download-playbook.md` before driving the browser — it contains the
non-obvious mechanics that make or break the run.

## What you need before starting

- A list of LISR study IDs (usually an `.xlsx`; the column is often `pending_studies`). Read it
  with the `xlsx` skill or `openpyxl`.
- The user's **Chrome** connected via the Claude-in-Chrome extension, already **logged into LISR**
  (`app.lisr.org`) with their institutional (e.g. Mayo) session active. The **LibKey Nomad**
  extension being installed helps but isn't required.
- The **LISR project number** (in the dashboard URL, e.g. `/overview/45` → `45`) and the
  **LibKey library id** (Mayo Clinic = `964`; confirm from the LibKey landing page which shows
  "Access provided by …"). These default to `45`/`964` in the bundled scripts — change them if the
  user's project differs.
- An output folder (default: a `Downloaded_files/` subfolder beside the ID list) and a working dir
  for the JSON state files the scripts produce.

Confirm the project number, library id, and output location with the user if they aren't obvious.
Files land in the user's Chrome **Downloads** folder first (no Save-As prompt); the scripts move
them into the output folder named by study ID.

## Naming convention

- Main full text → `<studyID>.pdf`
- Supplementary files → `<studyID>_suppl.<ext>` (if several: `<studyID>_suppl1.pdf`,
  `<studyID>_suppl2.xlsx`, …). Keep the original extension (pdf/docx/xlsx/zip/tif/jpg/…).

The `_suppl` token is what links a supplement back to its study, so always include it verbatim.

## The workflow

Work in phases. Local data work (identifier resolution, open-access fetching, bookkeeping) runs in
**Python** (it has internet and is fast/reliable). The institutional/paywalled downloads run
through **Chrome**. Keep a running JSON state so the run is resumable.

### Phase 0 — Setup & token capture
1. Read the ID list → unique, ordered list of study IDs. Note duplicates.
2. Create the output folder and confirm Chrome is on the LISR dashboard for the right project.
3. Capture the LISR API bearer token by hooking `fetch`/`XHR` and triggering one search in the UI,
   then reuse it for the metadata API. Details + exact JS in the playbook ("Capturing the LISR token").

### Phase 1 — Fetch metadata (LISR API)
Call `/backend/api/v1/summary/all/<project>?page=1&size=100&search=<ID>` with the token for each ID
(run it as a fire-and-forget in-page loop; poll progress). For each study capture: `title`,
`authers`, `paper_id`, `paper_id_type`, `journal`, `publish_date`, `nct_number`,
`is_abstract_publication`, `pdf_path`, `supplementary_pdf_path`. Match the exact `id` among results
(LISR search is fuzzy). Export the metadata to a JSON file via a Blob download (the tool's output
filter blocks pasting it back directly — see playbook "Getting data out of the page").

### Phase 2 — Resolve identifiers → DOIs (local Python)
Run `scripts/resolve_identifiers.py`. It classifies each `paper_id_type`:
- **DOI** → use directly.
- **OVID** → the value is a **PMID** (resolve PMID→DOI via NCBI) *unless* it looks like `nct…`
  (then it's a ClinicalTrials.gov registration — no journal article).
- **EMBASE** → an Embase accession with no DOI; resolve by **title** via Crossref, accepting only
  high title-similarity matches (≥0.9 auto; 0.8–0.9 flagged "verify"; below → no match).
Output: `resolved.json` (id → doi/pmid/nct + match score + status). Most "no DOI" cases are
conference abstracts with no full text to fetch.

### Phase 3 — Open-access + supplements pass (local Python, no browser)
Run `scripts/fetch_oa_and_supplements.py`. For every study with a DOI it:
- Looks up Unpaywall for an OA PDF and downloads it directly (browser-like UA) → `<id>.pdf`.
- For PMID/PMCID-linked studies, fetches **Europe PMC supplementary files** →
  `<id>_suppl*.<ext>`.
This reliably clears all genuinely open-access items (PMC, MDPI, BMC, preprints) and many
supplements without touching the browser. Records `oa_results.json`.

### Phase 4 — Institutional pass via LibKey (Chrome) — the core loop
For each remaining study with a DOI, download via `https://libkey.io/libraries/<lib>/<doi>`
(URL-encode the DOI). **This is where the browser mechanics matter — follow the playbook exactly.**
Essentials:
- **One fresh tab per download.** Chrome cancels the 2nd+ automatic download in a tab and cancels a
  download when the tab navigates away. So: open a pool of fresh tabs (many `tabs_create_mcp` calls
  in **one** message — batch-create inside `browser_batch` fails), navigate each tab once to its
  LibKey URL, wait ~8–9 s for the redirect to the publisher PDF, then run the grab JS once per tab.
  Never re-navigate a tab you've grabbed from.
- **Grab JS** (`scripts/grab_pdf.js`): fetch the current page; if it's a PDF blob, trigger an
  `<a download>` save; if it's an HTML wrapper, find the `/doi/pdfdirect/` or pdf-iframe `src` and
  fetch that. Wrap it in an IIFE (avoids `const` redeclaration across reruns) and give each fetch an
  AbortController timeout so one slow request can't freeze the batch.
- After each pool: move `Downloads/<id>.pdf` → output folder and record status with
  `scripts/move_round.py` (it also prints the next batch of URLs). Then batch-close the spent tabs.
- A LibKey landing that shows only "LIBRARY ACCESS OPTIONS" (no "Download PDF") means the library
  has no full text for it → record as unavailable, don't retry.

### Phase 5 — Supplements from publisher pages (Chrome, best-effort)
For studies whose full text you got but whose supplements weren't on Europe PMC, open the **article
landing page** (LibKey "Article Link", or `https://doi.org/<doi>`) in a fresh tab and look for
supplementary-file links (anchors/"supplementary"/"additional file"/"data supplement" sections, or
media URLs ending in pdf/docx/xlsx/zip/tif/jpg). Download each via the same fresh-tab fetch method as
`<id>_suppl<n>.<ext>`. Supplements are publisher-specific and messy — treat this as best-effort and
log what you couldn't get. See playbook "Supplementary materials" for per-publisher hints.

### Phase 6 — Wiley retry
Wiley (`onlinelibrary.wiley.com`, `acsjournals.onlinelibrary.wiley.com` for 10.3322) blocks the
in-page blob grab. Recover these by navigating **directly** to
`https://<wiley-host>/doi/pdfdirect/<doi>?download=true`, which Content-Disposition-downloads the
file with the journal's own filename; then map it back to the study ID by title/journal keyword.

### Phase 7 — Cloudflare-walled publishers
Some publishers sit behind a Cloudflare "verify you are human" interstitial you must **not** click
(it's a CAPTCHA/bot-check — prohibited). Known offenders: ScienceDirect/Elsevier (incl. Annals of
Oncology `10.1093/annonc` and SSRN `10.2139`), aacrjournals.org, academic.oup.com, tandfonline.com,
journals.sagepub.com, jamanetwork.com. For these, offer the user two paths and let them choose:
(a) **collaborative fetch** — the user solves the check once per publisher domain, then you fetch
that domain's PDFs while the clearance cookie is valid; or (b) a **clickable LibKey link list** in
the status sheet so they one-click each in their own browser (their click passes Cloudflare and
auto-downloads). Don't attempt to bypass the check yourself.

### Phase 8 — Status sheet
Run `scripts/build_status.py` to produce `Download_status.xlsx`: every study with its status, title,
journal, DOI, match score, whether a `_suppl` file is present, and a **clickable action link**
(LibKey for articles, ClinicalTrials.gov for registrations) for anything not downloaded. Categories:
Downloaded · Cloudflare-blocked (recoverable) · no-DOI/abstract · no institutional full text · trial
registration · publisher-specific issue.

## Operating principles
- **Resumable:** the JSON state files mean you can stop and continue (e.g. across days, or after a
  Cloudflare solve). Re-deriving the worklist = "studies with a DOI and no file yet."
- **Verify every file:** only count a download if it starts with `%PDF-` and is more than a few KB
  (an HTML error page saved as `.pdf` is the classic failure). The scripts check this.
- **Honest categorization:** if no full text exists (conference abstract, not in holdings), say so
  in the sheet rather than implying it was downloadable. Confirm with the user how to treat
  abstract-only records (usually: skip + mark unavailable).
- **Ask before scale when access is uncertain:** validate the end-to-end path on the first one or two
  studies (does institutional access actually return a PDF?) before launching the full pool.

## Scope & safety
- Only for downloading content the user is entitled to via their own logged-in institutional access,
  for legitimate research (systematic review / evidence synthesis). Do not bypass paywalls,
  CAPTCHAs, or bot-detection. Don't send the user's PDFs to third-party services.
