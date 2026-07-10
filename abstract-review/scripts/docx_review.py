# -*- coding: utf-8 -*-
"""
docx_review.py — a reusable library for reviewing Word (.docx) documents with
real Word **tracked changes** (w:ins / w:del) and **threaded comments**, authored
under a named reviewer.

It is the engine behind the `abstract-review` skill. It is deliberately
document-agnostic: it does not know anything about myelofibrosis, NMAs, or any
particular research type. It only knows how to:

  * read a .docx and report its paragraphs (with run breakdown), existing
    tracked changes, and existing comments (including reply threads and
    resolved/`done` state);
  * render the document as clean text, or with all changes accepted / rejected,
    or with inline INS/DEL/comment markers;
  * apply tracked insertions / deletions / replacements anchored by *text*
    (not fragile run indices), each attributed to the reviewer;
  * add threaded **reply** comments to existing comments, and brand-new
    **anchored** comments on a chosen phrase;
  * repackage everything into a new .docx and self-validate (comment-range
    balance; "reject-all reproduces the original" invariant).

Design notes
------------
* Edits are text-anchored and land inside a *single plain run*. That is how Word
  usually stores a sentence, and it keeps us from ever nesting a tracked change
  inside another tracked change or splitting a comment range. If a target spans
  runs (e.g. it crosses an existing tracked change), the call raises a clear
  error — split it into smaller single-run targets, or move the anchor. Run the
  inspector first (`inspect_docx.py`) to see the run boundaries.
* Comment infrastructure (comments.xml + commentsExtended/Ids/Extensible +
  people.xml + the content-type / relationship registrations) is created on
  demand, so this works on documents that have no comments yet.
* No third-party deps beyond `lxml`.

CLI
---
    python docx_review.py inspect  IN.docx                 # paragraphs+runs, comments, tracked changes
    python docx_review.py render   IN.docx [clean|accept|reject|markup]
    python docx_review.py apply    PLAN.json               # apply an edit plan -> OUT.docx (+ validate)
    python docx_review.py validate REVIEWED.docx [ORIGINAL.docx]
"""

import copy
import json
import sys
import zipfile
from collections import Counter, OrderedDict

from lxml import etree

# ------------------------------------------------------------------ namespaces
NS = {
    'w':     'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'w14':   'http://schemas.microsoft.com/office/word/2010/wordml',
    'w15':   'http://schemas.microsoft.com/office/word/2012/wordml',
    'w16cid':'http://schemas.microsoft.com/office/word/2016/wordml/cid',
    'w16cex':'http://schemas.microsoft.com/office/word/2018/wordml/cex',
    'ct':    'http://schemas.openxmlformats.org/package/2006/content-types',
    'rel':   'http://schemas.openxmlformats.org/package/2006/relationships',
    'xml':   'http://www.w3.org/XML/1998/namespace',
}
def q(pfx, tag):
    return '{%s}%s' % (NS[pfx], tag)
def wq(tag):
    return q('w', tag)

# content-type + relationship metadata for the optional comment parts
_COMMENT_PARTS = {
    'comments': dict(
        part='word/comments.xml',
        ctype='application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml',
        rtype='http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments',
        root='w:comments'),
    'commentsExtended': dict(
        part='word/commentsExtended.xml',
        ctype='application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtended+xml',
        rtype='http://schemas.microsoft.com/office/2011/relationships/commentsExtended',
        root='w15:commentsEx'),
    'commentsIds': dict(
        part='word/commentsIds.xml',
        ctype='application/vnd.openxmlformats-officedocument.wordprocessingml.commentsIds+xml',
        rtype='http://schemas.microsoft.com/office/2016/09/relationships/commentsIds',
        root='w16cid:commentsIds'),
    'commentsExtensible': dict(
        part='word/commentsExtensible.xml',
        ctype='application/vnd.openxmlformats-officedocument.wordprocessingml.commentsExtensible+xml',
        rtype='http://schemas.microsoft.com/office/2018/08/relationships/commentsExtensible',
        root='w16cex:commentsExtensible'),
    'people': dict(
        part='word/people.xml',
        ctype='application/vnd.openxmlformats-officedocument.wordprocessingml.people+xml',
        rtype='http://schemas.microsoft.com/office/2011/relationships/people',
        root='w15:people'),
}

