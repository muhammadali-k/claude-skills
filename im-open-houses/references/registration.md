# Registration playbook (`signup` mode)

Live-surveyed 2026-09-01 across ~20 IM program pages and 6 enumerable forms. Nothing here
is guessed: platforms and field lists were read from the actual pages.

## What open-house forms actually ask (2026 survey)

| Field | Frequency (6 forms) | Profile key |
|---|---|---|
| First / last name (or single "Name") | 4/6, always required | `first_name`, `last_name`, `full_name` |
| Email | 4/6, always required | `email` (**khan.muhammad2@mayo.edu**) |
| Medical school / "college or university you currently attend" | 4/6 (3 required) | `medical_school` — but if the wording is *currently attend*, use `current_institution` + " (medical school: " + `medical_school_short` + ")" only if the box is free text; for a plain "Medical school" box use `medical_school` |
| Questions for the panel (free text) | 4/6, usually optional | `default_question_for_panel` |
| Session/date radio | 1/6 | pick the session the user chose (earliest if unspecified) |
| "How did you hear about us" | 1/6 | "Program website" |
| "Email me info even if I can't attend" | 1/6 | Yes |
| AAMC / ECFMG / NRMP ID, DOB, phone, visa, scores | **0/6** | never auto-fill — see below |

Rule: **an open-house RSVP that demands AAMC/ECFMG/NRMP IDs, DOB, scores, or citizenship is
unusual.** Stop, show the user the form, and fill those only if he says so in that session.
Phone is in the profile and may be entered when a form makes it mandatory; DOB and IDs are
not entered without an explicit per-form OK.

Standard answers when asked:
- Applicant type → *International medical graduate (non-US IMG)*; degree *MBBS*; graduation *2023*.
- Visa → *Yes, requires sponsorship (J-1 or H-1B)*.
- Current role → *Research Fellow, Mayo Clinic Arizona*.
- Specialty of interest → *Internal Medicine (categorical)*; season *ERAS 2027 / Match 2027*.
- Pronouns → He/Him.

## Platform playbooks

### Microsoft Forms (`forms.office.com`, `forms.cloud.microsoft`) — **browser only**
Seen at UNMC and MaineHealth (the two live IM registrations found). React shell; the
anonymous JSON API returns error 674, so there is no headless path.
1. Open in Chrome. Some forms show a cover page — click **Start now** before fields exist.
2. `read_page` (interactive filter) → fields carry `aria-label="Required to answer"`.
3. `form_input` each field by ref; radios: click the option. Textareas accept `form_input`.
4. Screenshot → **Submit** → screenshot the "Your response was submitted" page.
5. No email confirmation is sent by MS Forms by default; the screenshot is the record.

### Zoom webinar / meeting registration (`*.zoom.us/webinar/register/...`, `/meeting/register/...`) — **browser only**
Vue SPA behind Cloudflare with a possible CAPTCHA. Default fields: First name, Last name,
Email (required), sometimes custom questions (school, questions, "how did you hear").
- The Chrome extension's site allowlist **currently blocks `*.zoom.us`** — the user must
  add it in the Claude-in-Chrome extension settings before Zoom sign-ups can run. If the
  tool refuses the domain, say exactly that and hand him the link.
- Zoom links expire fast after the event (several 2025 links now 404) — register early.
- If a CAPTCHA appears, stop and ask the user to solve it (never bypass).
- Confirmation: the page shows "Webinar Registration Approved" with the join link, and Zoom
  emails the join link to the Mayo address. Record the join URL in `--confirmation`.

