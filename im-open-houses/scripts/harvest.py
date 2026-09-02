#!/usr/bin/env python3
"""harvest.py — headless, deterministic pull of the sources that were live-tested to work
without a browser or login (see references/sources.md). Stdlib only.

    python3 harvest.py [--run-date YYYY-MM-DD] [--no-reddit] [--no-search] [--quick]

Writes  data/harvest_<RUN_DATE>.json:
  auto_candidates  — rows already in candidate-schema form (Project IMG doc, Eventbrite,
                     JSON-LD event pages, WordPress feeds). Review, then merge into
                     data/candidates_<RUN_DATE>.json.
  leads            — URLs worth opening with WebFetch (search hits, watchlist pages whose
                     open-house text changed, tweets). Each has a snippet + why.
  watch_changes    — watchlist pages whose open-house passage changed since last run.
  errors           — per-source failures (never fatal).
Also updates data/watch_state.json (hashes) so "changed" means changed.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
DATA = os.path.join(SKILL, "data")
REFS = os.path.join(SKILL, "references")
WATCHLIST = os.path.join(REFS, "watchlist.json")
WATCH_STATE = os.path.join(DATA, "watch_state.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
REDDIT_UA = "im-open-houses-monitor/1.0 (personal residency-applicant tool)"
HOME_TZ = ZoneInfo("America/Phoenix")

PROJECT_IMG_DOC = "https://docs.google.com/document/d/1DbH8EUbE5jxOrJ5WltN92T6zBu2GTyHPfcYfxsQC1d8/mobilebasic"
EVENTBRITE_SEARCH = "https://www.eventbrite.com/d/online/residency-open-house/?start_date={start}&end_date={end}"
RVOH_ORG = "https://residency-virtual-open-house.org/index.php?specialty=Internal+Medicine&when=upcoming&sort=date"

KEYWORDS = re.compile(r"open house|information session|info session|meet and greet|meet-and-greet|meet & greet|"
                      r"virtual session|q&a session|webinar|first look|recruitment event|meet the program", re.I)
IM_RE = re.compile(r"internal medicine|\bIM\b|med[- ]peds|medicine[- ]pediatrics", re.I)
NOT_IM = re.compile(r"anesthesi|neurolog(y|ical)|psychiatr|pediatric(?!s? ?/? ?internal)|family medicine|surgery|"
                    r"emergency medicine|radiolog|dermatolog|ob/?gyn|obstetric|patholog|ophthalm|orthop|urolog|"
                    r"otolaryng|physical medicine|pm&r|fellowship", re.I)
DATE_RE = re.compile(
    r"(?:(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\.?,?\s+)?"
    r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})(?:st|nd|rd|th)?"
    r"(?:,?\s+(20\d\d))?", re.I)
TIME_RE = re.compile(r"\b(\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)?)(?:\s*(?:-|–|—|to)\s*(\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)))?"
                     r"(?<=[mM.])\s*(ET|EST|EDT|CT|CST|CDT|MT|MST|MDT|PT|PST|PDT|Eastern|Central|Mountain|Pacific)?\b", re.I)
MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
WEEKDAYS = {w: i for i, w in enumerate(["mon", "tue", "wed", "thu", "fri", "sat", "sun"])}
STATE_ABBR = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA", "colorado": "CO",
    "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS", "kentucky": "KY", "louisiana": "LA",
    "maine": "ME", "maryland": "MD", "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD", "tennessee": "TN", "texas": "TX",
    "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC", "puerto rico": "PR",
}

errors: list[dict] = []


# ----------------------------------------------------------------------------- http
def get(url, ua=UA, timeout=25, accept=None):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": accept or "*/*",
                                               "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")


def safe_get(url, **kw):
    try:
        return get(url, **kw)
    except urllib.error.HTTPError as e:
        errors.append({"url": url, "error": f"HTTP {e.code}"})
    except Exception as e:  # noqa: BLE001
        errors.append({"url": url, "error": repr(e)[:200]})
    return None, None, None


def strip_tags(s: str) -> str:
    s = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", s, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>|</p>|</div>|</li>|</tr>|</h\d>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\xa0]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s).strip()


def unwrap_google(url: str) -> str:
    if "google.com/url?" in url:
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("q")
        if q:
            return q[0]
    return url


def platform_of(url: str | None) -> str:
    if not url:
        return "unknown"
    u = url.lower()
    if "zoom.us" in u:
        return "zoom"
    if "forms.office.com" in u or "forms.cloud.microsoft" in u or "forms.microsoft.com" in u:
        return "microsoft_form"
    if "events.teams.microsoft.com" in u or "teams.microsoft.com" in u:
        return "teams"
    if "docs.google.com/forms" in u or "forms.gle" in u:
        return "google_form"
    if "eventbrite" in u:
        return "eventbrite"
    if "qualtrics" in u:
        return "qualtrics"
    if "redcap" in u:
        return "redcap"
    if "surveymonkey" in u:
        return "surveymonkey"
    if "jotform" in u:
        return "jotform"
    if "calendly" in u:
        return "calendly"
    if "webex" in u:
        return "webex"
    if u.startswith("mailto:"):
        return "email"
    return "website"


# ----------------------------------------------------------------------------- dates
def infer_year(month: int, day: int, weekday: str | None, today: dt.date) -> int | None:
    """Pick the year (this or next) that makes the weekday match; else the nearest future-ish year."""
    cands = [today.year, today.year + 1]
    if weekday:
        w = WEEKDAYS.get(weekday[:3].lower())
        for y in cands:
            try:
                if dt.date(y, month, day).weekday() == w:
                    return y
            except ValueError:
                pass
        return None  # weekday contradicts both years → stale/ambiguous
    y = today.year
    try:
        d = dt.date(y, month, day)
    except ValueError:
        return None
    return y if d >= today - dt.timedelta(days=45) else y + 1


def parse_date_text(s: str, today: dt.date):
    """Return (iso_date, time_str, end_time_str, tz) from free text like 'Wed, Sep 2, 2026 • 6:00 PM CT'."""
    m = DATE_RE.search(s or "")
    if not m:
        return None, None, None, None
    wd, mon, day, year = m.groups()
    month = MONTHS[mon[:3].lower()]
    y = int(year) if year else infer_year(month, int(day), wd, today)
    if not y:
        return None, None, None, None
    try:
        iso = dt.date(y, month, int(day)).isoformat()
    except ValueError:
        return None, None, None, None
    t = TIME_RE.search(s)
    time_s = end_s = tz = None
    if t:
        time_s, end_s, tz = t.group(1), t.group(2), t.group(3)
        if time_s and not re.search(r"[ap]", time_s, re.I) and end_s and re.search(r"[ap]", end_s, re.I):
            time_s = time_s.strip() + " " + re.search(r"[ap]\.?m\.?", end_s, re.I).group(0)
    return iso, time_s, end_s, tz


# ----------------------------------------------------------------------------- sources
def src_project_img(today):
    """Community 'Open Houses List – Match 2027' Google Doc (public, server-rendered via /mobilebasic)."""
    out, leads = [], []
    st, _, body = safe_get(PROJECT_IMG_DOC)
    if not body:
        return out, leads
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", body, flags=re.S | re.I)
    for tr in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S | re.I)
        if len(cells) < 5:
            continue
        link = re.search(r'href="([^"]+)"', tr)
        url = unwrap_google(html.unescape(link.group(1))) if link else None
        txt = [strip_tags(c) for c in cells]
        n, program, state, spec = txt[0], txt[1], txt[2], txt[3]
        date_txt = txt[4] if len(txt) > 4 else ""
        if not IM_RE.search(spec) and not IM_RE.search(program):
            continue
        iso, time_s, end_s, tz = parse_date_text(date_txt, today)
        if iso and dt.date.fromisoformat(iso) < today:
            continue
        rec = {
            "program": program, "state": STATE_ABBR.get(state.lower().strip(), state.strip()[:2].upper() or None),
            "title": f"Virtual Open House ({spec.strip() or 'Internal Medicine'})",
            "event_type": "virtual open house", "date": iso, "date_tbd": iso is None,
            "time": time_s, "end_time": end_s, "timezone": tz,
            "registration_url": url, "platform": platform_of(url),
            "source_url": PROJECT_IMG_DOC, "source_kind": "aggregator",
            "notes": f"Project IMG list row {n}; date as listed: '{date_txt}'",
        }
        out.append(rec)
    return out, leads


def src_eventbrite(today):
    out = []
    url = EVENTBRITE_SEARCH.format(start=today.isoformat(), end=(today + dt.timedelta(days=150)).isoformat())
    st, _, body = safe_get(url)
    if not body:
        return out
    m = re.search(r"window\.__SERVER_DATA__\s*=\s*", body)
    if not m:
        errors.append({"url": url, "error": "no __SERVER_DATA__"}); return out
    try:
        data, _ = json.JSONDecoder().raw_decode(body[m.end():])
    except Exception as e:  # noqa: BLE001
        errors.append({"url": url, "error": f"server data parse: {e}"}); return out
    results = (((data.get("search_data") or {}).get("events") or {}).get("results")) or []
    for ev in results:
        name = ev.get("name") or ""
        if not IM_RE.search(name) or NOT_IM.search(name):
            continue
        start_date, start_time = ev.get("start_date"), ev.get("start_time")
        tzname = ev.get("timezone")
        if start_date and start_date < today.isoformat():
            continue
        out.append({
            "program": re.sub(r"\s*[-–—|].*$", "", name).strip() or name,
            "title": name, "event_type": "virtual open house", "date": start_date,
            "time": start_time, "timezone": tzname, "registration_url": ev.get("url"),
            "platform": "eventbrite", "source_url": ev.get("url") or url, "source_kind": "eventbrite",
            "notes": "Eventbrite online search hit; open the event page to confirm program + state",
        })
    return out


def src_rvoh_org(today):
    leads = []
    st, _, body = safe_get(RVOH_ORG)
    if body:
        txt = strip_tags(body)
        hits = [ln for ln in txt.splitlines() if IM_RE.search(ln) and KEYWORDS.search(ln)]
        if hits:
            leads.append({"url": RVOH_ORG, "source": "residency-virtual-open-house.org",
                          "why": f"{len(hits)} IM lines (site was empty for IM on 2026-09-01)", "snippet": " | ".join(hits[:5])[:400]})
    return leads


def decode_bing(u: str) -> str:
    m = re.search(r"[?&]u=a1([A-Za-z0-9_-]+)", u)
    if not m:
        return u
    s = m.group(1) + "=" * (-len(m.group(1)) % 4)
    try:
        return base64.urlsafe_b64decode(s).decode("utf-8", "replace")
    except Exception:  # noqa: BLE001
        return u


JUNK_HOSTS = ("merriam-webster", "dictionary.cambridge", "wikipedia.org", "wiktionary")


def src_bing(queries, today, seen_urls, sleep_s=8):
    leads = []
    for q in queries:
        url = "https://www.bing.com/search?format=rss&count=20&q=" + urllib.parse.quote(q)
        st, _, body = safe_get(url)
        if not body:
            continue
        items = re.findall(r"<item>(.*?)</item>", body, flags=re.S)
        first_host = None
        for it in items:
            link = re.search(r"<link>(.*?)</link>", it, flags=re.S)
            title = re.search(r"<title>(.*?)</title>", it, flags=re.S)
            pub = re.search(r"<pubDate>(.*?)</pubDate>", it, flags=re.S)
            desc = re.search(r"<description>(.*?)</description>", it, flags=re.S)
            if not link:
                continue
            u = decode_bing(html.unescape(link.group(1).strip()))
            host = urllib.parse.urlparse(u).netloc
            first_host = first_host or host
            if any(j in host for j in JUNK_HOSTS):
                continue
            t = html.unescape(strip_tags(title.group(1))) if title else ""
            d = html.unescape(strip_tags(desc.group(1))) if desc else ""
            if not (IM_RE.search(t + " " + d) and KEYWORDS.search(t + " " + d)):
                continue
            if NOT_IM.search(t) and not IM_RE.search(t):
                continue
            if u in seen_urls:
                continue
            seen_urls.add(u)
            leads.append({"url": u, "source": "bing", "query": q, "title": t[:160], "pubdate": pub.group(1) if pub else None,
                          "snippet": d[:300], "why": "search hit mentioning IM + open house/info session"})
        if first_host and any(j in first_host for j in JUNK_HOSTS):
            errors.append({"url": url, "error": "bing degraded (dictionary junk) — backing off"})
            break
        time.sleep(sleep_s)
    return leads


def src_reddit(today, seen_urls):
    leads = []
    feeds = [
        "https://www.reddit.com/r/IMGreddit/search.rss?q=%22open+house%22&restrict_sr=1&sort=new",
        "https://www.reddit.com/r/medicalschool/search.rss?q=%22open+house%22+%22internal+medicine%22&restrict_sr=1&sort=new",
    ]
    for i, url in enumerate(feeds):
        if i:
            time.sleep(61)  # reddit: ~1 unauthenticated request per minute
        st, _, body = safe_get(url, ua=REDDIT_UA)
        if not body:
            continue
        for entry in re.findall(r"<entry>(.*?)</entry>", body, flags=re.S):
            link = re.search(r'<link href="([^"]+)"', entry)
            title = re.search(r"<title>(.*?)</title>", entry, flags=re.S)
            upd = re.search(r"<updated>(.*?)</updated>", entry)
            if not link:
                continue
            u = html.unescape(link.group(1))
            when = upd.group(1)[:10] if upd else None
            if when and dt.date.fromisoformat(when) < today - dt.timedelta(days=45):
                continue
            if u in seen_urls:
                continue
            seen_urls.add(u)
            leads.append({"url": u, "source": "reddit", "title": html.unescape(title.group(1)) if title else "",
                          "pubdate": when, "why": "recent reddit thread about open houses (may link to lists/sheets)"})
    return leads


def src_tweets(leads):
    """For x.com status URLs among leads, fetch text via fxtwitter (the only working headless path)."""
    for ld in leads:
        m = re.search(r"(?:x|twitter)\.com/([A-Za-z0-9_]+)/status/(\d+)", ld["url"])
        if not m:
            continue
        api = f"https://api.fxtwitter.com/{m.group(1)}/status/{m.group(2)}"
        st, _, body = safe_get(api)
        if body:
            try:
                tw = json.loads(body).get("tweet") or {}
                ld["snippet"] = (tw.get("text") or "")[:500]
                ld["pubdate"] = tw.get("created_at")
                ld["why"] = "tweet text via fxtwitter"
            except Exception as e:  # noqa: BLE001
                errors.append({"url": api, "error": f"fxtwitter parse {e}"})
    return leads


def jsonld_events(body: str, page_url: str, today):
    out = []
    for blk in re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', body, flags=re.S | re.I):
        try:
            data = json.loads(html.unescape(blk.strip()))
        except Exception:  # noqa: BLE001
            continue
        objs = data if isinstance(data, list) else [data]
        for o in objs:
            if not isinstance(o, dict):
                continue
            typ = o.get("@type")
            if typ != "Event" and not (isinstance(typ, list) and "Event" in typ):
                continue
            name = o.get("name") or ""
            start = o.get("startDate") or ""
            if not start or start[:10] < today.isoformat():
                continue
            loc = o.get("location") or {}
            if isinstance(loc, list):
                loc = loc[0] if loc else {}
            out.append({"program": re.sub(r"\s*(virtual|open house|residency).*$", "", name, flags=re.I).strip() or name,
                        "title": name, "date": start[:10], "time": start[11:16] if len(start) > 15 else None,
                        "timezone": start[19:] or None, "registration_url": (o.get("url") if platform_of(o.get("url")) != "website" else None),
                        "platform": platform_of(o.get("url")), "source_url": page_url, "source_kind": "program_site",
                        "notes": f"schema.org Event JSON-LD; location type {loc.get('@type')}"})
    return out


def src_watchlist(today, quick=False):
    """Re-fetch known program pages; report the open-house passage when it changed."""
    wl = json.load(open(WATCHLIST)) if os.path.exists(WATCHLIST) else []
    state = json.load(open(WATCH_STATE)) if os.path.exists(WATCH_STATE) else {}
    changes, auto = [], []
    for w in wl:
        if quick and w.get("priority", 1) > 1:
            continue
        url = w["url"]
        st, final, body = safe_get(url)
        if not body:
            continue
        auto.extend(jsonld_events(body, url, today))
        txt = strip_tags(body)
        # passage(s): lines with a keyword, plus one line of context either side
        lines = txt.splitlines()
        keep = set()
        for i, ln in enumerate(lines):
            if KEYWORDS.search(ln):
                keep.update((i - 1, i, i + 1))
        passage = "\n".join(lines[i] for i in sorted(k for k in keep if 0 <= k < len(lines)))[:3000]
        dates = sorted({parse_date_text(ln, today)[0] for ln in passage.splitlines() if parse_date_text(ln, today)[0]} - {None})
        h = hashlib.sha1(passage.encode()).hexdigest()
        prev = state.get(url, {})
        entry = {"hash": h, "checked": today.isoformat(), "dates": dates}
        if prev.get("hash") != h:
            changes.append({"url": url, "program": w.get("program"), "state": w.get("state"), "first_check": not prev,
                            "dates_found": dates, "passage": passage[:1500],
                            "why": "watchlist page open-house passage changed" if prev else "first check of watchlist page"})
        state[url] = entry
        time.sleep(1.0)
    os.makedirs(DATA, exist_ok=True)
    json.dump(state, open(WATCH_STATE, "w"), indent=1)
    return changes, auto


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-date", default=dt.datetime.now(HOME_TZ).date().isoformat())
    ap.add_argument("--no-reddit", action="store_true")
    ap.add_argument("--no-search", action="store_true")
    ap.add_argument("--quick", action="store_true", help="skip low-priority watchlist pages")
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.run_date)
    y = today.year
    months = [(today + dt.timedelta(days=30 * k)).strftime("%B") for k in range(0, 3)]

    auto, leads = [], []
    seen = set()
    print("[1/6] Project IMG doc …", file=sys.stderr)
    c, l = src_project_img(today); auto += c; leads += l
    print(f"      {len(c)} IM rows dated today or later", file=sys.stderr)
    print("[2/6] Eventbrite …", file=sys.stderr)
    c = src_eventbrite(today); auto += c
    print(f"      {len(c)} IM events", file=sys.stderr)
    print("[3/6] residency-virtual-open-house.org …", file=sys.stderr)
    leads += src_rvoh_org(today)
    if not a.no_search:
        print("[4/6] Bing RSS …", file=sys.stderr)
        queries = [
            f'"internal medicine" residency "virtual open house" {y}',
            f'"internal medicine residency" "open house" register zoom',
            f'"internal medicine" residency "information session" applicants {y}',
            f'"internal medicine" residency "virtual open house" {months[0]} {y}',
            f'"internal medicine" residency "virtual open house" {months[1]} {y}',
            f'"open house" "internal medicine residency" forms.office.com OR forms.gle OR "zoom.us/webinar/register"',
        ]
        leads += src_bing(queries, today, seen)
    if not a.no_reddit:
        print("[5/6] Reddit RSS (≈1 min, rate-limited) …", file=sys.stderr)
        leads += src_reddit(today, seen)
    print("[6/6] watchlist pages …", file=sys.stderr)
    changes, c = src_watchlist(today, quick=a.quick); auto += c
    leads = src_tweets(leads)

    out = {"run_date": a.run_date, "auto_candidates": auto, "leads": leads, "watch_changes": changes, "errors": errors}
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, f"harvest_{a.run_date}.json")
    json.dump(out, open(path, "w"), indent=1, ensure_ascii=False)
    print(f"HARVEST auto_candidates={len(auto)} leads={len(leads)} watch_changes={len(changes)} errors={len(errors)}")
    print(f"HARVEST_PATH={path}")


if __name__ == "__main__":
    main()
