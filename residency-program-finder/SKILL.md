---
name: residency-program-finder
description: >-
  Use this to decide **where to apply for U.S. medical residency** — building an apply list, rank
  list, or shortlist, or vetting specific programs. Any specialty; default Internal Medicine.

  Trigger whenever the user is picking, filtering, or ranking residency programs: "build me an
  apply list," "shortlist X programs," "which programs should I apply to," judging programs as
  reach/target/safety, or deciding how to spend program signals (Gold vs Silver). Also for finding
  which programs accept a given applicant by visa sponsorship (J-1/H-1B), nationality, medical
  school, or Step scores — especially **international medical graduates (IMGs)** and other
  visa-needing applicants. And when someone distrusts aggregators (Residency Explorer, FREIDA,
  residencyadvisor) and wants program websites checked directly for real resident makeup, visa
  policy, or on-site fellowships.

  Prefer over plain web search. Not for personal statements, interview prep, fellowship
  applications, USMLE study plans, or choosing a medical school.
---

# Residency Program Finder

Help an applicant decide **where to apply for residency** and **how to spend their program signals**, producing a ranked, match-tiered apply list backed by primary-source verification.

Works for any specialty; **default to Internal Medicine** if unspecified. Built for and most valuable to **international medical graduates (IMGs)**, but usable for any applicant.

## The one principle that makes this skill worth using

**The program's own website is the source of truth. Aggregators are a starting point, not an answer.**

Residency Explorer, FREIDA, residencyadvisor.com, residencymatch.ai, and Doximity are the fast way to *find* candidate programs and to read signal/score data. But they are routinely wrong or stale on the three things that actually decide an application:

1. **Who is currently in the program** (resident composition, and which nationalities are really represented),
2. **Which visas the program sponsors**, and
3. **Which fellowships are on-site.**

So the core of this skill is: for every serious candidate, **open the program's own site and read the current-resident roster, the visa/eligibility page, and the fellowship list.** Never present an aggregator number as fact without a website check — or, if the site hides the data, an explicit *"aggregator-only, unverified"* label.

Real failure modes this catches (all observed in practice):
- An aggregator listed a program as sponsoring **both J-1 and H-1B**; the program's own 2024 GME policy said **J-1 only**.
- A "**Pakistani resident at Program A**" turned out to be at **Program B** — a name-based mis-attribution. **Never infer nationality from a surname.**
- A program with a high headline "**% IMG**" turned out to fill its international slots with **Latin-American** grads, not the applicant's group.
- A program's live roster showed **name + photo only, no medical school** — so its nationality claims were aggregator-only, not roster-confirmed.

Read `references/website-verification.md` before doing the verification pass — it is the heart of this skill.

## Workflow

### Step 1 — Build the applicant profile

Ask for anything missing. Capture:

- **Specialty** (default Internal Medicine).
- **Degree & training country**; IMG status (US-citizen IMG vs **non-US IMG** — this distinction matters enormously).
- **USMLE** Step 1 / 2 CK / 3, ECFMG certification, English test.
- **Visa need**: J-1, H-1B, both/open, or none (citizen / green card). The single biggest filter for IMGs.
- **Years since medical-school graduation** — many programs enforce a 3–5 year cutoff; compute it to the intended *start* date.
- **Geographic preferences** (ERAS divisions) or "open." See `references/signals-and-geography.md`.
- **Career goal and PRIORITY WEIGHTING** — this drives the ranking. Examples of priorities: representation of the applicant's own nationality, both-visa sponsorship, university/research strength (for a physician-scientist), an on-site fellowship in their target subspecialty, or raw match-safety. Ask the applicant to rank these; don't assume.
- **Connections**: anyone they know at a program, and their **own medical school's alumni** (same-school ties are the single strongest connection).

Record an **affinity group** = the applicant's nationality / medical-school country whose representation they care about (this generalizes "how many residents share my background"). Track **same-medical-school** matches separately — they're the strongest form of it.

### Step 2 — Assemble a candidate pool (aggregators + Residency Explorer)

Define **IMG-friendly = more than ~20% NON-US IMG residents** (visa-requiring international grads) — *not* "% IMG," which folds in US-citizen IMGs and DOs and badly overstates an IMG's odds. Use the applicant's own threshold if they give one.

Pull candidates per chosen division from the sources in `references/data-sources.md`. If the Chrome extension + the applicant's AAMC login are available, use **Residency Explorer** for its per-program interview-rate, signal-effect, and score data — see `references/residency-explorer.md` for exact navigation. RE is optional; the website pass (Step 3) is not.

