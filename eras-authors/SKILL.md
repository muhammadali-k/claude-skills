---
name: eras-authors
description: >-
  Reformat a pasted list of publication authors into the ERAS (Electronic Residency
  Application Service) publications-field format: "Lastname" + first-initial +
  middle-initial(s) with no periods or spaces between the initials, authors
  comma-separated in the original publication order — e.g. "Cameron Blake Smith"
  becomes "Smith CB". Also scans the list for Muhammad Ali Khan's own name (any
  variant — "Muhammad Ali Khan", "M.A. Khan", "Khan M", already-abbreviated forms,
  etc.) and calls it out separately as "Khan MA", since ERAS's publications field is
  rich-text and requires selecting a name and clicking its "B" (bold) button after
  pasting — plain text pasted from chat cannot carry bold formatting on its own.
  Trigger whenever the user pastes a raw author list and asks to format/convert it
  for ERAS, reformat an author list into initials, or invokes /eras-authors — even
  without naming the skill explicitly.
---

# ERAS author-list formatter

## What this does

ERAS's publications section wants each author written as `Lastname` followed
immediately by initials (first, then any middle), no periods, no space between the
initials, authors separated by `, ` in the order they appear on the actual
publication. Example: `Cameron Blake Smith` → `Smith CB`.

The user (Muhammad Ali Khan) re-pastes a fresh author list for each publication he's
entering into ERAS. The repetitive part is the reformatting; the one judgment call
each time is spotting *his own* name in the list so he knows which name to select and
bold in ERAS's field afterward (plain text can't carry bold into a web rich-text
field — that has to happen by hand, in-browser, after pasting).

## Steps

1. **Split into individual authors.** The pasted block may be comma-separated,
   semicolon-separated, separated by "and"/"&", one-per-line, or carry superscript
   affiliation/footnote markers (`John Smith1,2`, `Jane Doe*`) — strip those markers,
   they are not part of the name.
2. **Drop credentials, not suffixes.** Strip trailing degrees/credentials (MD, PhD,
   MPH, MSc, RN, FACS, etc.) — these never appear in the ERAS format. Keep true name
   suffixes (Jr, Sr, II, III, IV) attached to the surname, e.g. `Smith Jr AB`.
3. **Identify the surname per author.** Default: the last name token is the surname.
   Watch for:
   - Multi-word surnames / particles (`van`, `van der`, `de`, `de la`, `von`, `St.`) —
     these stay attached to the surname, e.g. `Erik Van Der Berg` → `Van Der Berg E`.
   - Input already given "Lastname, Firstname [Middle]" (e.g. copied from a reference
     manager) — the comma there separates the name's own parts, not two authors.
     Recognize this by a capitalized single/multi-word token immediately followed by
     a comma and then 1–3 given names; treat it as one author, not two.
   - Input already in the target abbreviated form (e.g. pasted from PubMed's
     `Smith AB, Cline J` style) — leave those authors as-is, don't re-derive them.
4. **Build each author as `Lastname` + initials, no delimiter between initials and
   no periods** — first-name initial, then each middle-name initial, in order, e.g.
   `Maria M. Garcia` → `Garcia MM`, `John Cline` → `Cline J` (no middle name → single
   initial).
5. **Join with `, `**, preserving original author order — do not alphabetize.
6. **Find Muhammad Ali Khan in the list.** Match liberally: "Muhammad Ali Khan",
   "M. Ali Khan", "M A Khan", "Muhammad A. Khan", already-abbreviated "Khan MA" /
   "Khan M", etc. all resolve to `Khan MA` in the output (use `Khan M` only if the
   input has no middle name/initial at all for him). If no plausible match exists,
   say so rather than guessing which entry is his.

## Output

Give two things, every time:

1. The ready-to-paste line:
   ```
   Smith AB, Cline J, Garcia MM, Khan MA
   ```
2. A one-line callout naming his entry and the manual step it still needs:
   ```
   Your name: Khan MA — after pasting, select it in the ERAS field and click "B" to bold it.
   ```

If a name is genuinely ambiguous (can't tell which token is the surname, e.g. two
plausible split points with no other cue), ask rather than guessing — but don't stop
for anything a competent human copyeditor would resolve on sight.
