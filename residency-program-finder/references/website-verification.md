# Verifying a program on its own website

This is the heart of the skill. Aggregators (Residency Explorer, FREIDA, residencyadvisor.com, residencymatch.ai, Doximity) are fine for *finding* candidates and for signal/score data, but they are frequently wrong or stale on resident composition, nationality representation, and visa sponsorship. The program's own site is authoritative — go there for every serious candidate.

## What to open

Programs organize sites differently, but you are looking for three pages:

1. **The current-resident roster** — labeled "Current Residents," "Meet the Residents," "Housestaff," "Our Residents," "Residents & Fellows." This is where medical schools (and thus nationalities) live.
2. **The applying / eligibility / visa page** — "How to Apply," "Applicants," "Eligibility," "International Applicants," "FAQ." This states visa sponsorship and any USMLE-attempt or years-since-graduation rules.
3. **The fellowships page** — to confirm whether the applicant's target subspecialty fellowship is *on-site* (vs. system-wide, enterprise, or merely nearby).

## What to extract from the roster

For each resident, capture **medical school and its country**. Then compute:

- **Non-US IMG count / %** = residents whose medical school is outside the US and Canada, divided by the roster size. This — not "% IMG" — is the number that reflects a non-US IMG's odds.
- **Affinity-group count** = residents whose medical school is in the applicant's country. Report it as a count with schools (e.g., "6 — Aga Khan x2, Dow, King Edward, CMH Lahore, Shifa").
- **Same-medical-school (alumni) matches** = residents or faculty from the applicant's *own* medical school. Flag these prominently — a senior from your exact school is the strongest connection an applicant can have.

### The surname trap — never infer nationality from a name

A name is not evidence of a medical school. Requiring the roster to state the **medical-school country** is the whole point. In practice, name-based inference produces real errors — e.g., a resident credited to one program's "Pakistani" cohort was actually enrolled at a *different* program entirely. If the roster does not state the school's country, you have **not** confirmed the affinity count; say so.

### When the site hides medical schools

Some programs publish only names + photos (no schools), or put the school on each resident's individual profile page (expensive to open one-by-one). When you cannot get schools from the roster:

- Fall back to **residencyadvisor.com**'s per-program "school breakdown" (an aggregator estimate of feeder schools and non-US IMG %), and **label the result "aggregator-only / not roster-confirmed."**
- Note the limitation honestly. "Program hides medical schools on its live roster; Pakistani presence is aggregator-only" is a true and useful statement — it is much better than a fabricated count.

## Visa: read the program's own words

Read the eligibility/FAQ page verbatim and record exactly what it says (e.g., "We sponsor J-1 only," "H-1B for categorical, ECFMG-certified, Step 3 by rank list," "We are not able to sponsor visas"). **If the program page conflicts with an aggregator, the program page wins.** Watch specifically for:

- Programs that recently **dropped H-1B** (GME policy PDFs are often dated — take the most recent).
- "**Does not sponsor H-1B**" (J-1 only) vs. "**sponsors both**."
- Programs that **sponsor no visa** — disqualifying for any visa-requiring applicant; exclude them.

## Fellowships & program type

- Confirm the target-subspecialty fellowship is **on-site** (an ACGME fellowship at that institution), versus system/enterprise/nearby access. On-site matters most for a subspecialty-bound applicant.
- Note whether the program is a **true university** (medical-school-owned academic center), **university-affiliated** (community program with a university teaching relationship), or **community**. This matters for physician-scientist credibility.

## Tools & tactics

- **WebFetch first** — fast; ask it to "list each resident and their medical school; count how many trained outside the US/Canada; list any whose school is in <country>; and state the visa sponsorship and whether an on-site <subspecialty> fellowship is mentioned."
- **Chrome extension** (`get_page_text`, `read_page`, `navigate`) when WebFetch returns HTTP 403 or the roster is JavaScript-rendered. `get_page_text` captures a rendered roster as text cleanly.
- Prefer roster pages that list schools **inline**. Opening individual resident profiles is a last resort (slow, and often the school still isn't shown).
- Prefer **current-year** rosters; graduated residents don't count.

## Confidence labels to carry into the output

Tag every composition/visa datum as one of:

- **roster-confirmed** — read from the program's own current roster/visa page.
- **aggregator-only** — from residencyadvisor / RE / FREIDA; site didn't publish it.
- **unverified** — inferred or single-source; flag for the applicant to check.

Carrying these labels into the spreadsheet/HTML is what makes the deliverable trustworthy.
