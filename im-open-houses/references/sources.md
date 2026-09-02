# Sources — where IM virtual open houses are announced, and what a headless agent can read

Live-tested 2026-09-01 from a headless host (curl/python, no login) and from Chrome. Every
verdict below was observed, not assumed. Re-test anything marked *fragile* if it starts
returning nothing; update this file when a source changes.

## 0. The picture
- Programs announce on their **own "Apply / Contact" page** (12 of 15 verified events were
  inline text there — WordPress/Drupal/Squarespace, no structured data), and on **X /
  Instagram** (community programs especially). The year is usually **omitted**; weekday +
  date must agree with the current year (`harvest.py` does this check).
- Registration is mostly **Microsoft Forms**, **Zoom webinar registration**, or a **direct
  Zoom/Teams join link**; Google Forms second; Qualtrics/Eventbrite/Jotform occasional.
  Registration pages are JS shells — **take the date from the announcing page**, never from
  the form.
- Timing clusters: **Aug 5 – Sep 14** (pre-ERAS-submission), second wave **Nov–Dec**
  (interview-season "second looks"), a few in Feb (post-rank-list, not useful).

## 1. Headless sources that work (what `scripts/harvest.py` polls)

| # | Source | Verdict | How |
|---|---|---|---|
| 1 | **Project IMG "Open Houses List – Match 2027"** (public Google Doc, community-maintained; distributed by @ProjectImg on X and a WhatsApp group) | **Works** via `/mobilebasic` (server-rendered table). `/export` and `/pub` → 401. | `https://docs.google.com/document/d/1DbH8EUbE5jxOrJ5WltN92T6zBu2GTyHPfcYfxsQC1d8/mobilebasic` — columns S.no / Program / State / Specialty / Date / Register link (Google `url?q=` wrapper). 263 rows on 2026-09-01, **only ~15 IM** (anesthesiology-dominated). Dates are free text ("Wed, Sep 2", "Wed, Aug 5, 2026 • 12:30 PM ET"). No Last-Modified header — diff by content. If the doc id changes, look for the new link in @ProjectImg tweets (via fxtwitter) or the r/IMGreddit thread. |
| 2 | **Eventbrite** online search + event JSON-LD | **Works**. Search page embeds `window.__SERVER_DATA__` (`search_data.events.results[]` with `start_date`, `start_time`, `timezone`, `url`); event pages carry schema.org `Event`. | `https://www.eventbrite.com/d/online/residency-open-house/?start_date=…&end_date=…`. Low yield (≈1 IM event/season) but free. |
| 3 | **Bing web search, RSS output** | **Works**, but `freshness`/`filters` params are **ignored**; do freshness client-side with `<pubDate>` (last-crawl date). Degrades to dictionary junk after ~6 rapid queries — `harvest.py` backs off when the first host is junk. `site:` operators are unreliable in RSS mode. | `https://www.bing.com/search?format=rss&count=20&q=<query>`; result links may be `bing.com/ck/a?…&u=a1<base64url>` — decode after `a1`. |
| 4 | **Reddit RSS** (r/IMGreddit, r/medicalschool) | **Works, ~1 request/minute per IP** (429 on the 2nd call within a minute); `.json` endpoints 403. Threads point to the Project IMG list and to program tweets. | `https://www.reddit.com/r/IMGreddit/search.rss?q=%22open+house%22&restrict_sr=1&sort=new` with a descriptive UA. `harvest.py` spaces calls 61 s apart (`--no-reddit` to skip). |
| 5 | **Program-page watchlist** (`references/watchlist.json`) | **Works**. Re-fetch, isolate the lines around *open house / information session / meet and greet / webinar*, hash them, report changes + any dates found. WordPress sites also expose `/feed/` and `/wp-json/wp/v2/posts?search=open%20house`; a few pages carry `Event` JSON-LD (Keck USC, Eventbrite). | Add every program page where an event was ever found — the same page is re-used next season. Priority 1 = check daily; 2 = daily unless `--quick`. |
| 6 | **X/Twitter by tweet id** (`api.fxtwitter.com/<handle>/status/<id>`, or `cdn.syndication.twimg.com/tweet-result?id=<id>&token=a`) | **Works for a known tweet id only.** Timelines, search, nitter mirrors, xcancel, rsshub, r.jina.ai, x.com HTML: all dead/blocked. | Tweet ids come from search hits (`x.com/<handle>/status/<id>`); `harvest.py` resolves them automatically. Program accounts that post open houses: @BaystateIM, @CAMCInternalIAM, @CapitalIMRes, @UMassIMResident, @svhmedres, @SalemIMres, @ProjectImg, @Inside_TheMatch. |
| 7 | **DuckDuckGo HTML** (`html.duckduckgo.com/html/?q=…&df=w`) | Works for ~8 requests then **IP-blocked >15 min** (HTTP 202 "anomaly"). The only engine whose date filter really works. | Not in `harvest.py` by default (too easy to get banned); use WebSearch instead. |
| 8 | Localist campus calendars (`events.<school>.edu/api/2/events?search=residency+open+house&days=200`) | Works as JSON but poor yield (stale 2024 entries). | Weekly at most. |
| 9 | YouTube search (`ytInitialData`, `sp=EgIIBA%3D%3D` = this month) | Works; only for programs streaming on YouTube Live (Carilion). | Low priority. |
| 10 | Google News RSS / Bing News RSS | Work, honor `when:7d`, index press only (0 relevant). | One call at most. |
| 11 | `residency-virtual-open-house.org` (server-rendered PHP; `index.php?specialty=Internal+Medicine&when=upcoming&sort=date`; event pages expose `.ics`) | Fetchable but **0 IM events** (anesthesiology mirror). | `harvest.py` pings it; alerts if IM lines appear. |