**Also look outside the chosen geographic divisions** for standout programs — signals and applications are not restricted to the applicant's preference divisions. Cast a wide net now; Step 3 filters it.

### Step 3 — Verify each candidate on its own website (mandatory)

For every serious candidate, follow `references/website-verification.md` to open the program's site and extract:

- **Current-resident roster** → count non-US IMG; count **affinity-group residents by their medical-school country** (never by name); flag any **same-medical-school (alumni)** residents/faculty.
- **Visa / eligibility page** → J-1 / H-1B / none. If it conflicts with an aggregator, **the program page wins.**
- **Fellowship list** → is the applicant's target-subspecialty fellowship on-site? Is there a research / physician-scientist track?
- **Program type** → true university vs university-affiliated vs community.

Use **WebFetch first** (fast). Use the **Chrome extension** (`get_page_text` / `read_page`) for sites that block WebFetch (HTTP 403) or render the roster with JavaScript. When a site publishes no medical schools, fall back to an aggregator's school breakdown and **label it aggregator-only / lower-confidence.** Prefer the most recent roster. **Never fabricate a percentage, name, or count.**

If the candidate list is large, verify in priority order (signal candidates and top targets first) and be explicit about what you verified live vs. left aggregator-only.

### Step 4 — Score, tier, and rank

Score each program against the applicant's Step-1 priority weighting. Assign a **match tier**:

- **Reach** — strong/selective programs that take few applicants like them, but not zero.
- **Target** — realistic; they take this profile and the applicant is competitive.
- **Safety** — high-probability given the applicant's scores/profile vs. the program's verified bar.

Anchor tiers in **verified composition + the applicant's competitiveness** (their scores vs. the program's invited-score range where RE provides it; whether the roster shows people like them). Keep the overall portfolio matched to the applicant's stated risk tolerance.

### Step 5 — Geographic preferences & program signals

Read `references/signals-and-geography.md`. In brief:

- **Geographic preferences**: ERAS lets the applicant flag a few divisions. It's a soft signal to programs, **not a filter** — they can apply and signal anywhere.
- **Program signals**: the number is **specialty-specific**, and some specialties **tier them Gold/Silver** (e.g., Internal Medicine 2026-27 = 3 Gold + 12 Silver). Look up the current count for the specialty. Programs weight signals for **interview invitations, not rank lists.**
- **Allocation**: spend signals on **Reach/Target** programs where a signal moves the needle (RE's Gold-signal interview-rate column shows how much); **don't waste signals on near-certain safeties** — those interview strong applicants anyway. Put **Gold** on genuine top choices where a signal is decisive and/or there's a real connection (especially a same-school tie). Keep the mix matched to the applicant's risk tolerance.

### Step 6 — Produce the deliverables

Assemble the verified programs into a JSON array using the record schema in `scripts/README.md`, then run the bundled scripts (they save every future run from re-writing them):

```bash
python3 scripts/build_workbook.py programs.json --config config.json --out "<Applicant> program list.xlsx"
python3 scripts/build_interactive_list.py programs.json --config config.json --out "<Applicant> apply list.html"
```

- **build_workbook.py** → a sortable Excel workbook: a READ-ME/strategy sheet + the ranked list with signal (Gold/Silver), tier, verified non-US IMG %, affinity-group residents, visa, fellowships, and a live-verified flag.
- **build_interactive_list.py** → a single self-contained HTML file the applicant can search, sort, and filter (by tier, signal, visa, affinity, live-verified) and open offline.

Also write a short **strategy narrative**: the division comparison, the signal recommendation with reasons, and — importantly — the **website-verification corrections you found** (surfacing where aggregators were wrong builds trust and is often the most valuable output).

## Guardrails

- **Program website > aggregator, every time.** Label any unverified figure as aggregator-only.
- **Never invent** a percentage, resident name, or count. Count affinity by **medical-school country**, not surname.
- **Surface the discriminating caveats**: years-since-graduation cutoffs, visa specifics, and any program that sponsors no visa (disqualifying for a visa-requiring applicant).
- This is **decision support, not a guarantee.** Tell the applicant to re-confirm the shortlist in Residency Explorer and on program sites before certifying their ERAS list.
- Entering the applicant's scores into Residency Explorer's "Program Alignment," accepting site Terms & Conditions, or logging in are actions the **applicant must consent to** — don't do them unprompted.
