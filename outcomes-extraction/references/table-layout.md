# Outcome table layouts — three families

There are **three template families**. They look nearly identical, they are **not** interchangeable,
and each has its **own field-ID set**:

| Family | File it came from | Columns | Key columns | Data block | Field IDs |
|---|---|---|---|---|---|
| `pwma` | `PWMA/pwma_template.xlsx` (and the legacy `OS/DFS/RFS *_to_extract.xlsx`) | A–Y (25) | F = Treatment Arm | G–Y (19 fields) | 3069–3089 |
| `nma` | `NMA/nma_template.xlsx` | A–X (24) | F = Treatment Arm | G–X (18 fields) | 21972–21993 |
| `pwma_subgroup` | `PWMA/pwma_subgroup_template.xlsx` | A–AA (27) | F = Subgroup, G = Extraction Possible, H = Treatment Arm | I–AA (19 fields) | 9432–9452 |

The legacy OS/DFS/RFS sheets are the `pwma` family with different IDs (OS 3223–3287, DFS 3243–3450,
RFS 3263–3283). `scripts/families.py` detects the family from the header; nothing keys off the
filename or the table key you choose.

Row 1 also carries a merged banner labelled **"Root Node"** spanning the whole data block
(G1:X1 / G1:Y1 / I1:AA1). It is not a field — it marks where the data columns begin.

---

## ⚠️ `Ec` AND `Et` MEAN DIFFERENT THINGS IN `pwma` AND `nma` ⚠️

```
pwma / pwma_subgroup     Et = EVENTS in treatment     Nt = N in treatment
                         Ec = EVENTS in control       Nc = N in control

nma                      Ec T1 = EVENT COUNT in T1    Et T1 = EVENT TOTAL (participants) in T1
                         Ec T2 = EVENT COUNT in T2    Et T2 = EVENT TOTAL (participants) in T2
```

**`Et` is an event COUNT in pwma and a participant TOTAL in nma.** There is no visual cue: an
extractor who carries one convention into the other writes the denominator where the numerator
belongs, the sheet still looks entirely plausible, and **nothing downstream catches it** — the
pooled effect is simply wrong.

Two defences, both already built in:
1. **Nothing in the pipeline speaks "Et"/"Ec".** The internal role names in `scripts/families.py`
   are `events_t`, `n_t`, `events_c`, `n_c`, and the result JSON always uses PWMA semantics
   (`et`=events-treatment, `nt`=N-treatment, `ec`=events-control, `nc`=N-control). The NMA
   relabelling happens once, in `assemble.py`, at write time.
2. **`scripts/qc.py` flags any row where an event count exceeds its own arm's denominator**, per
   family, and names the two columns to swap. That is the one arithmetic fact a swap always breaks.

If you ever hand-fill an NMA sheet, read the column header out loud before typing: *"Ec T1 is the
number of events; Et T1 is the number of patients."*

---

## Map by field ID / header role, NEVER by column letter
Each family assigns different IDs to the same role (Trial Name is 3069 in PWMA, 21972 in NMA, 9432 in
the subgroup sheet), and the subgroup template shifts every data column two letters right. Column
letters are therefore meaningless as identity. Resolve by the header label (with the `(ID: NNNN)` tag
stripped), and — in the NMA sheet — by the **row-2 group banner** as well, because the row-3 label
`T1` appears twice: once under **Regimen** (the arm name) and once under **Survival** (the landmark
rate). `families.py` does this; every script uses it.

## `pwma` — A–Y, comparison label in F, data G–Y

| Col | Header (ID) | Role | Meaning |
|---|---|---|---|
| G | Trial Name (3069) | `trial_name` | Short trial/acronym; `NA` if none |
| H | NCT (3070) | `nct` | Registry ID as printed |
| I | PMID (3071) | `pmid` | PubMed ID |
| J | O/F (3072) | `of` | Original vs Follow-up publication |
| K | (0 selected) (3073) | `zero` | Multi-select placeholder — `0` |
| L | Arms (3074) | `arms` | **Total arms in the trial** (same on every row of a study) |
| M | TE (3076) | `te` | Treatment effect = hazard ratio, treatment vs control |
| N | Lower CI (3077) | `lower_ci` | CI lower bound |
| O | Upper CI (3078) | `upper_ci` | CI upper bound |
| P | Treatment (3080) | `treatment` | Experimental arm name |
| Q | Control (3081) | `control` | Control arm name |
| R | Survival in Treatment (3082) | `surv_t` | Event-free rate (%) at the landmark, treatment |
| S | Survival in Control (3083) | `surv_c` | Event-free rate (%) at the landmark, control |
| **T** | **Et (3084)** | `events_t` | **EVENTS in treatment** |
| **U** | **Nt (3085)** | `n_t` | **N in treatment** (ITT) |
| **V** | **Ec (3086)** | `events_c` | **EVENTS in control** |
| **W** | **Nc (3087)** | `n_c` | **N in control** (ITT) |
| X | Median survival in treatment (3088) | `med_t` | Usually `NA` |
| Y | Median survival in control (3089) | `med_c` | Usually `NA` |