# namespace decls we want on freshly-created part roots
_ROOT_NSDECL = {
    'w15:commentsEx':          {'w15': NS['w15'], 'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'},
    'w16cid:commentsIds':      {'w16cid': NS['w16cid'], 'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'},
    'w16cex:commentsExtensible':{'w16cex': NS['w16cex'], 'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'},
    'w15:people':              {'w15': NS['w15'], 'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'},
    'w:comments':              {'w': NS['w'], 'w14': NS['w14'], 'w15': NS['w15'],
                                'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006'},
}


class ReviewError(Exception):
    pass


class DocxReview:
    """Load a .docx, report/edit it, save a reviewed copy."""

    def __init__(self, path, reviewer='Muhammad Ali Khan', date='2026-01-01T00:00:00Z',
                 initials=None):
        self.path = path
        self.reviewer = reviewer
        self.date = date
        self.initials = initials or ''.join(w[0] for w in reviewer.split()[:3]).upper()
        self._parts = OrderedDict()          # name -> bytes (verbatim)
        self._trees = {}                     # name -> parsed ElementTree (for parts we touch)
        self._track_id = 900_000            # high base to avoid colliding with existing ids
        self._load()

    # ---------------------------------------------------------------- load/save
    def _load(self):
        with zipfile.ZipFile(self.path) as z:
            for info in z.infolist():
                self._parts[info.filename] = z.read(info.filename)
        self._doc = self._tree('word/document.xml')
        self._body = self._doc.getroot().find(wq('body'))

    def _tree(self, name):
        if name not in self._trees:
            if name not in self._parts:
                raise ReviewError('missing part: %s' % name)
            self._trees[name] = etree.fromstring(self._parts[name]).getroottree()
        return self._trees[name]

    def save(self, out_path):
        # serialize any parsed trees back into the byte map
        for name, tree in self._trees.items():
            self._parts[name] = etree.tostring(
                tree, xml_declaration=True, encoding='UTF-8', standalone=True)
        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, data in self._parts.items():
                z.writestr(name, data)

    # ---------------------------------------------------------------- helpers
    @property
    def paragraphs(self):
        return self._body.findall(wq('p'))

    @staticmethod
    def run_text(el):
        return ''.join((t.text or '') for t in el.iter(wq('t')))

    @staticmethod
    def para_text(p):
        """Full visible text of a paragraph (accepting insertions, keeping normal text,
        excluding deletions' delText)."""
        out = []
        def rec(node, deleted=False):
            for ch in node:
                if ch.tag == wq('del'):
                    rec(ch, True)
                elif ch.tag == wq('ins'):
                    rec(ch, deleted)
                elif ch.tag == wq('r'):
                    if not deleted:
                        out.append(''.join((t.text or '') for t in ch.iter(wq('t'))))
                else:
                    rec(ch, deleted)
        rec(p)
        return ''.join(out)

    def _next_track_id(self):
        self._track_id += 1
        return str(self._track_id)

    def _make_run(self, rpr, text, deltext=False):
        r = etree.Element(wq('r'))
        if rpr is not None:
            r.append(copy.deepcopy(rpr))
        t = etree.SubElement(r, wq('delText') if deltext else wq('t'))
        t.set(q('xml', 'space'), 'preserve')
        t.text = text
        return r

    def _wrap(self, tag, rpr, text):
        el = etree.Element(wq(tag))
        el.set(wq('id'), self._next_track_id())
        el.set(wq('author'), self.reviewer)
        el.set(wq('date'), self.date)
        el.append(self._make_run(rpr, text, deltext=(tag == 'del')))
        return el

    # ---------------------------------------------------------------- reporting
    def report_paragraphs(self):
        rep = []
        for i, p in enumerate(self.paragraphs):
            runs = []
            for j, ch in enumerate(p):
                tag = ch.tag.split('}')[1]
                if tag == 'r':
                    runs.append({'i': j, 'kind': 'run', 'text': self.run_text(ch)})
                elif tag in ('ins', 'del'):
                    runs.append({'i': j, 'kind': tag, 'text': self.run_text(ch)})
                elif tag in ('commentRangeStart', 'commentRangeEnd'):
                    runs.append({'i': j, 'kind': tag, 'id': ch.get(wq('id'))})
            rep.append({'index': i, 'text': self.para_text(p), 'runs': runs})
        return rep

    def report_comments(self):
        if 'word/comments.xml' not in self._parts:
            return []
        croot = self._tree('word/comments.xml').getroot()
        # threading map from commentsExtended
        parent_of = {}
        done_of = {}
        if 'word/commentsExtended.xml' in self._parts:
            for ex in self._tree('word/commentsExtended.xml').getroot():
                pid = ex.get(q('w15', 'paraId'))
                parent_of[pid] = ex.get(q('w15', 'paraIdParent'))
                done_of[pid] = ex.get(q('w15', 'done'))
        pid2cid = {}
        for c in croot:
            for pp in c.findall(wq('p')):
                pid2cid[pp.get(q('w14', 'paraId'))] = c.get(wq('id'))
        out = []
        for c in croot:
            cid = c.get(wq('id'))
            first_pid = c.find(wq('p')).get(q('w14', 'paraId')) if c.find(wq('p')) is not None else None
            parent_pid = None
            done = '0'
            for pp in c.findall(wq('p')):
                pid = pp.get(q('w14', 'paraId'))
                if parent_of.get(pid):
                    parent_pid = parent_of[pid]
                if done_of.get(pid) == '1':
                    done = '1'
            out.append({
                'id': cid,
                'author': c.get(wq('author')),
                'date': c.get(wq('date')),
                'reply_to': pid2cid.get(parent_pid) if parent_pid else None,
                'resolved': done == '1',
                'text': '\n'.join(''.join(t.text or '' for t in pp.iter(wq('t')))
                                  for pp in c.findall(wq('p'))).strip(),
            })
        return out

    def render(self, mode='clean'):
        """mode: clean | accept | reject | markup"""
        lines = []
        for p in self.paragraphs:
            if mode == 'markup':
                lines.append(self._markup_line(p))
            else:
                lines.append(self._plain_line(p, mode))
        return '\n'.join(lines)

    def _plain_line(self, p, mode):
        out = []
        def rec(node, ins=False, dele=False):
            for ch in node:
                if ch.tag == wq('ins'):
                    rec(ch, True, dele)
                elif ch.tag == wq('del'):
                    rec(ch, ins, True)
                elif ch.tag == wq('r'):
                    txt = ''.join((t.text or '') for t in ch.iter(wq('t')))
                    txt += ''.join((t.text or '') for t in ch.iter(wq('delText')))
                    if not txt:
                        continue
                    if mode == 'accept' and dele:
                        continue
                    if mode == 'reject' and ins:
                        continue
                    if mode == 'clean' and (ins or dele):
                        # clean = accept insertions, drop deletions
                        if dele:
                            continue
                    out.append(txt)
                else:
                    rec(ch, ins, dele)
        rec(p)
        return ''.join(out)

    def _markup_line(self, p):
        out = []
        def rec(node, ins=False, dele=False):
            for ch in node:
                if ch.tag == wq('ins'):
                    rec(ch, True, dele)
                elif ch.tag == wq('del'):
                    rec(ch, ins, True)
                elif ch.tag == wq('r'):
                    txt = ''.join((t.text or '') for t in ch.iter(wq('t')))
                    txt += ''.join((t.text or '') for t in ch.iter(wq('delText')))
                    if not txt:
                        continue
                    if dele:
                        out.append('[DEL:%s]' % txt)
                    elif ins:
                        out.append('[INS:%s]' % txt)
                    else:
                        out.append(txt)
                elif ch.tag == wq('commentRangeStart'):
                    out.append('{{C%s>' % ch.get(wq('id')))
                elif ch.tag == wq('commentRangeEnd'):
                    out.append('<C%s}}' % ch.get(wq('id')))
                else:
                    rec(ch, ins, dele)
        rec(p)
        return ''.join(out)

    # ---------------------------------------------------------------- run finding
    def _find_run(self, para_index, needle, context=None, occurrence=1):
        """Return the direct-child <w:r> of paragraph `para_index` that contains
        `needle` (optionally also `context`). Errors if the needle is not fully
        inside one plain run."""
        try:
            p = self.paragraphs[para_index]
        except IndexError:
            raise ReviewError('paragraph index %r out of range (0..%d)'
                              % (para_index, len(self.paragraphs) - 1))
        hits = []
        for ch in p:
            if ch.tag != wq('r'):
                continue
            txt = self.run_text(ch)
            if needle in txt and (context is None or context in txt):
                hits.append((ch, txt))
        if not hits:
            # diagnose: is the needle present at all (spanning runs)?
            whole = self.para_text(p)
            if needle in whole:
                raise ReviewError(
                    'target %r spans multiple runs / a tracked change in paragraph %d; '
                    'choose a smaller target that lies within one run (run inspect to see '
                    'run boundaries).' % (needle, para_index))
            raise ReviewError('target %r not found in paragraph %d.\nParagraph text: %r'
                              % (needle, para_index, whole))
        if len(hits) < occurrence:
            raise ReviewError('only %d occurrence(s) of %r in paragraph %d (asked for #%d); '
                              'add a `context` to disambiguate.'
                              % (len(hits), needle, para_index, occurrence))
        return hits[occurrence - 1][0]

    def _splice(self, run_el, segments):
        """Replace run_el with keep/ins/del segments; keep+del must reconstruct the run."""
        recon = ''.join(t for k, t in segments if k in ('keep', 'del'))
        assert recon == self.run_text(run_el), \
            'internal splice mismatch: %r vs %r' % (recon, self.run_text(run_el))
        parent = run_el.getparent()
        idx = list(parent).index(run_el)
        rpr = run_el.find(wq('rPr'))
        new_els = []
        for kind, text in segments:
            if kind == 'keep':
                new_els.append(self._make_run(rpr, text))
            elif kind == 'ins':
                new_els.append(self._wrap('ins', rpr, text))
            elif kind == 'del':
                new_els.append(self._wrap('del', rpr, text))
        parent.remove(run_el)
        for off, el in enumerate(new_els):
            parent.insert(idx + off, el)

    @staticmethod
    def _split3(text, needle, context=None):
        pos = text.find(needle)
        return text[:pos], needle, text[pos + len(needle):]

    # ---------------------------------------------------------------- tracked edits
    def replace(self, paragraph, find, replace, context=None, occurrence=1):
        run = self._find_run(paragraph, find, context, occurrence)
        before, mid, after = self._split3(self.run_text(run), find)
        segs = []
        if before:
            segs.append(('keep', before))
        segs.append(('del', mid))
        if replace:
            segs.append(('ins', replace))
        if after:
            segs.append(('keep', after))
        self._splice(run, segs)

    def delete(self, paragraph, find, context=None, occurrence=1):
        self.replace(paragraph, find, '', context, occurrence)

    def insert_after(self, paragraph, anchor, text, context=None, occurrence=1):
        run = self._find_run(paragraph, anchor, context, occurrence)
        before, mid, after = self._split3(self.run_text(run), anchor)
        segs = []
        keep_head = before + mid
        if keep_head:
            segs.append(('keep', keep_head))
        segs.append(('ins', text))
        if after:
            segs.append(('keep', after))
        self._splice(run, segs)

    def insert_before(self, paragraph, anchor, text, context=None, occurrence=1):
        run = self._find_run(paragraph, anchor, context, occurrence)
        before, mid, after = self._split3(self.run_text(run), anchor)
        segs = []
        if before:
            segs.append(('keep', before))
        segs.append(('ins', text))
        segs.append(('keep', mid + after))
        self._splice(run, segs)

    # ---------------------------------------------------------------- comment infra
    def _ensure_comment_parts(self):
        """Create comments.xml (+ Extended/Ids/Extensible/people) and register them
        in [Content_Types].xml and word/_rels/document.xml.rels if absent."""
        # content types
        ct_tree = self._tree('[Content_Types].xml')
        ct_root = ct_tree.getroot()
        existing_overrides = {o.get('PartName') for o in ct_root
                              if o.tag == q('ct', 'Override')}
        # relationships
        rels_name = 'word/_rels/document.xml.rels'
        rels_tree = self._tree(rels_name)
        rels_root = rels_tree.getroot()
        existing_rel_targets = {r.get('Target') for r in rels_root}
        rid_nums = [int(r.get('Id')[3:]) for r in rels_root
                    if r.get('Id', '').startswith('rId') and r.get('Id')[3:].isdigit()]
        next_rid = max(rid_nums) + 1 if rid_nums else 1

        for key, meta in _COMMENT_PARTS.items():
            part = meta['part']
            if part not in self._parts:
                root = etree.Element(q(*meta['root'].split(':')),
                                     nsmap=_ROOT_NSDECL.get(meta['root'], None))
                # mc:Ignorable to match Word output (harmless if extra)
                self._parts[part] = etree.tostring(
                    root, xml_declaration=True, encoding='UTF-8', standalone=True)
                self._trees.pop(part, None)
            # content type override
            pn = '/' + part
            if pn not in existing_overrides:
                ov = etree.SubElement(ct_root, q('ct', 'Override'))
                ov.set('PartName', pn)
                ov.set('ContentType', meta['ctype'])
                existing_overrides.add(pn)
            # relationship
            target = part.split('word/', 1)[1] if part.startswith('word/') else part
            if target not in existing_rel_targets:
                rel = etree.SubElement(rels_root, q('rel', 'Relationship'))
                rel.set('Id', 'rId%d' % next_rid); next_rid += 1
                rel.set('Type', meta['rtype'])
                rel.set('Target', target)
                existing_rel_targets.add(target)

    # unique paraId / durableId
    def _existing_ids(self):
        paraids, durids, cids = set(), set(), set()
        if 'word/comments.xml' in self._parts:
            for c in self._tree('word/comments.xml').getroot():
                cids.add(int(c.get(wq('id'))))
                for pp in c.findall(wq('p')):
                    pid = pp.get(q('w14', 'paraId'))
                    if pid:
                        paraids.add(pid)
        if 'word/commentsIds.xml' in self._parts:
            for e in self._tree('word/commentsIds.xml').getroot():
                durids.add(e.get(q('w16cid', 'durableId')))
        return paraids, durids, (max(cids) if cids else -1)

    def _mint_ids(self, n):
        paraids, durids, maxcid = self._existing_ids()
        out = []
        pc, dc = 0, 0
        cid = maxcid
        for _ in range(n):
            cid += 1
            while True:
                pc += 1
                pid = '7EDA%04X' % pc
                if pid not in paraids:
                    paraids.add(pid); break
            while True:
                dc += 1
                did = '7EDA%04X' % (0x2000 + dc)
                if did not in durids:
                    durids.add(did); break
            out.append((str(cid), pid, did))
        return out

    def _add_comment_body(self, cid, paraid, text):
        croot = self._tree('word/comments.xml').getroot()
        c = etree.SubElement(croot, wq('comment'))
        c.set(wq('id'), cid); c.set(wq('author'), self.reviewer)
        c.set(wq('date'), self.date); c.set(wq('initials'), self.initials)
        p = etree.SubElement(c, wq('p'))
        p.set(q('w14', 'paraId'), paraid); p.set(q('w14', 'textId'), '77777777')
        r1 = etree.SubElement(p, wq('r'))
        rpr1 = etree.SubElement(r1, wq('rPr'))
        etree.SubElement(rpr1, wq('rStyle')).set(wq('val'), 'CommentReference')
        etree.SubElement(r1, wq('annotationRef'))
        r2 = etree.SubElement(p, wq('r'))
        rpr2 = etree.SubElement(r2, wq('rPr'))
        etree.SubElement(rpr2, wq('sz')).set(wq('val'), '20')
        etree.SubElement(rpr2, wq('szCs')).set(wq('val'), '20')
        t = etree.SubElement(r2, wq('t')); t.set(q('xml', 'space'), 'preserve'); t.text = text

    def _add_ext(self, paraid, parent_paraid, done='0'):
        root = self._tree('word/commentsExtended.xml').getroot()
        ex = etree.SubElement(root, q('w15', 'commentEx'))
        ex.set(q('w15', 'paraId'), paraid)
        if parent_paraid:
            ex.set(q('w15', 'paraIdParent'), parent_paraid)
        ex.set(q('w15', 'done'), done)

    def _add_cid(self, paraid, durid):
        root = self._tree('word/commentsIds.xml').getroot()
        e = etree.SubElement(root, q('w16cid', 'commentId'))
        e.set(q('w16cid', 'paraId'), paraid); e.set(q('w16cid', 'durableId'), durid)

    def _add_cexs(self, durid):
        root = self._tree('word/commentsExtensible.xml').getroot()
        e = etree.SubElement(root, q('w16cex', 'commentExtensible'))
        e.set(q('w16cex', 'durableId'), durid); e.set(q('w16cex', 'dateUtc'), self.date)

    def _ensure_person(self):
        root = self._tree('word/people.xml').getroot()
        if any(p.get(q('w15', 'author')) == self.reviewer for p in root):
            return
        person = etree.SubElement(root, q('w15', 'person'))
        person.set(q('w15', 'author'), self.reviewer)
        pi = etree.SubElement(person, q('w15', 'presenceInfo'))
        pi.set(q('w15', 'providerId'), 'None'); pi.set(q('w15', 'userId'), self.reviewer)

    def _ref_run(self, cid):
        r = etree.Element(wq('r'))
        rpr = etree.SubElement(r, wq('rPr'))
        etree.SubElement(rpr, wq('rStyle')).set(wq('val'), 'CommentReference')
        etree.SubElement(r, wq('commentReference')).set(wq('id'), cid)
        return r

    def _parent_paraid(self, parent_cid):
        for c in self._tree('word/comments.xml').getroot():
            if c.get(wq('id')) == str(parent_cid):
                return c.find(wq('p')).get(q('w14', 'paraId'))
        raise ReviewError('parent comment id %r not found' % parent_cid)

    # ---------------------------------------------------------------- comment ops
    def comment_reply(self, parent, text):
        """Add a threaded reply to an existing comment id, nested on its range."""
        self._ensure_comment_parts()
        parent = str(parent)
        parent_pid = self._parent_paraid(parent)
        (cid, pid, did), = self._mint_ids(1)
        self._add_comment_body(cid, pid, text)
        self._add_ext(pid, parent_pid, '0')
        self._add_cid(pid, did)
        self._add_cexs(did)
        self._ensure_person()
        # anchor: nest on parent's range in document.xml
        docroot = self._doc.getroot()
        crs = next((e for e in docroot.iter(wq('commentRangeStart'))
                    if e.get(wq('id')) == parent), None)
        ref = next((e for e in docroot.iter(wq('commentReference'))
                    if e.get(wq('id')) == parent), None)
        if crs is None or ref is None:
            raise ReviewError('anchors for parent comment %r not found in document' % parent)
        p1 = crs.getparent(); i1 = list(p1).index(crs)
        new_crs = etree.Element(wq('commentRangeStart')); new_crs.set(wq('id'), cid)
        p1.insert(i1 + 1, new_crs)
        ref_run = ref.getparent()
        p2 = ref_run.getparent(); i2 = list(p2).index(ref_run)
        new_cre = etree.Element(wq('commentRangeEnd')); new_cre.set(wq('id'), cid)
        p2.insert(i2 + 1, new_cre)
        p2.insert(i2 + 2, self._ref_run(cid))
        return cid

    def comment_on(self, paragraph, target, text, context=None, occurrence=1):
        """Add a brand-new anchored comment on `target` within a paragraph."""
        self._ensure_comment_parts()
        (cid, pid, did), = self._mint_ids(1)
        self._add_comment_body(cid, pid, text)
        self._add_ext(pid, None, '0')
        self._add_cid(pid, did)
        self._add_cexs(did)
        self._ensure_person()
        run = self._find_run(paragraph, target, context, occurrence)
        before, mid, after = self._split3(self.run_text(run), target)
        rpr = run.find(wq('rPr'))
        parent = run.getparent(); idx = list(parent).index(run)
        seq = []
        if before:
            seq.append(self._make_run(rpr, before))
        crs = etree.Element(wq('commentRangeStart')); crs.set(wq('id'), cid); seq.append(crs)
        seq.append(self._make_run(rpr, mid))
        cre = etree.Element(wq('commentRangeEnd')); cre.set(wq('id'), cid); seq.append(cre)
        seq.append(self._ref_run(cid))
        if after:
            seq.append(self._make_run(rpr, after))
        parent.remove(run)
        for off, el in enumerate(seq):
            parent.insert(idx + off, el)
        return cid

    # ---------------------------------------------------------------- validation
    def validate(self, original_path=None):
        problems = []
        # comment-range balance
        s, e, r = Counter(), Counter(), Counter()
        for el in self._doc.getroot().iter():
            if el.tag == wq('commentRangeStart'): s[el.get(wq('id'))] += 1
            elif el.tag == wq('commentRangeEnd'): e[el.get(wq('id'))] += 1
            elif el.tag == wq('commentReference'): r[el.get(wq('id'))] += 1
        defined = set()
        if 'word/comments.xml' in self._parts:
            defined = {c.get(wq('id')) for c in self._tree('word/comments.xml').getroot()}
        for cid in (set(s) | set(e) | set(r) | defined):
            if not (s[cid] == e[cid] == r[cid] == 1 and cid in defined):
                problems.append('comment %s unbalanced: start=%d end=%d ref=%d defined=%s'
                                % (cid, s[cid], e[cid], r[cid], cid in defined))
        # reject-all invariant vs original
        if original_path:
            orig = DocxReview(original_path)
            if self.render('reject') != orig.render('accept'):
                # note: original may itself contain tracked changes; compare reject-view to
                # the original's own current-view
                if self.render('reject') != orig.render('reject'):
                    problems.append('reject-all view does not reproduce the original document '
                                    '(unexpected collateral change)')
        return problems


