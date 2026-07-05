# XML patterns — inserting narrative into an existing CQ document

These are copy-paste building blocks for editing `unpacked/word/document.xml`. The CQ documents use **Arial 11 pt** body text (`<w:sz w:val="22"/>`), a bold heading style for "Clinical Question N" and "Literature Review", and SoF tables you must leave untouched. Insert narrative by **targeted `str_replace`** — do not rewrite the file.

## Command sequence

```bash
# 1. See current content
pandoc <file>.docx -o current.md

# 2. Unpack
python /mnt/skills/public/docx/scripts/office/unpack.py <file>.docx unpacked/

# 3. Edit unpacked/word/document.xml with str_replace (patterns below)

# 4. Repack + validate
python /mnt/skills/public/docx/scripts/office/pack.py unpacked/ <file>_final.docx --original <file>.docx

# 5. Verify
pandoc <file>_final.docx -o check.md   # read it back
```

## Where to insert

The opening summary + numbered subsections go **between** the "Literature Review" heading paragraph and the **first** table subtitle.

**Anchor the narrative insertion on the "Literature Review" heading paragraph plus the single blank paragraph that follows it — and nothing else.** Replace that anchor with: the heading paragraph + a blank + your narrative paragraphs. This keeps the insertion entirely *above* the first subtitle.

**Do not let the narrative edit's `old_str` include the first subtitle paragraph.** A tempting shortcut is to anchor on `[blank + first subtitle]` and rewrite it — but if the `new_str` then forgets to re-add that subtitle, the subtitle is silently deleted, and any later block reorder will misgroup on the now-blank "subtitle." Keep the two concerns separate: **(1)** insert narrative above the first subtitle, then **(2)** reformat each subtitle in its own edit. The two steps never share an anchor.

For documents with several tables, after the narrative is in, convert each table's bold subtitle to italic+underline in place (one edit per subtitle), and insert the dagger footnote immediately after each `</w:tbl>`.

### Reordering comparison blocks (multi-comparison CQs)

When the comparisons must be reordered (lead with significant, then high→moderate→low certainty) and the document's tables are **not** already in that order, do not hand-move large tables — it corrupts easily. Instead:

1. Insert all narrative first, in the **final intended order** (the opening sentence and the numbered subsections written as 22.1, 22.2, … in sorted order). This narrative sits in the prefix, above the first table, so reordering tables underneath it does not disturb it.
2. Run the helper to move the table blocks into the same order:
   ```bash
   python <skill>/scripts/reorder_comparison_blocks.py unpacked/word/document.xml <permutation>
   ```
   `<permutation>` is the comma-separated list of **original** 0-based block indices in their new order. A block = the subtitle paragraph + its table + trailing footnotes up to the next subtitle. Example: tables physically in order [Ribociclib, Palbociclib, Abemaciclib] that should become [Abemaciclib, Ribociclib, Palbociclib] → permutation `2,0,1`. The script aborts (exit 2) if any table's preceding paragraph is empty — that is the missing-subtitle signal; restore the subtitle and rerun.
3. After reordering, walk the now-ordered subtitles top-to-bottom and reformat + renumber them 1,2,3,… (italic+underline, with the `X.Y` prefix), then add the dagger footnote after each table.

If there are only two or three small comparisons and you prefer not to script it, you may reorder by hand — but verify with pandoc afterward that every subtitle still sits directly above its own table.

### Inserting the dagger footnote when several tables are identical