## `nma` — A–X, comparison label in F, data G–X
No `(0 selected)` column. Group banners in row 2: **Regimen** (L–M), **Result** (N–P),
**Survival** (Q–R), **Ec & Et** (S–V).

| Col | Header (ID) | Role | Meaning |
|---|---|---|---|
| G–K | Trial Name (21972), NCT (21973), PMID (21974), O/F (21975), Arms (21976) | as above | — |
| L | Regimen · T1 (21978) | `treatment` | **T1 = the treatment arm** (regimen name) |
| M | Regimen · T2 (21979) | `control` | **T2 = the active comparator**, usually the trial's control arm |
| N | Result · Measure (21981) | `te` | The effect estimate (HR), T1 vs T2 |
| O | Result · Lower CI (21982) | `lower_ci` | CI lower bound |
| P | Result · Upper CI (21983) | `upper_ci` | CI upper bound |
| Q | Survival · T1 (21985) | `surv_t` | Landmark event-free rate (%), T1 |
| R | Survival · T2 (21986) | `surv_c` | Landmark event-free rate (%), T2 |
| **S** | **Ec & Et · Ec T1 (21988)** | `events_t` | **EVENT COUNT in T1** |
| **T** | **Ec & Et · Et T1 (21989)** | `n_t` | **EVENT TOTAL = participants in T1** (ITT) |
| **U** | **Ec & Et · Ec T2 (21990)** | `events_c` | **EVENT COUNT in T2** |
| **V** | **Ec & Et · Et T2 (21991)** | `n_c` | **EVENT TOTAL = participants in T2** (ITT) |
| W | Median survival in treatment (21992) | `med_t` | Usually `NA` |
| X | Median survival in control (21993) | `med_c` | Usually `NA` |

## `pwma_subgroup` — A–AA, **two extra columns shift everything two letters right**
Same 19 roles and the same Et/Nt/Ec/Nc meaning as `pwma`, but the left-hand block gains two columns:

```
pwma          A  B  C  D  E  | F=Treatment Arm |                    G ... Y   (data)
subgroup      A  B  C  D  E  | F=Subgroup | G=Extraction Possible | H=Treatment Arm | I ... AA (data)
                               ^^^ two inserted columns ^^^         everything after shifts +2
```

| Col | Header (ID) | Role |
|---|---|---|
| F | Subgroup | the subgroup **level** for this row (e.g. `Risk group: M1 NED`) |
| G | Extraction Possible | whether this subgroup result can actually be extracted (see conventions.md) |
| H | Treatment Arm | the comparison label (`Primary`, `3 year Sorafenib`, …) |
| I–N | Trial Name (9432), NCT (9433), PMID (9434), O/F (9435), (0 selected) (9436), Arms (9437) | metadata |
| O–Q | TE (9439), Lower CI (9440), Upper CI (9441) | `te`, `lower_ci`, `upper_ci` |
| R–S | Treatment (9443), Control (9444) | `treatment`, `control` |
| T–U | Survival in Treatment (9445), Survival in Control (9446) | `surv_t`, `surv_c` |
| **V–Y** | **Et (9447), Nt (9448), Ec (9449), Nc (9450)** | **events-T, N-T, events-C, N-C — the pwma meaning** |
| Z–AA | Median survival in treatment (9451), in control (9452) | `med_t`, `med_c` |

**Row identity on the subgroup sheet is (study × comparison × subgroup level)** — the key needs all
three. The number of subgroup levels **varies by study and by subgroup type**: in the seeded
Living-Periop-RCC sheet most studies carry four risk-group levels (`High`,
`Intermediate-to-high`, `M0 High`, `M1 NED`) but study 1553 carries only two, and study 1515 carries
four levels for each of its two comparisons (8 rows). Never hardcode a count.

## Data types — every data cell is TEXT
In the seeded files every data cell is a text string (`'0.97'`, `'54'`, `'2'`, PMID `'36099926'`);
only col A (Paper ID) is numeric. That is what makes the upload robust: because the columns are TEXT,
the literal **`NA`** is valid everywhere, so any unreported field is simply `NA`. Write all data
values as strings and never leave a data cell blank.

The seeded files are inconsistent about the missing token — the PWMA sheet uses `NA`, `NR` and `NM`;
the subgroup sheet is pre-filled with `N/A`. **Write `NA`**; `qc.py` recognises all of those variants
when it computes fill-rates so an inherited `N/A` isn't mistaken for a real value.

## Identifiers
- **Trial Name / NCT** — read from the paper (NCT usually in the abstract/registration line); fall
  back to a project map for naming consistency. The seeded sheets sometimes carry a **DOI** in the
  NCT or PMID column — that is seed noise, not a convention; put the real identifier in.
- **PMID** — most reliable via the PubMed MCP `convert_article_ids` (DOI→PMID); back-fill from the
  seeded rows or read it off the paper. (idconv misses some DOIs — cross-check.)
- These go in `study_info` in the assemble config (see workflow.md), one entry per paper.
