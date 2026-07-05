# Using Residency Explorer (via the Chrome extension)

Residency Explorer (residencyexplorer.org) is an AAMC tool with **source-verified, per-program interview and match data** — the best available for "how do applicants like me actually fare here" and for the **program-signal effect**. It requires the applicant's **AAMC login**, so drive it with the **claude-in-chrome extension** in the applicant's own browser. It is optional; the website-verification pass is not. Treat RE's visa and composition fields as *leads to verify on the program site*, not facts (see failure modes in `website-verification.md`).

## Getting in (the applicant must consent)

1. The applicant logs in with their **AAMC** credentials — you don't enter passwords.
2. RE shows a **Terms & Conditions** gate. Accepting a legal agreement is the **applicant's call** — ask them to accept (or to explicitly authorize you) before proceeding.
3. "Program Alignment" personalizes results by the applicant's scores, but it requires **entering their USMLE scores into a form** — get consent before entering personal data. You can do most of the useful work without it, from the **Explore Programs** table below.

## The Explore Programs table (the workhorse)

Left nav → **Explore Programs**. Set **Change Specialty** at the top. Each row is a program with these columns:

- **Program Alignment** (blank until you enter the applicant's profile).
- **Middle 80% of Scores**: *Step 2 CK — All Invited* range, *Level 2 CE — DOs Invited*. Compare the applicant's Step 2 to the invited range for a competitiveness read.
- **Interview Rate** by category: **Silver Signal**, **Gold Signal**, **No Signal** (the signal effect — how much a signal lifts interview odds); **In-State / Out-of-State**; **MD / DO / US IMG / Non-US IMG**.
- **City / State / Region.**

### How to read the key columns

- **Non-US IMG** here is the **interview rate for non-US IMG applicants** — i.e., attainability *per application* (higher = easier to land an interview). It is **not** the program's resident composition. A heavily-IMG program can show a *low* rate because it's flooded with applications. Read it alongside the roster composition you verify on the site.
- **Gold Signal vs No Signal** is the money column for signal strategy: e.g., "No signal 1% → Gold 37%" means a Gold signal is decisive there. Spend Gold where this lift is large *and* the applicant genuinely wants the program.
- **Step 2 — All Invited** range vs. the applicant's Step 2 = a quick reach/target/safety read.

## Filters (left "Refine By" panel)

- **Visas Accepted or Sponsored**: J-1, H1-B, F-1 OPT. Filtering to **H1-B** surfaces the both-visa-capable programs (most H-1B sponsors also do J-1). *Verify on the program site — RE's visa flags are sometimes wrong or stale.*
- **Location**: **Region** (the ~9 divisions) and **State**. Also **Display Applicant Type(s)** — keep Non-US IMG selected.

## Extraction tactic (fast + avoids the pagination trap)

The table **caps at 50 rows with no visible pager**. To get everything without fighting pagination:

1. Apply a **Region** or **State** filter so the result set is ≤50.
2. Call the extension's **`get_page_text`** on the tab — it returns the entire visible table as clean text (one line per program: name, score ranges, the signal/interview-rate numbers, city/state/region). Parse that.
3. For large regions (NY, etc.), filter by **State** (each state is well under 50) to avoid the cap.

Save each region/state extract to a small text file as you go, then parse them together.

## Reliability caveat (say this in the output)

RE is convenient and its interview-rate/signal data is uniquely valuable, but it has been observed to be **wrong on visa** (e.g., listing H-1B for a program that its own current GME policy says is J-1 only) and it does not tell you *which nationalities* fill the non-US IMG slots. Use RE to prioritize and to read the signal effect; use the **program website** to confirm visa and composition.
