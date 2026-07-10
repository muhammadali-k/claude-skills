# DOCX mechanics — tracked changes + threaded comments

Everything that touches the `.docx` goes through `scripts/docx_review.py`. Do **not** hand-edit the OOXML:
tracked changes and threaded comments span five interdependent parts, and one imbalance makes Word refuse
to open the file or silently drop your markup. The script keeps them consistent and self-validates.

## What a reviewed .docx actually contains

A `.docx` is a zip. The relevant parts:

- `word/document.xml` — the body. Tracked changes are `<w:ins>` / `<w:del>` wrappers (each with
  `w:author`, `w:date`, `w:id`) around runs; a deletion stores its text in `<w:delText>`. Comments are
  anchored by a `<w:commentRangeStart w:id=N/>` … `<w:commentRangeEnd w:id=N/>` pair plus a
  `<w:commentReference w:id=N/>` run.
- `word/comments.xml` — the comment bodies (`<w:comment w:id author date initials>` with paragraphs, each
  carrying a `w14:paraId`).
- `word/commentsExtended.xml` — **threading and resolved state**: `<w15:commentEx w15:paraId=…
  w15:paraIdParent=… w15:done=0|1>`. A reply points its `paraIdParent` at the **root** comment's paraId.
- `word/commentsIds.xml` — `w16cid` durable IDs (paraId → durableId).
- `word/commentsExtensible.xml` — `w16cex` per-durableId metadata (UTC date).
- `word/people.xml` — author presence list.
- `[Content_Types].xml` and `word/_rels/document.xml.rels` — register the comment parts. The script adds
  these registrations automatically when a document has no comments yet.

## The two invariants the tool guarantees

1. **Comment-range balance** — every comment id has exactly one `commentRangeStart`, one
   `commentRangeEnd`, one `commentReference`, and a body in `comments.xml`.
2. **Reject-all reproduces the original** — with all your tracked changes rejected, the document's text is
   identical to the input. This is the proof you only ever *added* reversible markup and never clobbered
   text. `apply` runs both checks; it errors rather than write a bad file.

## Workflow

### 1. Inspect

```
python scripts/docx_review.py inspect FILE.docx
```

Prints: every paragraph with its **index** and text; a **run breakdown** for paragraphs that contain
tracked changes or comment anchors (so you can see where run boundaries fall); and every **existing
comment** with author, thread (`reply->N`), and `[RESOLVED]` state. You anchor edits by paragraph index +
a text snippet, so this is where you find them.

`render FILE.docx accept|reject|clean|markup` prints the text in each view (`markup` shows
`[INS:…]`/`[DEL:…]` and `{{Cn> … <Cn}}` comment ranges).

### 2. Write an edit plan

A JSON file (`assets/plan.example.json` is a complete example):

```json
{
  "input":  "/abs/path/IN.docx",
  "output": "/abs/path/OUT_MAK_reviewed.docx",
  "reviewer": "Muhammad Ali Khan",
  "date": "2026-07-09T18:30:00Z",
  "edits": [
    {"type":"replace","paragraph":3,"find":"Three","replace":"Four","context":"concern. Three Phase"},
    {"type":"insert_after","paragraph":13,"anchor":"spleen volume reduction","text":", whereas parsaclisib did not"},
    {"type":"delete","paragraph":11,"find":"of G3 thrombocytopenia "},
    {"type":"comment_reply","parent":"52","text":"Re your question 'How?': ... - MAK"},
    {"type":"comment_on","paragraph":11,"target":"G3 anemia","text":"For parallelism ... - MAK","context":"lower risk of G3 anemia"}
  ]
}
```

**Edit operations** (all tracked changes are text-anchored and must land inside one run):

| type | args | effect |
|---|---|---|
| `replace` | `paragraph`, `find`, `replace`, `context?`, `occurrence?` | tracked delete of `find` + insert of `replace` |
| `delete` | `paragraph`, `find`, `context?`, `occurrence?` | tracked deletion |
| `insert_after` | `paragraph`, `anchor`, `text`, `context?`, `occurrence?` | tracked insertion right after `anchor` |
| `insert_before` | `paragraph`, `anchor`, `text`, `context?`, `occurrence?` | tracked insertion right before `anchor` |
| `comment_reply` | `parent` (existing comment id, string), `text` | threaded reply nested on that comment's range |
| `comment_on` | `paragraph`, `target`, `text`, `context?`, `occurrence?` | new comment anchored on `target` |

**Anchoring rules:**
- `find`/`anchor`/`target` must appear inside a **single plain run** (not spanning a run boundary or an
  existing tracked change). If it spans, the tool errors — pick a smaller snippet, or split into two edits.
- If a snippet occurs more than once in the paragraph, add `context` (a longer substring of the same run)
  or `occurrence` (1-based) to disambiguate. The tool errors if it's ambiguous.
- Paragraph indices come from `inspect`. They are stable within one run of the tool; each edit re-finds
  its run, so multiple edits in the same paragraph compose safely (do the `replace` that changes a word
  before an `insert_after` that depends on the surrounding text).

### 3. Apply + validate

```
python scripts/docx_review.py apply PLAN.json
```

Applies every edit, writes `output`, and runs both invariants. On any problem it prints what failed and
exits non-zero — fix the plan (usually an anchor that moved or an ambiguous `find`) and re-run. Re-running
is safe: it always starts from `input`, never from a half-edited file.

### 4. Eyeball + deliver

`render OUT.docx markup` to read the changes in place, `render OUT.docx accept` for the final text (check
the venue character count on this), and hand back the new file. Name it so the original is preserved
(e.g. `Name_MAK_reviewed.docx`).

## Using the library directly (advanced)

For anything the plan schema doesn't express, import it:

```python
import sys; sys.path.insert(0, "scripts")
from docx_review import DocxReview
dr = DocxReview("IN.docx", reviewer="Muhammad Ali Khan", date="2026-07-09T18:30:00Z")
for p in dr.report_paragraphs(): ...          # locate anchors
dr.replace(3, "Three", "Four", context="concern. Three Phase")
dr.comment_reply("52", "…")
dr.comment_on(11, "G3 anemia", "…", context="lower risk of G3 anemia")
dr.save("OUT.docx")
print(DocxReview("OUT.docx").validate("IN.docx"))   # [] means clean
```

`report_paragraphs()`, `report_comments()`, and `render(mode)` are the read APIs; `replace`, `delete`,
`insert_after`, `insert_before`, `comment_reply`, `comment_on` are the write APIs. `date` should be an ISO
`YYYY-MM-DDThh:mm:ssZ` string, chosen later than the author's edits so the thread ordering reads right.