## 2. Sources that only work in a real browser (local `scan --local` / `signup`)

| Source | Status | Use |
|---|---|---|
| **OpenHouse — `residency-open-house.vercel.app`** (community-sourced, 908 open houses, +105/7 days, hourly updates, 32 specialties incl. IM, links "verified") | Listings and `/api/openhouses` are behind **Google/Discord sign-in**; `robots.txt` disallows `/api/`. **The user signs in himself in Chrome**; the skill only *reads* the listings through that logged-in tab. Never sign in, accept terms, or scrape the API on his behalf. | Local runs: open the site in a new tab; if the listings render (he is signed in), filter Specialty = Internal Medicine, read upcoming rows (program, date/time, link), add them to the candidates file with `source_kind: "aggregator"` and `source_url` = the site. If it shows the sign-in landing page, skip and say so in the run note. |
| X/Twitter search (`x.com/search?q=…&f=live`), Instagram (#IMresidency, program accounts), Threads, Facebook groups, LinkedIn | Login walls / JS shells headlessly; readable in Chrome when the user is logged in. | Optional in local runs: search `"open house" "internal medicine" residency` (latest) and read the top posts. |
| Google web search with `tbs=qdr:d` (past 24 h) | JS wall headlessly; works in Chrome. | Local runs: the fastest freshness filter available. |

## 3. Dead or not worth polling (verified)
- "Residency Open Houses" Google Sheet `1XNE5aZj27…` — private (401 everywhere).
- insidethematch.com open-house calendars — Match 2023 content; @Inside_TheMatch reposts only.
- Instagram mirrors (imginn/picuki/dumpor) — captions without dates, 403/410, break often.
- Bluesky public API — 403 from cloud hosts. Google cache — gone. Startpage/Brave/Mojeek/Ecosia — block first request. Yahoo date filters — HTTP 500.
- AAIM/APDIM/ACP — no IM equivalent of the ASA anesthesiology open-house list.
- Scorpion-CMS event pages (`…/event-details/?event=NNNN`, e.g. Mary Washington, Mobile Infirmary) — date block never renders, even in Chrome; use the coordinator email.
- AMA "virtual open houses — what you should know" article — evergreen explainer, re-dated every year; not an event.

## 4. WebSearch query bank (run all of them every day — `openhouse.py queries` prints the current-dated set)
Core phrasings × current month names, plus platform-restricted forms
(`forms.office.com OR forms.gle OR "zoom.us/webinar/register"`), `site:x.com`,
`site:instagram.com`, `site:reddit.com`, HCA domains, and `"Open Houses List" "Match 2027"`
(catches re-shares of the Project IMG doc or a successor). Search engines recycle the same
~10 pages regardless of wording; **new programs surface mostly from domain-restricted
queries, the Project IMG doc, and Reddit threads** — so read those leads carefully rather
than running more generic queries.

## 5. Freshness and stale-page rules
- A hit is *new* only if its URL was never seen **or** its extracted date set changed.
- Drop any page whose only dates are ≤ last season; when a page shows a weekday + date, the
  weekday must match the current year (the Weill Cornell Localist page still shows a live
  2024 Zoom link — classic trap).
- Event pages die fast (Zoom registrations 404 after the event; forms.gle links expire).
  Store the date from the announcing page and the first registration link seen.
- Reddit: max 3–4 requests per run, ≥ 60 s apart. Bing: ≤ 6 queries, 8 s apart. DDG: avoid.

## 6. Seeds observed on 2026-09-01 (for calibration; the state file is authoritative)
UNMC (Sep 2, 6–7 pm CT, MS Forms) · Creighton Phoenix (Sep 2, 6–7 pm MT, Qualtrics) ·
Providence St. Vincent OR (Sep 2, 6:30 pm PT, per Project IMG) · Baystate MA (Aug 27 / Sep 3,
6–7:30 pm ET, QR-code RSVP on X) · Augusta Health VA (Sep 8, 7 pm ET, direct Zoom) ·
UM/Jackson Memorial FL (Sep 8 IMG-specific session, registration TBD) · MaineHealth ME (Sep 9,
6 pm ET, MS Forms) · Hillsboro Medical Center OR (Sep 9, 5 pm PT, Eventbrite) · UConn (Sep 14,
6:30–7:30 pm ET, direct Teams) · Beebe DE (Oct 2, 5 pm, MS Forms) · GW DC (TBD) · UM Capital
Region MD (TBD) · Mobile Infirmary AL (date not rendered; email coordinator) · Yale (Nov 2/16/
23/30, Dec 7 recruitment webinars, interview-linked).
