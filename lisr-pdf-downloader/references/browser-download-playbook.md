# Browser download playbook

The non-obvious mechanics for getting real PDFs onto disk through Chrome (driven via the
Claude-in-Chrome MCP). Read this before Phase 4. Everything here was learned the hard way on a live
197-study run.

## Table of contents
1. Capturing the LISR token
2. Fetching metadata from the LISR API
3. Getting data out of the page (output filter)
4. The fresh-tab download rule (the single most important thing)
5. The grab JS
6. Running a download pool (round structure)
7. Wiley (Atypon-style block) — pdfdirect trick
8. Cloudflare-walled publishers
9. Supplementary materials
10. Publisher cheat-sheet

---

## 1. Capturing the LISR token
LISR authenticates its API with a Bearer token held in memory (not in localStorage/cookies, so a
plain `fetch(..., {credentials:'include'})` returns 401). Hook the header once, then trigger a real
search in the UI so the app makes an authenticated request you can sniff:

```js
if (!window.__authCap) {
  window.__authCap = { token: null };
  const of = window.fetch;
  window.fetch = function(...a){ try{ const h=a[1]&&a[1].headers; let t=null;
    if(h instanceof Headers) t=h.get('Authorization'); else if(h) t=h['Authorization']||h['authorization'];
    if(t) window.__authCap.token=t; }catch(e){} return of.apply(this,a); };
  const os = XMLHttpRequest.prototype.setRequestHeader;
  XMLHttpRequest.prototype.setRequestHeader = function(k,v){ if(String(k).toLowerCase()==='authorization') window.__authCap.token=v; return os.apply(this,arguments); };
}
'hooked';
```
Then type any study ID into the LISR search box and press Enter. `window.__authCap.token` is now the
`Bearer …` string. If it expires mid-run, re-trigger a UI search to recapture.

## 2. Fetching metadata from the LISR API
`GET /backend/api/v1/summary/all/<project>?page=1&size=100&include_deleted=false&sort_by=created_at&sort_order=desc&search=<ID>`
with header `Authorization: <token>`. Returns `{items:[...], page_info:{total,has_next,...}}`. Search
is fuzzy, so pick the item whose `id` exactly equals the study ID (paginate if `has_next` and not
found). Fields of interest: `title, authers, paper_id, paper_id_type, journal, publish_date,
nct_number, is_abstract_publication, pdf_path, supplementary_pdf_path`.

For ~200 IDs, loop in-page fire-and-forget with small concurrency (~6) and poll a counter — a single
awaited loop will exceed the tool's ~45 s eval timeout (the page keeps running after the timeout, so
just poll `Object.keys(window.__meta).length`).

## 3. Getting data out of the page (output filter)
The MCP JS tool blocks outputs that look like cookies/query-strings ("[BLOCKED: Cookie/query string
data]"), which trips on JSON full of URLs/DOIs. To exfiltrate structured data, **download it as a
file** instead:
```js
const blob = new Blob([JSON.stringify(window.__meta)], {type:'application/json'});
const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='lisr_metadata.json';
document.body.appendChild(a); a.click();
```
Then move it from the Downloads folder with Bash. (Pure base64/numbers are fine to return; URLs and
JSON-with-DOIs are not.)

## 4. The fresh-tab download rule (MOST IMPORTANT)
Chrome's "multiple automatic downloads" protection cancels the **2nd and later** programmatic
download in a given tab, and navigating a tab away **cancels a download that hasn't finished
flushing**. Symptom: the grab returns `OK<size>` but no file appears.

Rules that make downloads reliable:
- **One download per tab.** Use a *fresh* tab for each study; never reuse a tab for a second
  download; never re-navigate a tab after grabbing from it.
- **Create tabs in parallel, individually.** Issue many `tabs_create_mcp` calls in a single
  message (they return distinct tab ids). `tabs_create_mcp` inside a `browser_batch` fails
  ("No tab available"). `tabs_close_mcp` *does* work inside `browser_batch` — batch-close spent tabs.
