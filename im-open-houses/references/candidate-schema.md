# Candidate file schema (`data/candidates_<RUN_DATE>.json`)

A JSON **list**. One object per event found during discovery. `openhouse.py validate` checks it.

```json
[
  {
    "program": "Trinity Health Livonia Hospital / Wayne State University Internal Medicine Residency",
    "state": "MI",
    "title": "Virtual Open House for 2027 Applicants",
    "event_type": "virtual open house",
    "date": "2026-09-15",
    "time": "6:00 PM",
    "end_time": "7:00 PM",
    "duration_min": 60,
    "timezone": "ET",
    "registration_url": "https://us02web.zoom.us/webinar/register/WN_xxxx",
    "platform": "zoom",
    "source_url": "https://www.trinityhealthmichigan.org/.../internal-medicine-residency",
    "source_kind": "program_site",
    "audience": "all applicants",
    "notes": "Coordinator: jane.doe@trinity-health.org; second session Oct 6 listed separately"
  }
]
```

| Field | Required | Rules |
|---|---|---|
| `program` | yes | Full official program name as printed, including sponsor/university if shown. Never abbreviate; the matcher needs the real words. |
| `state` | no (strongly recommended) | Two-letter USPS code. Used for timezone default and tier matching. |
| `title` | yes | The event's own title. |
| `event_type` | no | `virtual open house` (default), `virtual info session`, `meet and greet`, `Q&A webinar`, `IMG session`, `hybrid open house`. |
| `date` | yes unless `date_tbd` | ISO `YYYY-MM-DD` preferred; `September 15, 2026` also parses. One object per date if a series is listed. |
| `date_tbd` | — | `true` when announced without a date ("coming soon — details to follow"). |
| `time` / `end_time` | no | As printed, e.g. `6:00 PM`, `18:00`, `noon`→`12:00 PM`. Omit if not posted (event becomes all-day). |
| `duration_min` | no | Used when only a start time is posted (default 60). |
| `timezone` | no | As printed: `ET`, `CT`, `MT`, `PT`, `EST`, `Eastern`, or an IANA name. If absent, inferred from `state`. |
| `registration_url` | no | The actual sign-up link (Zoom/Google Form/Eventbrite/Microsoft Form/Qualtrics/REDCap/Calendly). Not the program homepage. |
| `platform` | no | One of `zoom, google_form, microsoft_form, eventbrite, qualtrics, redcap, surveymonkey, jotform, calendly, email, teams, webex, website, unknown`. |
| `source_url` | yes | The page where you read the announcement (program page, X/Instagram post, Reddit thread, aggregator row). |
| `source_kind` | no | `program_site, x, instagram, facebook, reddit, aggregator, eventbrite, zoom, email, other`. |
| `audience` | no | Who it is for, if stated (e.g. `IMGs`, `4th-year students`, `all applicants`). |
| `notes` | no | Anything a registrant needs: coordinator email, "IMG-only session", capacity limits, "registration closes Sep 10", uncertainty about the year. |

Exclusions (do not include): in-person-only events; fellowship or non-IM specialties; events dated before today; interview-day logistics for invited applicants only; generic "contact us" pages.

Dedup key computed by `ingest`: normalised program name + event date (or title when date TBD). Re-submitting the same event on later days is expected and harmless.
