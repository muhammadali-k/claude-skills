#!/usr/bin/env python3
"""im-open-houses — state, de-duplication, program matching, and digest rendering
for Internal Medicine residency virtual open houses.

Stdlib only (Python 3.9+). Every command is idempotent.

    python3 openhouse.py ingest  CANDIDATES.json [--run-date YYYY-MM-DD]
    python3 openhouse.py digest  [--run-date YYYY-MM-DD] [--out PATH]
    python3 openhouse.py calendar-json [--run-date ...]      # events to add to Google Calendar
    python3 openhouse.py mark    EVENT_ID registered|declined|attended [--note TEXT]
    python3 openhouse.py match   "program name"               # fuzzy lookup in my_programs.json
    python3 openhouse.py queries [--run-date ...]             # the daily search-query bank
    python3 openhouse.py status
    python3 openhouse.py validate CANDIDATES.json             # schema check, no writes

State lives in ../data/events.json (committed to git). See SKILL.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
DATA = os.path.join(SKILL, "data")
REFS = os.path.join(SKILL, "references")
EVENTS = os.path.join(DATA, "events.json")
PROGRAMS = os.path.join(REFS, "my_programs.json")
RUNS = os.path.join(DATA, "runs")
HOME_TZ = ZoneInfo("America/Phoenix")

TZ_ALIASES = {
    "ET": "America/New_York", "EST": "America/New_York", "EDT": "America/New_York",
    "EASTERN": "America/New_York",
    "CT": "America/Chicago", "CST": "America/Chicago", "CDT": "America/Chicago",
    "CENTRAL": "America/Chicago",
    "MT": "America/Denver", "MST": "America/Phoenix", "MDT": "America/Denver",
    "MOUNTAIN": "America/Denver", "AZ": "America/Phoenix", "ARIZONA": "America/Phoenix",
    "PT": "America/Los_Angeles", "PST": "America/Los_Angeles", "PDT": "America/Los_Angeles",
    "PACIFIC": "America/Los_Angeles",
    "HST": "Pacific/Honolulu", "AKST": "America/Anchorage", "AKDT": "America/Anchorage",
    "UTC": "UTC", "GMT": "UTC",
}
STATE_TZ = {  # default event timezone when only the state is known
    "CT": "America/Chicago", "ME": "America/New_York", "MA": "America/New_York", "NH": "America/New_York",
    "VT": "America/New_York", "RI": "America/New_York", "NY": "America/New_York", "NJ": "America/New_York",
    "PA": "America/New_York", "DE": "America/New_York", "MD": "America/New_York", "DC": "America/New_York",
    "VA": "America/New_York", "WV": "America/New_York", "NC": "America/New_York", "SC": "America/New_York",
    "GA": "America/New_York", "FL": "America/New_York", "OH": "America/New_York", "MI": "America/New_York",
    "IN": "America/New_York", "KY": "America/New_York", "TN": "America/Chicago", "AL": "America/Chicago",
    "MS": "America/Chicago", "LA": "America/Chicago", "AR": "America/Chicago", "MO": "America/Chicago",
    "IL": "America/Chicago", "WI": "America/Chicago", "MN": "America/Chicago", "IA": "America/Chicago",
    "ND": "America/Chicago", "SD": "America/Chicago", "NE": "America/Chicago", "KS": "America/Chicago",
    "OK": "America/Chicago", "TX": "America/Chicago", "MT": "America/Denver", "WY": "America/Denver",
    "CO": "America/Denver", "NM": "America/Denver", "UT": "America/Denver", "ID": "America/Denver",
    "AZ": "America/Phoenix", "NV": "America/Los_Angeles", "CA": "America/Los_Angeles",
    "OR": "America/Los_Angeles", "WA": "America/Los_Angeles", "AK": "America/Anchorage", "HI": "Pacific/Honolulu",
    "PR": "America/Puerto_Rico",
}

STATUSES = {"new", "announced", "registered", "declined", "attended", "past", "cancelled"}
PLATFORMS = {"zoom", "google_form", "microsoft_form", "eventbrite", "qualtrics", "redcap",
             "surveymonkey", "jotform", "calendly", "email", "teams", "webex", "website", "unknown"}

STOPWORDS = {"the", "of", "and", "at", "in", "for", "program", "programs", "residency", "internal",
             "medicine", "im", "medical", "center", "health", "hospital", "university", "school",
             "system", "healthcare", "regional", "campus", "college", "inc", "llc", "dba", "&"}


# ----------------------------------------------------------------------------- io
def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    os.replace(tmp, path)


def load_state():
    st = load_json(EVENTS, {"version": 1, "events": {}, "runs": []})
    st.setdefault("events", {})
    st.setdefault("runs", [])
    return st


# ----------------------------------------------------------------------------- normalisation
def norm_tokens(s: str) -> set:
    s = re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower())
    s = s.replace("st ", "saint ").replace("mt ", "mount ")
    return {t for t in s.split() if t and t not in STOPWORDS}


def norm_program_key(s: str) -> str:
    return " ".join(sorted(norm_tokens(s)))[:80]


def parse_tz(name: str | None, state: str | None) -> ZoneInfo:
    if name:
        n = name.strip()
        if state and state.upper() == "AZ" and n.upper() in ("MT", "MST", "MDT", "MOUNTAIN", "ARIZONA"):
            return ZoneInfo("America/Phoenix")  # Arizona never observes DST
        if n.upper() in TZ_ALIASES:
            return ZoneInfo(TZ_ALIASES[n.upper()])
        try:
            return ZoneInfo(n)
        except Exception:
            pass
    if state and state.upper() in STATE_TZ:
        return ZoneInfo(STATE_TZ[state.upper()])
    return ZoneInfo("America/New_York")


def parse_when(date_s: str | None, time_s: str | None, tz: ZoneInfo):
    """Return (start_dt or None, all_day bool). Accepts ISO date, 'Sept 12, 2026', 'September 12 2026';
    time like '6:00 PM', '18:00', '6pm', '6-7 PM' (first time wins)."""
    if not date_s:
        return None, True
    d = None
    ds = date_s.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y",
                "%A, %B %d, %Y", "%A %B %d, %Y", "%A, %b %d, %Y", "%d %B %Y", "%d %b %Y"):
        try:
            d = dt.datetime.strptime(ds.replace("Sept ", "Sep ").replace(".", ""), fmt).date()
            break
        except ValueError:
            continue
    if d is None:
        m = re.search(r"(\d{4})-(\d{2})-(\d{2})", ds)
        if m:
            d = dt.date(int(m[1]), int(m[2]), int(m[3]))
    if d is None:
        return None, True
    if not time_s:
        return dt.datetime(d.year, d.month, d.day, tzinfo=tz), True
    t = time_s.strip().lower().replace(".", "")
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", t)
    if not m:
        return dt.datetime(d.year, d.month, d.day, tzinfo=tz), True
    hh = int(m[1]); mm = int(m[2] or 0); ap = m[3]
    if not ap:  # look for an am/pm later in the string ("6-7 pm")
        m2 = re.search(r"(am|pm)", t)
        ap = m2[1] if m2 else None
    if ap == "pm" and hh < 12:
        hh += 12
    if ap == "am" and hh == 12:
        hh = 0
    if hh > 23:
        return dt.datetime(d.year, d.month, d.day, tzinfo=tz), True
    return dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=tz), False


def event_id(program: str, start: dt.datetime | None, title: str) -> str:
    key = norm_program_key(program) + "|" + (start.date().isoformat() if start else norm_program_key(title))
    return "oh_" + hashlib.sha1(key.encode()).hexdigest()[:10]


# ----------------------------------------------------------------------------- program matching
_PROGRAMS = None


def programs():
    global _PROGRAMS
    if _PROGRAMS is None:
        d = load_json(PROGRAMS, {"programs": [], "excluded": []})
        for p in d["programs"]:
            p["_tok"] = norm_tokens(p["program"])
        for p in d["excluded"]:
            p["_tok"] = norm_tokens(p["program"])
        _PROGRAMS = d
    return _PROGRAMS


def match_program(name: str, state: str | None = None):
    """Best fuzzy match against my_programs.json. Returns (record, score, list_name) or (None, 0, None)."""
    q = norm_tokens(name)
    if not q:
        return None, 0.0, None
    best = (None, 0.0, None)
    for list_name in ("programs", "excluded"):
        for p in programs()[list_name]:
            t = p["_tok"]
            if not t:
                continue
            inter = len(q & t)
            if inter == 0:
                continue
            score = inter / max(1, min(len(q), len(t)))
            if state and p.get("state") and str(p["state"]).upper() == state.upper():
                score += 0.15
            elif state and p.get("state") and str(p["state"]).upper() != state.upper():
                score -= 0.25
            if score > best[1]:
                best = (p, score, list_name)
    if best[1] < 0.6:
        return None, best[1], None
    return best


def tag_for(rec, list_name):
    if rec is None:
        return {"on_my_list": False, "tier": None, "priority_rank": None, "visa": None,
                "grad_cutoff_risk": None, "excluded_why": None}
    if list_name == "excluded":
        return {"on_my_list": False, "tier": "X", "priority_rank": None, "visa": None,
                "grad_cutoff_risk": None, "excluded_why": rec.get("why")}
    return {"on_my_list": True, "tier": rec.get("tier"), "priority_rank": rec.get("priority_rank"),
            "visa": rec.get("visa"), "grad_cutoff_risk": rec.get("grad_cutoff_risk"), "excluded_why": None,
            "list_program": rec.get("program"), "state": rec.get("state")}


# ----------------------------------------------------------------------------- ingest
REQUIRED = ("program", "title", "source_url")


def validate_candidates(cands):
    errs = []
    if not isinstance(cands, list):
        return ["top level must be a list"]
    for i, c in enumerate(cands):
        for k in REQUIRED:
            if not c.get(k):
                errs.append(f"[{i}] missing {k}")
        if c.get("platform") and c["platform"] not in PLATFORMS:
            errs.append(f"[{i}] platform {c['platform']!r} not in {sorted(PLATFORMS)}")
        if not c.get("date") and not c.get("date_tbd"):
            errs.append(f"[{i}] needs 'date' (YYYY-MM-DD) or date_tbd: true")
    return errs


def ingest(path, run_date):
    cands = load_json(path, None)
    if cands is None:
        sys.exit(f"cannot read {path}")
    errs = validate_candidates(cands)
    if errs:
        sys.exit("candidate file invalid:\n  " + "\n  ".join(errs))
    st = load_state()
    ev = st["events"]
    new, updated, dup = [], [], []
    for c in cands:
        tz = parse_tz(c.get("timezone"), c.get("state"))
        start, all_day = parse_when(c.get("date"), c.get("time"), tz)
        end = None
        if start and not all_day:
            end_s = c.get("end_time")
            if end_s:
                e, _ = parse_when(c.get("date"), end_s, tz)
                end = e if e and e > start else None
            end = end or (start + dt.timedelta(minutes=int(c.get("duration_min") or 60)))
        eid = event_id(c["program"], start, c["title"])
        rec, score, lname = match_program(c["program"], c.get("state"))
        tags = tag_for(rec, lname)
        rec_out = {
            "id": eid,
            "program": c["program"].strip(),
            "state": (c.get("state") or tags.get("state") or "").upper() or None,
            "title": c["title"].strip(),
            "event_type": c.get("event_type") or "virtual open house",
            "date": start.date().isoformat() if start else None,
            "date_tbd": bool(c.get("date_tbd")) or start is None,
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
            "all_day": all_day,
            "timezone": str(tz),
            "start_phoenix": start.astimezone(HOME_TZ).isoformat() if start and not all_day else None,
            "registration_url": c.get("registration_url"),
            "platform": c.get("platform") or "unknown",
            "source_url": c["source_url"],
            "source_kind": c.get("source_kind") or "web",
            "audience": c.get("audience"),
            "notes": c.get("notes"),
            "match": tags,
            "match_score": round(score, 2),
        }
        if eid in ev:
            old = ev[eid]
            changed = False
            for k in ("registration_url", "start", "end", "title", "notes", "platform", "audience"):
                if rec_out.get(k) and rec_out.get(k) != old.get(k):
                    if k == "registration_url" and old.get(k):
                        continue  # keep first registration link unless it was empty
                    old[k] = rec_out[k]; changed = True
            old["last_seen"] = run_date
            old.setdefault("seen_count", 1)
            old["seen_count"] += 1
            (updated if changed else dup).append(eid)
        else:
            rec_out["status"] = "new"
            rec_out["first_seen"] = run_date
            rec_out["last_seen"] = run_date
            rec_out["seen_count"] = 1
            rec_out["registration"] = None
            ev[eid] = rec_out
            new.append(eid)
    st["runs"].append({"date": run_date, "candidates": len(cands), "new": len(new),
                       "updated": len(updated), "duplicates": len(dup)})
    save_json(EVENTS, st)
    print(f"INGESTED candidates={len(cands)} new={len(new)} updated={len(updated)} duplicates={len(dup)}")
    for eid in new:
        e = ev[eid]
        print(f"  NEW {eid} | {e['program']} | {e['date'] or 'TBD'} | tier={e['match']['tier']}")
    return new


# ----------------------------------------------------------------------------- digest
TZ_ABBR = {"America/New_York": ("EST", "EDT"), "America/Chicago": ("CST", "CDT"),
           "America/Denver": ("MST", "MDT"), "America/Phoenix": ("MST", "MST"),
           "America/Los_Angeles": ("PST", "PDT"), "America/Anchorage": ("AKST", "AKDT"),
           "Pacific/Honolulu": ("HST", "HST"), "America/Puerto_Rico": ("AST", "AST"), "UTC": ("UTC", "UTC")}


def tz_abbr(d: dt.datetime) -> str:
    name = str(d.tzinfo)
    if name in TZ_ABBR:
        return TZ_ABBR[name][1 if d.dst() else 0]
    z = d.strftime("%Z")
    return z if z and not z.startswith("UTC") else name


def fmt_local(e):
    if not e.get("start"):
        return "date TBD"
    s = dt.datetime.fromisoformat(e["start"])
    try:
        s = s.astimezone(ZoneInfo(e.get("timezone") or "America/New_York"))
    except Exception:
        pass
    if e.get("all_day"):
        return s.strftime("%a %b %-d, %Y") + " (time TBD)"
    tzabbr = tz_abbr(s)
    loc = s.strftime(f"%a %b %-d, %Y · %-I:%M %p {tzabbr}")
    p = s.astimezone(HOME_TZ)
    if p.strftime("%Y-%m-%d %H:%M") != s.strftime("%Y-%m-%d %H:%M"):
        loc += p.strftime(" (= %-I:%M %p Phoenix)")
    if e.get("end"):
        en = dt.datetime.fromisoformat(e["end"])
        loc = loc.replace(" (=", en.strftime("–%-I:%M %p") + " (=", 1) if " (=" in loc else loc + en.strftime("–%-I:%M %p")
    return loc


def tier_badge(m):
    if m.get("excluded_why"):
        return f"⛔ excluded ({m['excluded_why']})"
    if not m.get("on_my_list"):
        return "▫️ not on my list"
    t = m.get("tier")
    if t == "U":
        t = "U (no roster data in my sweep)"
    star = f" · ★ priority #{m['priority_rank']}" if m.get("priority_rank") else ""
    visa = f" · visa: {m['visa']}" if m.get("visa") else ""
    risk = " · ⚠️ grad-year cutoff" if m.get("grad_cutoff_risk") == "HARD" else ""
    return f"Tier {t}{star}{visa}{risk}"


def sort_key(e):
    return (e.get("date") or "9999-12-31", e.get("start") or "")


def render_digest(run_date: str):
    st = load_state()
    ev = st["events"]
    today = dt.date.fromisoformat(run_date)
    # roll past events
    for e in ev.values():
        if e.get("date") and dt.date.fromisoformat(e["date"]) < today and e["status"] in ("new", "announced", "registered"):
            e["status"] = "past" if e["status"] != "registered" else "attended"
    new = sorted([e for e in ev.values() if e["status"] == "new"], key=sort_key)
    soon = sorted([e for e in ev.values() if e["status"] in ("announced", "registered")
                   and e.get("date") and today <= dt.date.fromisoformat(e["date"]) <= today + dt.timedelta(days=7)],
                  key=sort_key)
    later = sorted([e for e in ev.values() if e["status"] in ("announced", "registered")
                    and e.get("date") and dt.date.fromisoformat(e["date"]) > today + dt.timedelta(days=7)],
                   key=sort_key)
    tbd = [e for e in ev.values() if e["status"] == "announced" and not e.get("date")]

    def line(i, e, numbered=True):
        head = f"{i}. " if numbered else "- "
        reg = f" · [Register]({e['registration_url']})" if e.get("registration_url") else " · registration: see source"
        stat = {"registered": " · ✅ registered", "declined": " · ❌ declined"}.get(e["status"], "")
        out = (f"{head}**{e['program']}**{(' (' + e['state'] + ')') if e.get('state') else ''} — {e['title']}\n"
               f"   {fmt_local(e)} · {tier_badge(e['match'])}{stat}\n"
               f"   {reg} · [Source]({e['source_url']}) · `{e['id']}`")
        if e.get("notes"):
            out += f"\n   _{e['notes']}_"
        return out

    md = [f"# IM virtual open houses — {today.strftime('%A, %B %-d, %Y')}", ""]
    if new:
        md.append(f"## 🆕 New since last run ({len(new)})")
        md.append("")
        for i, e in enumerate(new, 1):
            md.append(line(i, e))
        md.append("")
        md.append("**Reply in Claude Code:** `/im-open-houses signup 1,3` (numbers above) or "
                  "`/im-open-houses signup all` — registrations use khan.muhammad2@mayo.edu. "
                  "Nothing is submitted until you say so.")
    else:
        md.append("## 🆕 New since last run: none")
        md.append("")
        md.append("No newly posted IM virtual open houses were found today. Sources were checked; see run notes.")
    md.append("")
    if soon:
        md.append(f"## 📅 Coming up in the next 7 days ({len(soon)})")
        md.append("")
        for e in soon:
            md.append(line(None, e, numbered=False))
        md.append("")
    if later:
        md.append(f"## 🗓 Later ({len(later)})")
        md.append("")
        for e in later:
            md.append(line(None, e, numbered=False))
        md.append("")
    if tbd:
        md.append(f"## ❓ Announced, date not yet posted ({len(tbd)})")
        md.append("")
        for e in tbd:
            md.append(line(None, e, numbered=False))
        md.append("")
    reg_n = sum(1 for e in ev.values() if e["status"] == "registered")
    md.append(f"_Tracked: {len(ev)} events · registered: {reg_n} · tiers from my_programs.json (2026-07-19 sweep)._")
    # mark new -> announced happens in `commit-run`, not here, so a re-render is idempotent
    save_json(EVENTS, st)
    return "\n".join(md), new


def cmd_digest(run_date, out):
    md, new = render_digest(run_date)
    os.makedirs(RUNS, exist_ok=True)
    path = out or os.path.join(RUNS, f"{run_date}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(md + "\n")
    print(md)
    print(f"\nDIGEST_PATH={path}\nNEW_COUNT={len(new)}")


def cmd_commit_run(run_date):
    """Flip 'new' -> 'announced' after the digest has been delivered."""
    st = load_state()
    n = 0
    for e in st["events"].values():
        if e["status"] == "new":
            e["status"] = "announced"; e["announced_on"] = run_date; n += 1
    save_json(EVENTS, st)
    print(f"announced={n}")


def cmd_calendar_json(run_date):
    """Events not yet pushed to Google Calendar, as ready-to-create payloads."""
    st = load_state()
    out = []
    for e in st["events"].values():
        if e.get("calendar_added") or not e.get("start") or e["status"] in ("declined", "past", "cancelled"):
            continue
        if e["match"].get("excluded_why"):
            continue  # programs I excluded (e.g. no visa sponsorship) stay off the calendar
        s = dt.datetime.fromisoformat(e["start"])
        if s.date() < dt.date.fromisoformat(run_date):
            continue
        payload = {
            "id": e["id"],
            "summary": f"[IM open house] {e['program']} — {e['title']}",
            "description": (f"{e['title']}\nProgram: {e['program']} ({e.get('state') or ''})\n"
                            f"{tier_badge(e['match'])}\nRegister: {e.get('registration_url') or 'see source'}\n"
                            f"Source: {e['source_url']}\nStatus: {e['status']}\nevent id: {e['id']}"),
            "timezone": e["timezone"],
        }
        if e.get("all_day"):
            payload["start_date"] = e["date"]; payload["end_date"] = (s.date() + dt.timedelta(days=1)).isoformat()
        else:
            payload["start"] = e["start"]; payload["end"] = e.get("end") or (s + dt.timedelta(hours=1)).isoformat()
        out.append(payload)
    print(json.dumps(out, indent=1))


def cmd_mark(eid, status, note, extra):
    st = load_state()
    e = st["events"].get(eid)
    if not e:
        sys.exit(f"unknown event id {eid}")
    if status not in STATUSES:
        sys.exit(f"status must be one of {sorted(STATUSES)}")
    e["status"] = status
    if status == "registered":
        e["registration"] = {"when": dt.datetime.now(HOME_TZ).isoformat(), "email": "khan.muhammad2@mayo.edu",
                             "note": note, **extra}
    elif note:
        e["notes"] = ((e.get("notes") or "") + " | " + note).strip(" |")
    if extra.get("calendar_added"):
        e["calendar_added"] = True
    save_json(EVENTS, st)
    print(f"{eid} -> {status}")


def cmd_status():
    st = load_state()
    from collections import Counter
    c = Counter(e["status"] for e in st["events"].values())
    print(f"events={len(st['events'])} {dict(c)}")
    print(f"runs={len(st['runs'])} last={st['runs'][-1] if st['runs'] else None}")


# ----------------------------------------------------------------------------- query bank
def cmd_queries(run_date):
    y = dt.date.fromisoformat(run_date).year
    season = f"{y}-{(y + 1) % 100:02d}"
    base = [
        f'"internal medicine" residency "virtual open house" {y}',
        f'"internal medicine residency" "virtual open house" register',
        f'"internal medicine" residency "virtual information session" {y}',
        f'"internal medicine" residency "virtual info session" applicants {y}',
        f'"internal medicine" residency "meet and greet" virtual applicants {y}',
        f'"internal medicine" residency "open house" zoom applicants {y}',
        f'"internal medicine" residency "Q&A session" virtual applicants {y}',
        f'"internal medicine" residency webinar prospective applicants {y}',
        f'"internal medicine" residency "virtual open house" IMG',
        f'"internal medicine" residency "open house" "{season}" OR "{y + 1} match"',
        f'"internal medicine" residency "virtual open house" September {y}',
        f'"internal medicine" residency "virtual open house" October {y}',
        f'"internal medicine" residency "virtual open house" November {y}',
        f'"internal medicine" residency "virtual open house" December {y}',
        f'site:zoom.us "internal medicine" residency open house',
        f'site:eventbrite.com "internal medicine" residency virtual open house',
        f'site:forms.gle OR site:docs.google.com/forms "internal medicine residency" open house',
        f'site:forms.office.com "internal medicine residency" open house',
        f'site:x.com "internal medicine" residency "virtual open house"',
        f'site:instagram.com "internal medicine residency" "open house"',
        f'site:reddit.com "virtual open house" "internal medicine" {y}',
        f'"IM residency" "virtual open house" {y}',
        f'"categorical internal medicine" "open house" virtual {y}',
        f'"med-peds" OR "internal medicine" residency "virtual open house" {y}',
        f'"preliminary" "internal medicine" residency "open house" virtual {y}',
    ]
    print("\n".join(base))


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    today = dt.datetime.now(HOME_TZ).date().isoformat()

    p = sub.add_parser("ingest"); p.add_argument("path"); p.add_argument("--run-date", default=today)
    p = sub.add_parser("validate"); p.add_argument("path")
    p = sub.add_parser("digest"); p.add_argument("--run-date", default=today); p.add_argument("--out")
    p = sub.add_parser("commit-run"); p.add_argument("--run-date", default=today)
    p = sub.add_parser("calendar-json"); p.add_argument("--run-date", default=today)
    p = sub.add_parser("mark"); p.add_argument("id"); p.add_argument("status"); p.add_argument("--note")
    p.add_argument("--calendar-added", action="store_true"); p.add_argument("--confirmation")
    p = sub.add_parser("match"); p.add_argument("name"); p.add_argument("--state")
    p = sub.add_parser("queries"); p.add_argument("--run-date", default=today)
    sub.add_parser("status")
    a = ap.parse_args()

    if a.cmd == "ingest":
        ingest(a.path, a.run_date)
    elif a.cmd == "validate":
        errs = validate_candidates(load_json(a.path, None))
        print("OK" if not errs else "\n".join(errs)); sys.exit(1 if errs else 0)
    elif a.cmd == "digest":
        cmd_digest(a.run_date, a.out)
    elif a.cmd == "commit-run":
        cmd_commit_run(a.run_date)
    elif a.cmd == "calendar-json":
        cmd_calendar_json(a.run_date)
    elif a.cmd == "mark":
        extra = {}
        if a.calendar_added: extra["calendar_added"] = True
        if a.confirmation: extra["confirmation"] = a.confirmation
        cmd_mark(a.id, a.status, a.note, extra)
    elif a.cmd == "match":
        rec, score, lname = match_program(a.name, a.state)
        print(json.dumps({"match": rec and {k: v for k, v in rec.items() if k != "_tok"}, "score": round(score, 2),
                          "list": lname}, indent=1, default=str))
    elif a.cmd == "queries":
        cmd_queries(a.run_date)
    elif a.cmd == "status":
        cmd_status()


if __name__ == "__main__":
    main()