# ------------------------------------------------------------------ edit plan
def apply_plan(plan):
    """plan = dict with keys: input, output, reviewer, date, edits[].
    Each edit is a dict with 'type' in {replace,delete,insert_after,insert_before,
    comment_reply,comment_on} plus its args. Returns (DocxReview, problems)."""
    dr = DocxReview(plan['input'],
                    reviewer=plan.get('reviewer', 'Muhammad Ali Khan'),
                    date=plan.get('date', '2026-01-01T00:00:00Z'),
                    initials=plan.get('initials'))
    for k, ed in enumerate(plan['edits']):
        t = ed['type']
        try:
            if t == 'replace':
                dr.replace(ed['paragraph'], ed['find'], ed['replace'],
                           ed.get('context'), ed.get('occurrence', 1))
            elif t == 'delete':
                dr.delete(ed['paragraph'], ed['find'], ed.get('context'), ed.get('occurrence', 1))
            elif t == 'insert_after':
                dr.insert_after(ed['paragraph'], ed['anchor'], ed['text'],
                                ed.get('context'), ed.get('occurrence', 1))
            elif t == 'insert_before':
                dr.insert_before(ed['paragraph'], ed['anchor'], ed['text'],
                                 ed.get('context'), ed.get('occurrence', 1))
            elif t == 'comment_reply':
                dr.comment_reply(ed['parent'], ed['text'])
            elif t == 'comment_on':
                dr.comment_on(ed['paragraph'], ed['target'], ed['text'],
                              ed.get('context'), ed.get('occurrence', 1))
            else:
                raise ReviewError('unknown edit type %r' % t)
        except Exception as exc:
            raise ReviewError('edit #%d (%s) failed: %s' % (k, t, exc))
    dr.save(plan['output'])
    problems = DocxReview(plan['output']).validate(plan['input'])
    return dr, problems