### Google Forms (`docs.google.com/forms/.../viewform`, `forms.gle`) — **headless POST is the reliable path**
**Observed 2026-09-01 (Baystate form):** in the Chrome tool, text fields fill fine but `role=radio`
options did NOT toggle by ref-click, coordinate click, dispatched mouse events, or Space — the
form stayed unsubmittable. The headless POST below worked first time ("Your response has been
recorded"). So for Google Forms: read the field ids with curl, POST, and only fall back to Chrome
if the POST re-renders the form (validation error) or redirects to `ServiceLogin`.
In the 2026 IM sample Google Forms were used for *advance questions*, not registration
(MGH, Weill Cornell), but community programs use them for RSVPs too.
- `forms.gle` short links do **not** resolve under curl (JS deep-link page) — open in Chrome.
- Browser path: fill by ref, submit, screenshot "Your response has been recorded".
- Headless recipe (preferred): page source has `FB_PUBLIC_LOAD_DATA_`
  with `entry.NNN` ids and a hidden `fbzx`; `POST .../formResponse` with `entry.NNN=…`,
  `fvv=1`, `pageHistory=0`, `fbzx=<value>`. Parse ids with:
  `json.loads(re.search(r"FB_PUBLIC_LOAD_DATA_ = (.*?);</script>", html, re.S)[1])[1][1]` →
  each question `q[1]` is the title, `q[4][i][0]` the entry id, `q[4][i][2]` required, `q[4][i][1]`
  the option list. If the form shows an "Email *" responder box, send `emailAddress=<mayo email>`
  even when the logged-out HTML lacks `name="emailAddress"` (Baystate accepted it). Success = the
  response page contains "Your response has been recorded"; a re-rendered form means a
  validation error; a `ServiceLogin` redirect means login-gated → browser.

### Eventbrite / Qualtrics / SurveyMonkey / REDCap / Jotform / Calendly / SignUpGenius — **browser**
All JS-rendered (Qualtrics: "Javascript is required", field names like `QR~QID1~1~TEXT`).
Eventbrite may require a checkout step even for free tickets — complete it; do **not**
create an account (use "checkout as guest" if offered; otherwise stop and tell the user).

### Direct Zoom join / YouTube Live / "no registration required"
Nothing to submit. Mark the event `registered --note "no registration needed; join link: …"`
so the calendar entry carries the join URL, and add the link to the calendar description.

### Email RSVP (`mailto:` or "email the coordinator")
Draft with the template below, show it, send only after the user approves (Gmail connector
sends from kmuhammadali0224@gmail.com — say so; if he wants it from the Mayo address, he
must send it himself, so give him the text).

```
Subject: RSVP — Internal Medicine Residency Virtual Open House, <date>

Dear <Coordinator name or "Program Coordinator">,

I would like to register for the <Program name> Internal Medicine Residency virtual open
house on <date, time, timezone>. Please let me know if any further details are required.

Name: Muhammad Ali Khan
Email: khan.muhammad2@mayo.edu
Medical school: Nishtar Medical University, Multan, Pakistan (MBBS, 2023)
Current position: Research Fellow, Mayo Clinic Arizona
Applying: Internal Medicine, ERAS 2027

Thank you for hosting the session.

Kind regards,
Muhammad Ali Khan
```

## Browser hygiene (every sign-up)
1. `tabs_context_mcp` → `tabs_create_mcp` (never reuse another task's tab) → `navigate`.
2. Fill → `screenshot` (save_to_disk) **before** submit → submit → `screenshot` after.
3. Read the confirmation text; record with
   `python3 scripts/openhouse.py mark <id> registered --confirmation "<text / join link>"`.
4. Close the tab. Never accept cookie banners beyond "reject non-essential"; never create
   accounts; never enter payment details (no open house should ask).
5. If the same event has two mechanisms (register + questions form), do the registration
   first; submit the questions form with `default_question_for_panel` only if it is optional
   and quick.

## Profile schema (`data/profile.local.json`, gitignored)
```json
{
  "first_name": "", "last_name": "", "full_name": "", "pronouns": "",
  "email": "khan.muhammad2@mayo.edu", "personal_email": "", "phone": "",
  "current_position": "", "current_institution": "", "position_line": "",
  "medical_school": "", "medical_school_short": "", "medical_school_country": "",
  "degree": "MBBS", "graduation_year": 2023, "graduation_month": "",
  "applicant_type": "Non-US IMG", "is_img": true, "citizenship": "",
  "visa_status": "", "needs_visa_sponsorship": true, "visa_preference": "",
  "ecfmg_certified": true, "ecfmg_certified_date": "",
  "aamc_id": "", "usmle_ecfmg_id": "", "eras_application_id": "", "nrmp_id": "",
  "specialty": "Internal Medicine (categorical)", "application_season": "ERAS 2027 / NRMP Match 2027",
  "additional_degree": "", "timezone": "America/Phoenix",
  "default_question_for_panel": "", "how_heard": "Program website", "session_preference": "earliest"
}
```
Only `first_name`, `last_name`, `email`, `medical_school`, `current_institution`, and
`default_question_for_panel` are needed for the forms seen in 2026; the rest exist so the
skill never has to guess. IDs are filled only on explicit per-form approval.
