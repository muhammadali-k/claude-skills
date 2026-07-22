#!/usr/bin/env python3
"""
studies-fetch: daily cross-sectional PubMed pull for heme/onc + medical-AI journals.

Stdlib only (urllib, xml.etree, json, datetime). No API key required.

Subcommands
-----------
  fetch   Query all configured journals over a rolling window, drop already-seen
          PMIDs, fetch metadata for the new ones, write a dated digest JSON, and
          record the new PMIDs in the seen-store so they never repeat.
  check   Report per-journal hit counts over a wide window (default 90d) WITHOUT
          touching the seen-store. Use this to validate journal abbreviations
          after editing references/journals.json (a journal that returns 0 here
          almost always has a wrong 'ta').
  stats   Show seen-store size and last-run info.

Typical daily use (driven by the SKILL, but runnable by hand):
  python fetch_pubmed.py fetch --days 2

Design notes
------------
* "No repeats": every PMID ever emitted is stored in data/seen_ids.json with the
  date it was added. Entries older than --prune-days (default 180) are dropped to
  bound file size; a paper that old will never re-enter a 1-3 day window anyway.
* "Cross-sectional for one day": each fetch is a self-contained snapshot. The
  rolling window (default 2 days) plus the seen-filter means delayed indexing is
  caught on a later day without producing duplicates.
* NCBI etiquette: <=3 requests/sec without a key. We sleep between calls and set
  tool/email params. Set env STUDIES_FETCH_EMAIL to your email to be a good
  citizen (recommended by NCBI, not required).
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL = "studies-fetch"
EMAIL = os.environ.get("STUDIES_FETCH_EMAIL", "")

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
JOURNALS_PATH = os.path.join(SKILL_DIR, "references", "journals.json")
DATA_DIR = os.path.join(SKILL_DIR, "data")
SEEN_PATH = os.path.join(DATA_DIR, "seen_ids.json")

REQUEST_PAUSE = 0.34  # seconds between requests (~3/sec)


# ----------------------------- HTTP helpers -----------------------------------

def _common_params():
    p = {"tool": TOOL}
    if EMAIL:
        p["email"] = EMAIL
    return p


def _get(url, retries=3):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": TOOL})
            with urllib.request.urlopen(req, timeout=40) as resp:
                return resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"request failed after {retries} tries: {url}\n  {last}")


def esearch(term, reldate, datetype="edat", retmax=300):
    params = _common_params()
    params.update({
        "db": "pubmed",
        "term": term,
        "reldate": str(reldate),
        "datetype": datetype,
        "retmax": str(retmax),
        "retmode": "json",
    })
    url = f"{EUTILS}/esearch.fcgi?" + urllib.parse.urlencode(params)
    time.sleep(REQUEST_PAUSE)
    data = json.loads(_get(url))
    res = data.get("esearchresult", {})
    return res.get("idlist", []), int(res.get("count", 0))


def efetch_batch(pmids):
    """Fetch full records for up to ~200 PMIDs; return list of parsed dicts."""
    params = _common_params()
    params.update({"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})
    url = f"{EUTILS}/efetch.fcgi?" + urllib.parse.urlencode(params)
    time.sleep(REQUEST_PAUSE)
    raw = _get(url)
    return _parse_articles(raw)


# ----------------------------- XML parsing ------------------------------------

def _text(el):
    return "".join(el.itertext()).strip() if el is not None else ""


def _parse_articles(raw):
    out = {}
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return out
    for art in root.findall(".//PubmedArticle"):
        cit = art.find("./MedlineCitation")
        if cit is None:
            continue
        pmid_el = cit.find("./PMID")
        pmid = _text(pmid_el)
        if not pmid:
            continue
        article = cit.find("./Article")
        title = _text(article.find("./ArticleTitle")) if article is not None else ""

        # Abstract (may be multi-section)
        abstract = ""
        if article is not None:
            parts = []
            for ab in article.findall("./Abstract/AbstractText"):
                label = ab.get("Label")
                txt = _text(ab)
                parts.append(f"{label}: {txt}" if label else txt)
            abstract = " ".join(p for p in parts if p).strip()

        # Authors -> "First A, Second B, et al"
        authors = []
        if article is not None:
            for a in article.findall("./AuthorList/Author"):
                ln = _text(a.find("./LastName"))
                init = _text(a.find("./Initials"))
                if ln:
                    authors.append(f"{ln} {init}".strip())
                else:
                    coll = _text(a.find("./CollectiveName"))
                    if coll:
                        authors.append(coll)
        if len(authors) > 3:
            authors_str = ", ".join(authors[:3]) + ", et al"
        else:
            authors_str = ", ".join(authors)

        # Journal full title
        journal_full = ""
        if article is not None:
            journal_full = _text(article.find("./Journal/Title"))

        # Date: prefer electronic ArticleDate, else PubDate
        pubdate = _parse_date(article)

        # DOI
        doi = ""
        for aid in art.findall("./PubmedData/ArticleIdList/ArticleId"):
            if aid.get("IdType") == "doi":
                doi = _text(aid)
                break

        out[pmid] = {
            "pmid": pmid,
            "doi": doi,
            "title": title,
            "abstract": abstract,
            "authors": authors_str,
            "journal_full": journal_full,
            "pubdate": pubdate,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        }
    return out


def _parse_date(article):
    if article is None:
        return ""
    ad = article.find("./ArticleDate")
    if ad is not None:
        y = _text(ad.find("./Year"))
        m = _text(ad.find("./Month"))
        d = _text(ad.find("./Day"))
        if y:
            return "-".join(x for x in [y, m.zfill(2) if m else "", d.zfill(2) if d else ""] if x)
    pd = article.find("./Journal/JournalIssue/PubDate")
    if pd is not None:
        md = _text(pd.find("./MedlineDate"))
        if md:
            return md
        y = _text(pd.find("./Year"))
        m = _text(pd.find("./Month"))
        d = _text(pd.find("./Day"))
        if y:
            return " ".join(x for x in [y, m, d] if x)
    return ""


# ----------------------------- state (seen store) -----------------------------

def _today():
    return dt.date.today().isoformat()


def load_seen():
    if not os.path.exists(SEEN_PATH):
        return {"seen": {}, "last_run": None, "runs": 0}
    try:
        with open(SEEN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("seen", {})
        data.setdefault("last_run", None)
        data.setdefault("runs", 0)
        return data
    except (json.JSONDecodeError, OSError):
        return {"seen": {}, "last_run": None, "runs": 0}


def save_seen(state):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = SEEN_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=0)
    os.replace(tmp, SEEN_PATH)


def prune_seen(state, prune_days):
    if prune_days <= 0:
        return
    cutoff = (dt.date.today() - dt.timedelta(days=prune_days)).isoformat()
    state["seen"] = {k: v for k, v in state["seen"].items() if v >= cutoff}


# ----------------------------- config -----------------------------------------

def load_config():
    with open(JOURNALS_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return cfg["journals"], cfg["topic_filter"]


def build_term(journal, topic_filter):
    clause = f'"{journal["ta"]}"[ta]'
    if journal.get("scope") == "topic":
        clause = f'({clause}) AND {topic_filter}'
    return clause


# ----------------------------- commands ---------------------------------------

def cmd_fetch(args):
    journals, topic_filter = load_config()
    state = load_seen()
    seen = state["seen"]

    # 1) Collect candidate PMIDs per journal.
    pmid_meta = {}   # pmid -> {"journal","domain"}  (first journal that yields it wins)
    per_journal_counts = {}
    print(f"[studies-fetch] querying {len(journals)} journals, window={args.days}d ...",
          file=sys.stderr)
    for j in journals:
        term = build_term(j, topic_filter)
        try:
            ids, _count = esearch(term, reldate=args.days, retmax=args.max_per_journal)
        except RuntimeError as e:
            print(f"  ! {j['name']}: {e}", file=sys.stderr)
            continue
        new_here = 0
        for pid in ids:
            if pid in seen:
                continue
            if pid not in pmid_meta:
                pmid_meta[pid] = {"journal": j["name"], "domain": j["domain"]}
                new_here += 1
        per_journal_counts[j["name"]] = (len(ids), new_here)

    new_pmids = list(pmid_meta.keys())
    print(f"[studies-fetch] {len(new_pmids)} new PMIDs after dedup", file=sys.stderr)

    # 2) Fetch metadata in batches of 200.
    records = []
    for i in range(0, len(new_pmids), 200):
        batch = new_pmids[i:i + 200]
        parsed = efetch_batch(batch)
        for pid in batch:
            rec = parsed.get(pid)
            if not rec:
                continue
            rec.update(pmid_meta[pid])   # add journal + domain
            records.append(rec)

    # 3) Sort by domain then date desc.
    domain_order = {"heme": 0, "onc": 1, "medai": 2, "genmed": 3}
    records.sort(key=lambda r: (domain_order.get(r["domain"], 9), _sortkey_date(r["pubdate"])),
                 reverse=False)

    # 4) Write digest JSON.
    os.makedirs(DATA_DIR, exist_ok=True)
    date_str = _today()
    out_path = args.out or os.path.join(DATA_DIR, f"digest_{date_str}.json")
    digest = {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "window_days": args.days,
        "total_new": len(records),
        "by_domain": _count_by_domain(records),
        "records": records,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(digest, f, indent=2, ensure_ascii=False)

    # 5) Update state (mark all new PMIDs seen), prune, save.
    for pid in new_pmids:
        seen[pid] = date_str
    prune_seen(state, args.prune_days)
    state["last_run"] = dt.datetime.now().isoformat(timespec="seconds")
    state["runs"] += 1
    save_seen(state)

    # 6) Human summary to stdout.
    bd = digest["by_domain"]
    print(f"NEW STUDIES: {len(records)}  "
          f"(heme={bd.get('heme',0)} onc={bd.get('onc',0)} "
          f"medai={bd.get('medai',0)} genmed={bd.get('genmed',0)})")
    print(f"DIGEST_JSON: {out_path}")
    print(f"SEEN_STORE: {len(seen)} PMIDs tracked")


def _sortkey_date(s):
    # crude but monotone: pull leading YYYY[-MM[-DD]] if present
    return s.replace("-", "").replace(" ", "")[:8].ljust(8, "0") if s else "00000000"


def _count_by_domain(records):
    c = {}
    for r in records:
        c[r["domain"]] = c.get(r["domain"], 0) + 1
    return c


def cmd_check(args):
    journals, topic_filter = load_config()
    print(f"Journal resolution check over {args.days}d window "
          f"(0 hits => likely wrong 'ta'):\n")
    zero = []
    for j in journals:
        term = build_term(j, topic_filter)
        try:
            _ids, count = esearch(term, reldate=args.days, retmax=1)
        except RuntimeError as e:
            print(f"  ERR  {j['name']}: {e}")
            continue
        flag = "  <-- CHECK" if count == 0 else ""
        print(f"  {count:>5}  {j['name']}  [{j['ta']}]{flag}")
        if count == 0:
            zero.append(j["name"])
    if zero:
        print("\nZero-hit journals (verify abbreviation at "
              "https://www.ncbi.nlm.nih.gov/nlmcatalog/journals ):")
        for n in zero:
            print(f"  - {n}")
    else:
        print("\nAll journals resolved.")


def cmd_stats(args):
    state = load_seen()
    print(f"seen PMIDs : {len(state['seen'])}")
    print(f"last run   : {state['last_run']}")
    print(f"total runs : {state['runs']}")
    print(f"store path : {SEEN_PATH}")


# ----------------------------- main -------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="studies-fetch PubMed daily pull")
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fetch", help="pull new studies and write dated digest")
    f.add_argument("--days", type=int, default=2,
                   help="rolling window in days (entrez date). Default 2.")
    f.add_argument("--max-per-journal", type=int, default=300)
    f.add_argument("--prune-days", type=int, default=180,
                   help="drop seen PMIDs older than this. Default 180.")
    f.add_argument("--out", default=None, help="override digest JSON path")
    f.set_defaults(func=cmd_fetch)

    c = sub.add_parser("check", help="validate journal abbreviations")
    c.add_argument("--days", type=int, default=90)
    c.set_defaults(func=cmd_check)

    s = sub.add_parser("stats", help="show seen-store status")
    s.set_defaults(func=cmd_stats)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