# ------------------------------------------------------------------ CLI
def _cli():
    if len(sys.argv) < 2:
        print(__doc__); return 1
    cmd = sys.argv[1]
    if cmd == 'inspect':
        dr = DocxReview(sys.argv[2])
        print('=== PARAGRAPHS (index | text) ===')
        for p in dr.report_paragraphs():
            if not p['text'].strip() and not p['runs']:
                continue
            print('P%-3d %s' % (p['index'], p['text'][:160]))
        print('\n=== RUN BREAKDOWN (only paragraphs with tracked changes / comments) ===')
        for p in dr.report_paragraphs():
            if any(r['kind'] != 'run' for r in p['runs']):
                print('P%d:' % p['index'])
                for r in p['runs']:
                    if r['kind'] == 'run':
                        print('   [%d] run   %r' % (r['i'], r['text'][:90]))
                    elif r['kind'] in ('ins', 'del'):
                        print('   [%d] %-3s   %r' % (r['i'], r['kind'], r['text'][:90]))
                    else:
                        print('   [%d] %s id=%s' % (r['i'], r['kind'], r.get('id')))
        print('\n=== EXISTING COMMENTS ===')
        for c in dr.report_comments():
            tag = ('reply->%s' % c['reply_to']) if c['reply_to'] else 'root'
            res = ' [RESOLVED]' if c['resolved'] else ''
            print('C%s %s (%s)%s\n   %s\n' % (c['id'], c['author'], tag, res, c['text'][:400]))
        return 0
    if cmd == 'render':
        mode = sys.argv[3] if len(sys.argv) > 3 else 'clean'
        print(DocxReview(sys.argv[2]).render(mode)); return 0
    if cmd == 'apply':
        plan = json.load(open(sys.argv[2]))
        dr, problems = apply_plan(plan)
        print('Applied %d edits -> %s' % (len(plan['edits']), plan['output']))
        if problems:
            print('VALIDATION PROBLEMS:'); [print('  -', p) for p in problems]; return 2
        print('Validation: OK (comment ranges balanced; reject-all reproduces original)')
        return 0
    if cmd == 'validate':
        orig = sys.argv[3] if len(sys.argv) > 3 else None
        problems = DocxReview(sys.argv[2]).validate(orig)
        if problems:
            print('PROBLEMS:'); [print('  -', p) for p in problems]; return 2
        print('OK'); return 0
    print('unknown command: %s' % cmd); return 1


if __name__ == '__main__':
    sys.exit(_cli())
