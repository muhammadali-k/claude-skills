#!/usr/bin/env python3
"""Open-access full-text + supplementary-file fetcher (no browser needed).

For every study with a DOI in resolved.json:
  - Unpaywall -> best OA PDF -> <out>/<id>.pdf  (validated %PDF, >3KB)
  - NCBI ID-converter DOI/PMID -> PMCID, then Europe PMC supplementaryFiles ZIP
    -> unpacked to <out>/<id>_suppl<n>.<ext>

This clears genuinely open-access items (PMC, MDPI, BMC, preprints) and many supplements
without touching Chrome. Paywalled items fall through to the browser/LibKey pass.

Usage:
  python fetch_oa_and_supplements.py --resolved resolved.json --out Downloaded_files --email you@example.com
  python fetch_oa_and_supplements.py ... --no-supplements      # skip supplement fetching
"""
import argparse, json, os, time, io, zipfile, urllib.request, urllib.parse

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'

def fetch(url, timeout=40, referer=None):
    h = {'User-Agent': UA}
    if referer: h['Referer'] = referer
    return urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=timeout)

def pmcid_for(doi, pmid, email):
    ids = doi or pmid
    if not ids: return None
    try:
        u = ('https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?format=json&tool=srdl&email='
             + urllib.parse.quote(email) + '&ids=' + urllib.parse.quote(ids))
        d = json.loads(fetch(u, 25).read())
        recs = d.get('records', [])
        if recs and recs[0].get('pmcid'): return recs[0]['pmcid']
    except Exception:
        pass
    return None

def grab_supplements(pmcid, sid, out):
    """Europe PMC supplementaryFiles returns a ZIP of all supplements."""
    try:
        data = fetch(f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/supplementaryFiles', 60).read()
    except Exception:
        return 0
    if data[:2] != b'PK':
        return 0
    n = 0
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
        members = [m for m in zf.namelist() if not m.endswith('/')]
        for i, m in enumerate(members, 1):
            ext = os.path.splitext(m)[1].lower() or '.dat'
            tag = '_suppl' if len(members) == 1 else f'_suppl{i}'
            with zf.open(m) as fh:
                open(os.path.join(out, f'{sid}{tag}{ext}'), 'wb').write(fh.read())
            n += 1
    except Exception:
        return n
    return n

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resolved', default='resolved.json')
    ap.add_argument('--out', default='Downloaded_files')
    ap.add_argument('--email', default='research@example.com')
    ap.add_argument('--no-supplements', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    resolved = json.load(open(a.resolved, encoding='utf-8'))
    results = json.load(open('oa_results.json', encoding='utf-8')) if os.path.exists('oa_results.json') else {}
    existing = {f.rsplit('.', 1)[0] for f in os.listdir(a.out) if f.lower().endswith('.pdf') and '_suppl' not in f}

    todo = [sid for sid, r in resolved.items() if r.get('doi') and sid not in existing]
    print(f'OA candidates (no PDF yet): {len(todo)}')
    n_ok = n_supp = 0
    for sid in todo:
        rec = resolved[sid]; doi = rec['doi']
        # --- OA PDF via Unpaywall ---
        pdf_url = oa_status = None
        try:
            d = json.loads(fetch('https://api.unpaywall.org/v2/' + urllib.parse.quote(doi) + '?email=' + a.email, 25).read())
            oa_status = d.get('oa_status'); loc = d.get('best_oa_location') or {}
            pdf_url = loc.get('url_for_pdf')
        except Exception as e:
            results[sid] = {'status': 'unpaywall_err', 'doi': doi, 'detail': repr(e)[:80]}; time.sleep(0.2); continue
        if pdf_url:
            try:
                data = fetch(pdf_url, 45, referer='https://unpaywall.org').read()
                if data[:5] == b'%PDF-' and len(data) > 3000:
                    open(os.path.join(a.out, sid + '.pdf'), 'wb').write(data)
                    results[sid] = {'status': 'oa_ok', 'size': len(data), 'oa_status': oa_status, 'doi': doi}
                    n_ok += 1; print(f'  {sid} OA_OK {len(data)//1024}KB ({oa_status})')
                else:
                    results[sid] = {'status': 'oa_notpdf', 'oa_status': oa_status, 'doi': doi}
            except Exception as e:
                results[sid] = {'status': 'oa_dl_err', 'oa_status': oa_status, 'doi': doi, 'detail': repr(e)[:80]}
        else:
            results[sid] = {'status': 'no_oa', 'oa_status': oa_status, 'doi': doi}
        # --- Supplements via Europe PMC (independent of OA PDF success) ---
        if not a.no_supplements and not any(f.startswith(sid + '_suppl') for f in os.listdir(a.out)):
            pmcid = pmcid_for(doi, rec.get('pmid'), a.email)
            if pmcid:
                got = grab_supplements(pmcid, sid, a.out)
                if got: n_supp += got; results[sid]['supplements'] = got; print(f'    {sid} supplements: {got} file(s)')
        json.dump(results, open('oa_results.json', 'w', encoding='utf-8'), indent=0)
        time.sleep(0.25)

    from collections import Counter
    c = Counter(v['status'] for v in results.values())
    print('\n=== OA SUMMARY ===')
    for k, v in sorted(c.items(), key=lambda x: -x[1]): print(f'  {v:3}  {k}')
    print(f'New OA PDFs: {n_ok} | supplement files: {n_supp}')
    json.dump(results, open('oa_results.json', 'w', encoding='utf-8'), indent=0)

if __name__ == '__main__':
    main()