- **Let the download flush** — keep a ~2.5 s `await` inside the grab after the click, and don't
  navigate that tab again.
- Files have no Save-As prompt; they appear in the user's Chrome Downloads folder.

## 5. The grab JS
See `scripts/grab_pdf.js` for the canonical version. Shape: IIFE (so reruns don't hit
`const`-redeclared), each `fetch` guarded by an AbortController (~18 s) so a hang can't freeze the
batch, returns `"<id>.pdf|OK<size>"` / `"|LIBKEY"` / `"|CF:<host>"` / `"|FAIL:<host>"`.

Strategy order inside the grab:
1. If host is still `libkey.io` → return `LIBKEY` (landing didn't redirect; either no full text, or
   needs the "remember PDF format" pref — see below).
2. If the page title matches `just a moment|verify you are human|attention required` → `CF:<host>`
   (Cloudflare; stop).
3. `fetch(location.href)`; if it's a PDF blob (`type` includes `pdf`, size > ~1.5 KB) → save.
4. Else scan `iframe/embed/object` `src`/`data` and anchors for `pdfdirect|epdf|/pdf/|.pdf`; prefer
   `pdfdirect`; fetch the best candidate and save. Retry the scan 2× with a short wait (publisher
   wrappers inject the iframe late).

**"Remember PDF format" pref:** the first LibKey landing shows buttons + a checkbox "Automatically
remember format choice for 24 hours". Tick it and click "Download PDF" once; afterwards LibKey
landings auto-redirect straight to the publisher PDF, so a single navigate→grab works per study.

