#!/usr/bin/env python3
"""Resolve LISR paper_id values to DOIs.

Input: lisr_metadata.json  (dict: id -> record from the LISR API, see SKILL.md Phase 1)
Output: resolved.json      (dict: id -> record + doi/pmid/nct/match_score/resolve_status)

paper_id_type handling:
  DOI    -> use paper_id directly
  OVID   -> PMID (resolve PMID->DOI via NCBI) unless it matches 'nct\\d' (trial registration)
  EMBASE -> Embase accession, no DOI; resolve by title via Crossref (title-similarity gated)

Usage:
  python resolve_identifiers.py --meta lisr_metadata.json --out resolved.json --email you@example.com
"""
import argparse, json, re, time, urllib.request, urllib.parse
from difflib import SequenceMatcher

def get(url, ua, timeout=25):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': ua}), timeout=timeout).read()

def norm(t):
    if not t: return ''
    t = re.sub(r'&[a-z]+;', ' ', t.lower())
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', t).split())

def sim(a, b):
    return round(SequenceMatcher(None, norm(a), norm(b)).ratio(), 3)

def year_of(s):
    m = re.search(r'(19|20)\d{2}', str(s or ''))
    return m.group(0) if m else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--meta', default='lisr_metadata.json')
    ap.add_argument('--out', default='resolved.json')
    ap.add_argument('--email', default='research@example.com', help='contact email for Crossref/NCBI polite pools')
    a = ap.parse_args()
    ua = f'SystematicReview/1.0 (mailto:{a.email})'

    meta = json.load(open(a.meta, encoding='utf-8'))
    records = list(meta.values())
    for r in records:
        pid = (r.get('paper_id') or '').strip(); t = r.get('paper_id_type')
        r['doi'] = r['pmid'] = r['nct'] = None
        r['matched_title'] = None; r['match_score'] = None; r['resolve_status'] = None
        if t == 'DOI':
            r['doi'] = pid.lower(); r['category'] = 'doi'; r['resolve_status'] = 'have_doi'
        elif t == 'OVID' and re.match(r'(?i)nct\d', pid):
            r['nct'] = pid.upper(); r['category'] = 'trial_registration'; r['resolve_status'] = 'trial_registration'
        elif t == 'OVID' and pid.isdigit():
            r['pmid'] = pid; r['category'] = 'pmid'
        elif t == 'EMBASE':
            r['category'] = 'embase_title'
        else:
            r['category'] = 'other'

    # --- PMID -> DOI via NCBI esummary (batched) ---
    pmid_recs = [r for r in records if r['category'] == 'pmid']
    print(f'PMID group: {len(pmid_recs)}')
    esum = {}
    pmids = [r['pmid'] for r in pmid_recs]
    for i in range(0, len(pmids), 150):
        chunk = pmids[i:i+150]
        url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=' + ','.join(chunk)
        try:
            res = json.loads(get(url, ua)).get('result', {})
            for pid in chunk:
                if pid in res: esum[pid] = res[pid]
        except Exception as e:
            print('NCBI err:', repr(e)[:100])
        time.sleep(0.4)
    for r in pmid_recs:
        info = esum.get(r['pmid'])
        if not info:
            r['resolve_status'] = 'pmid_no_ncbi'; continue
        doi = next((x.get('value') for x in info.get('articleids', []) if x.get('idtype') == 'doi'), None)
        r['matched_title'] = info.get('title', ''); r['match_score'] = sim(r.get('title', ''), info.get('title', ''))
        if doi:
            r['doi'] = doi.lower()
            r['resolve_status'] = 'resolved_doi' if r['match_score'] >= 0.85 else 'resolved_doi_check'
        else:
            r['resolve_status'] = 'pmid_no_doi'

    # --- EMBASE title -> DOI via Crossref ---
    emb = [r for r in records if r['category'] == 'embase_title']
    print(f'EMBASE group: {len(emb)}')
    for r in emb:
        title = (r.get('title') or '').strip()
        if not title:
            r['resolve_status'] = 'no_title'; continue
        q = urllib.parse.urlencode({'query.bibliographic': title, 'rows': 5, 'mailto': a.email})
        best, best_sc = None, 0
        try:
            for it in json.loads(get('https://api.crossref.org/works?' + q, ua)).get('message', {}).get('items', []):
                sc = sim(title, (it.get('title') or [''])[0])
                if sc > best_sc: best_sc, best = sc, it
        except Exception as e:
            r['resolve_status'] = 'crossref_err'; time.sleep(0.5); continue
        if best:
            r['matched_title'] = (best.get('title') or [''])[0]; r['match_score'] = best_sc
            cand = best.get('DOI', '').lower()
            ly = year_of(r.get('publish_date')); cy = None
            for k in ('published-print', 'published-online', 'published', 'issued'):
                dp = best.get(k, {}).get('date-parts')
                if dp and dp[0] and dp[0][0]: cy = str(dp[0][0]); break
            year_ok = (ly is None or cy is None or abs(int(ly) - int(cy)) <= 1)
            r['cand_type'] = best.get('type', ''); r['cand_year'] = cy
            if best_sc >= 0.90 and year_ok: r['doi'] = cand; r['resolve_status'] = 'resolved_doi'
            elif best_sc >= 0.80: r['doi'] = cand; r['resolve_status'] = 'resolved_doi_check'
            else: r['resolve_status'] = 'no_match'; r['cand_doi_low'] = cand
        else:
            r['resolve_status'] = 'no_match'
        time.sleep(0.34)

    json.dump({str(r['id']): r for r in records}, open(a.out, 'w', encoding='utf-8'), indent=1)
    from collections import Counter
    c = Counter(r['resolve_status'] for r in records)
    print('\n=== RESOLVE SUMMARY ===')
    for k, v in sorted(c.items(), key=lambda x: -x[1]): print(f'  {v:3}  {k}')
    print(f"Total with a DOI: {sum(1 for r in records if r.get('doi'))} / {len(records)}  -> {a.out}")

if __name__ == '__main__':
    main()