`str_replace` on `</w:tbl>` alone is not unique across multiple tables. Either include the *following* distinctive content (the next subtitle's text) in the anchor, or insert programmatically — append a dagger-footnote paragraph immediately after each `<w:tbl>` element:

```python
from lxml import etree
W="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
qn=lambda t:f"{{{W}}}{t}"
tree=etree.parse("unpacked/word/document.xml"); body=tree.getroot().find(qn("body"))
dagger='<w:p xmlns:w="%s" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"><w:r><w:rPr><w:rFonts w:ascii="Arial" w:cs="Arial" w:eastAsia="Arial" w:hAnsi="Arial"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr><w:t xml:space="preserve">\u2020 Calculated using event rate in the control/comparator arm.</w:t></w:r></w:p>' % W
for t in [e for e in body if e.tag==qn("tbl")]:
    t.addnext(etree.fromstring(dagger))
tree.write("unpacked/word/document.xml", xml_declaration=True, encoding="UTF-8", standalone=True)
```

Match the footnote size (`w:sz`) to the document's existing footnotes (18 = 9 pt or 20 = 10 pt).

## Body paragraph (normal narrative text)

```xml
<w:p w14:paraId="0C98CB10" w14:textId="77777701" w:rsidR="003128DD" w:rsidRDefault="003128DD" w:rsidP="004A4A1A">
  <w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
      <w:sz w:val="22"/>
      <w:szCs w:val="22"/>
    </w:rPr>
  </w:pPr>
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
      <w:sz w:val="22"/>
      <w:szCs w:val="22"/>
    </w:rPr>
    <w:t xml:space="preserve">PARAGRAPH TEXT HERE</w:t>
  </w:r>
</w:p>
```

- Use a **unique** `w14:paraId` / `w14:textId` for every new paragraph (any 8-hex-digit value not already in the file). Increment them so they stay unique.
- Use `xml:space="preserve"` whenever the text has meaningful leading/trailing spaces; harmless to include always.
- For an **empty spacer paragraph** between blocks, drop the `<w:r>…</w:r>` and keep just the `<w:pPr>` (same as the blank paragraphs already in the document). Put one spacer between the opening sentence and the first numbered item, and one between consecutive numbered items, to match the spacing of CQ16/CQ19.

### Escaping inside `<w:t>`

- `&` → `&amp;` , `<` → `&lt;` , `>` → `&gt;`
- Square brackets `[` `]`, parentheses, %, and the word "to" are literal — no escaping needed.
- For smart apostrophes/quotes use entities: `&#x2019;` (’), `&#x201C;` (“), `&#x201D;` (”). Plain ASCII quotes are fine too if the document already uses them.

## Italic + underline table subtitle

Replace the existing **bold** subtitle run properties with italic + underline, and prefix the number. The whole paragraph:

```xml
<w:p w14:paraId="0C98CB20" w14:textId="77777720" w:rsidR="000126EF" w:rsidRDefault="000126EF" w:rsidP="004A4A1A">
  <w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
      <w:i/>
      <w:iCs/>
      <w:sz w:val="22"/>
      <w:szCs w:val="22"/>
      <w:u w:val="single"/>
    </w:rPr>
  </w:pPr>
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
      <w:i/>
      <w:iCs/>
      <w:sz w:val="22"/>
      <w:szCs w:val="22"/>
      <w:u w:val="single"/>
    </w:rPr>
    <w:t>19.2 Denosumab versus Placebo (Premenopausal)</w:t>
  </w:r>
</w:p>
```

The difference from the bold input is: drop `<w:b/>`/`<w:bCs/>`, add `<w:i/>`/`<w:iCs/>` and `<w:u w:val="single"/>` in **both** the `<w:pPr><w:rPr>` and the run's `<w:rPr>`. Add the `X.Y ` number prefix to the text. Note element order inside `<w:rPr>`: fonts, then `<w:i/>`, `<w:iCs/>`, `<w:sz>`, `<w:szCs>`, then `<w:u>` last is acceptable; keep `<w:u>` after the size.

## Control-arm footnote (10 pt)

Insert immediately after a table's `</w:tbl>`, before any existing footnote paragraph. The dagger is a literal "†" via entity `&#x2020;`:

```xml
<w:p w14:paraId="0C98CB30" w14:textId="77777730" w:rsidR="00CC455A" w:rsidRDefault="00CC455A" w:rsidP="004A4A1A">
  <w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
      <w:sz w:val="20"/>
      <w:szCs w:val="20"/>
    </w:rPr>
  </w:pPr>
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
      <w:sz w:val="20"/>
      <w:szCs w:val="20"/>
    </w:rPr>
    <w:t xml:space="preserve">&#x2020; Calculated using event rate in the control/comparator arm.</w:t>
  </w:r>
</w:p>
```

The footnote font size here is 10 pt (`w:val="20"`). Some documents use 9 pt (`w:val="18"`) for footnotes (CQ19) — match whatever the document already uses for its existing footnotes so the two notes are consistent.

### Superscript marker (if a footnote uses a lettered/numbered marker)

For an existing certainty footnote like "ᵃ Very serious imprecision…", the marker is a superscript run:

```xml
<w:r>
  <w:rPr>
    <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
    <w:sz w:val="20"/>
    <w:szCs w:val="20"/>
    <w:vertAlign w:val="superscript"/>
  </w:rPr>
  <w:t>a</w:t>
</w:r>
```

Leave existing certainty footnotes in place. Only **add** the dagger footnote; never delete the imprecision/inconsistency note.

## Sanity checks after packing

- `pack.py` runs validation and auto-repairs `durableId` and missing `xml:space`. If it reports a schema error, re-open the XML and check element nesting and that every new `<w:p>` is well-formed.
- Read the repacked file with `pandoc … -o check.md` and confirm: (1) the opening sentence and every numbered item are present and correct, (2) the brackets/HRs match the tables, (3) the tables themselves are unchanged, (4) each table has the dagger footnote, (5) subtitles are italic+underline with the number prefix.