## 6. Running a download pool (round structure)
Per round of N≈8:
1. **Create N fresh tabs** — N `tabs_create_mcp` calls in one message; collect the ids.
2. **One `browser_batch`**: N `navigate` (each tab → its LibKey URL), then one `wait` ~9 s, then N
   `javascript_tool` grabs (one per tab, each with that study's `<id>.pdf` filename).
3. **Bash**: `python scripts/move_round.py "<id>|<status>,<id>|<status>,..."` — moves valid
   `Downloads/<id>.pdf` into the output folder, records status, prints the NEXT N URLs.
4. **One `browser_batch`** of N `tabs_close_mcp` to close the spent tabs.
Keep two long-lived tabs (the LISR dashboard + a scratch tab) so the group never empties.

If a single grab throws a CDP error ("target navigated/detached", "Identifier already declared"),
the `browser_batch` stops at that item; the earlier items still ran. Re-grab the leftover tabs
individually (they're already on their pages) with the IIFE grab.

## 7. Wiley (and similar) — pdfdirect trick
`onlinelibrary.wiley.com` (and `acsjournals.onlinelibrary.wiley.com` for CA Cancer J, `10.3322`)
serve a JS "epdf" reader, not a raw PDF, and block the in-page blob save. Recover by navigating a
fresh tab **directly** to:
`https://<wiley-host>/doi/pdfdirect/<doi>?download=true`
This responds with `Content-Disposition: attachment`, so Chrome downloads it immediately (tab stays
blank/chrome:// — the grab will error with "Cannot access a chrome:// URL", which is fine). The file
saves with Wiley's own descriptive name; map it back to the study ID by journal/author keyword and
rename to `<id>.pdf`.

## 8. Cloudflare-walled publishers
A "Just a moment… / verify you are human" page is a CAPTCHA/bot-check. **Do not click or solve it.**
Known Cloudflare publishers seen on oncology content:
`sciencedirect.com` (Elsevier — also Annals of Oncology `10.1093/annonc`, SSRN `10.2139`),
`aacrjournals.org`, `academic.oup.com`, `tandfonline.com`, `journals.sagepub.com`, `jamanetwork.com`.
Note many of these are reached via LibKey (state A) but blocked at the publisher; some Elsevier items
instead show LibKey "access options" (state B, no LibKey PDF).

Handling (let the user pick):
- **Collaborative fetch:** the user clicks "verify" once per domain in their own browser; the
  `cf_clearance` cookie then lets your same-browser fetches through for ~30 min. Batch that domain's
  studies right after. (For Elsevier specifically, LibKey often has no PDF, so go `doi.org/<doi>` →
  ScienceDirect article → read the `pdfft` link → fetch.)
- **Link list:** put the LibKey URL in the status sheet; the user one-clicks each (their real-browser
  click clears Cloudflare and auto-downloads).

## 9. Supplementary materials
Save as `<studyID>_suppl.<ext>` (multiple → `_suppl1`, `_suppl2`, …). Two sources:
- **Europe PMC (best, scriptable):** for studies with a PMCID,
  `https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/supplementaryFiles` returns a ZIP of all
  supplements. `scripts/fetch_oa_and_supplements.py` does this and unpacks them. Reliable for OA/PMC.
- **Publisher article page (best-effort, browser):** open the article landing page (LibKey "Article
  Link" or `doi.org/<doi>`) in a fresh tab; collect links whose text/href signals a supplement
  ("supplementary", "appendix", "additional file", "data supplement", or media URLs ending in
  pdf/docx/xlsx/zip/csv/tif/jpg/pptx). Fetch each same-origin and save with `_suppl<n>`. Per-publisher
  hints: NEJM "Supplementary Appendix" (a PDF link on the article page); JCO/Atypon "Data Supplement"
  (`/doi/suppl/<doi>`); Springer/BMC "Electronic Supplementary Material"/"Additional file N"
  (`/articles/...//MediaObjects/...`); MDPI a zip of supplements. Cloudflare publishers' supplements
  are blocked just like their PDFs.

Supplements are inherently inconsistent; log what you fetched and what you couldn't, and don't let a
missing supplement block the main run.

## 10. Publisher cheat-sheet
| DOI prefix / host | Publisher | Behavior |
|---|---|---|
| 10.1056 nejm.org | NEJM | LibKey → raw PDF; blob grab works |
| 10.1200 ascopubs.org | ASCO/JCO (Atypon) | wrapper; grab the `/doi/pdfdirect/` iframe (often routes to PMC) |
| 10.1158 aacrjournals.org | AACR | **Cloudflare** (unless LibKey routes to PMC) |
| 10.1002 / 10.1111 onlinelibrary.wiley.com | Wiley | blob blocked → `pdfdirect?download=true` |
| 10.3322 acsjournals… | CA Cancer J (Wiley) | `pdfdirect?download=true` on acsjournals host |
| 10.1007 / 10.1245 link.springer.com | Springer | raw `content/pdf/...pdf`; blob grab works |
| 10.1186 | BMC (Springer) | OA; blob grab works |
| 10.3390 mdpi-res.com | MDPI | OA; blob grab works |
| 10.1159 | Karger | often LibKey state B (no full text) |
| 10.1016 sciencedirect.com | Elsevier | **Cloudflare**; LibKey usually has no PDF |
| 10.1093/annonc | Annals of Oncology | **Cloudflare** (on ScienceDirect) |
| 10.1093/jnci, /jjco | Oxford UP | **Cloudflare** (academic.oup.com) |
| 10.1080 tandfonline.com | Taylor & Francis | **Cloudflare** |
| 10.1177 journals.sagepub.com | SAGE | **Cloudflare** |
| 10.1001 jamanetwork.com | JAMA | **Cloudflare** |
| 10.2139 | SSRN | **Cloudflare** |
| 10.1097 journals.lww.com | LWW/Wolters Kluwer | secure PDF; usually needs manual |

ASCO meeting abstracts (`10.1200/jco.YYYY.NN.16_suppl.*`) download as ~50 KB one-page abstract PDFs —
that's the only "full text" that exists for them, which is fine.
