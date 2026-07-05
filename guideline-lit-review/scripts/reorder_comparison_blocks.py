#!/usr/bin/env python3
"""
reorder_comparison_blocks.py — reorder the comparison blocks (subtitle + SoF
table + trailing footnotes) inside an unpacked guideline CQ document.xml.

The MODEL decides the order (the clinical judgment: significant-first, then by
certainty). This script does only the mechanical move so large tables are not
corrupted by hand-editing.

A "comparison block" is defined as: the subtitle paragraph immediately preceding
a <w:tbl>, that table, and every paragraph after it up to (but not including) the
next subtitle paragraph — so any footnote paragraphs travel with their table.

Usage:
  python reorder_comparison_blocks.py <document.xml> <permutation>

  <permutation> is a comma-separated list of 0-based ORIGINAL block indices in
  the desired new order. Example: a document whose tables are physically ordered
  [Ribociclib, Palbociclib, Abemaciclib] (indices 0,1,2) that should become
  [Abemaciclib, Ribociclib, Palbociclib] uses permutation "2,0,1".

The file is rewritten in place. Run pack.py afterward to validate, then read the
result back with pandoc to confirm. This script does NOT renumber subtitles or
add footnotes — do those with targeted edits after reordering (numbers must run
top-to-bottom 1,2,3,… in the final physical order).
"""
import sys
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
def qn(tag): return f"{{{W}}}{tag}"

def is_table(el): return el.tag == qn("tbl")
def is_para(el):  return el.tag == qn("p")
def is_sectpr(el):return el.tag == qn("sectPr")

def main():
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    path = sys.argv[1]
    perm = [int(x) for x in sys.argv[2].split(",")]

    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(path, parser)
    root = tree.getroot()
    body = root.find(qn("body"))
    if body is None:
        print("No <w:body> found"); sys.exit(1)

    children = list(body)
    # positions of tables in the flat child list
    tbl_pos = [i for i, el in enumerate(children) if is_table(el)]
    if len(tbl_pos) < 2:
        print(f"Found {len(tbl_pos)} table(s); need >=2 to reorder. Nothing to do.")
        sys.exit(0)

    # subtitle index for each table = the paragraph immediately preceding it
    def para_text(el):
        return "".join(t.text or "" for t in el.iter(qn("t"))).strip()
    subtitle_idx = []
    for tp in tbl_pos:
        j = tp - 1
        if j < 0 or not is_para(children[j]):
            print(f"Table at child {tp} has no preceding subtitle paragraph; aborting.")
            sys.exit(1)
        if not para_text(children[j]):
            # An empty paragraph directly above a table almost always means the
            # subtitle was accidentally deleted (e.g., a narrative-insertion edit
            # consumed it). Reordering on a blank "subtitle" silently misgroups.
            print(f"ERROR: the paragraph directly above the table at child {tp} is "
                  f"EMPTY — its subtitle appears to be missing. Restore the subtitle "
                  f"above every table before reordering. Aborting to avoid misgrouping.")
            sys.exit(2)
        subtitle_idx.append(j)

    # end of comparison region = first sectPr after last table, else len
    end_idx = len(children)
    for i in range(tbl_pos[-1], len(children)):
        if is_sectpr(children[i]):
            end_idx = i
            break

    # block k spans [subtitle_idx[k], subtitle_idx[k+1]) ; last to end_idx
    bounds = subtitle_idx + [end_idx]
    blocks = []
    for k in range(len(tbl_pos)):
        blocks.append(children[bounds[k]:bounds[k+1]])

    if sorted(perm) != list(range(len(blocks))):
        print(f"Permutation {perm} is not a valid ordering of {len(blocks)} blocks "
              f"(expected a rearrangement of 0..{len(blocks)-1}).")
        sys.exit(1)

    prefix = children[:bounds[0]]            # headings + opening narrative + blanks
    suffix = children[end_idx:]              # sectPr (and anything after)

    # detach all children, then re-append in the new order
    for el in children:
        body.remove(el)
    for el in prefix:
        body.append(el)
    for k in perm:
        for el in blocks[k]:
            body.append(el)
    for el in suffix:
        body.append(el)

    tree.write(path, xml_declaration=True, encoding="UTF-8", standalone=True)
    print(f"Reordered {len(blocks)} comparison blocks to order {perm}. "
          f"Renumber subtitles top-to-bottom and add footnotes next.")

if __name__ == "__main__":
    main()
