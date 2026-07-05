#!/usr/bin/env python3
"""Per-round bookkeeping for the browser/LibKey pass.

1. Moves valid Downloads/<id>.pdf (and Downloads/<id>_suppl*.*) into the output folder.
2. Records each study's status in browser_results.json.
3. Prints the NEXT batch of LibKey URLs to fetch (studies with a DOI, no file yet, not terminal,
   not on a known Cloudflare publisher).

Status tokens you pass come from the grab JS: OK<size> | LIBKEY | CF:<host> | FAIL:<host>.
Anything not 'retry' is treated as terminal (won't reappear in NEXT). Use 'retry' to re-queue.

Usage:
  python move_round.py "16302|OK,24634|LIBKEY,28757|CF:sciencedirect"      # process + print next
  python move_round.py ""                                                  # just print next batch
Options: --out Downloaded_files --downloads <chrome downloads dir> --resolved resolved.json
         --library 964 --batch 8
"""
import argparse, json, os, sys, shutil

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pairs', nargs='?', default='', help='comma list of "<id>|<status>"')
    ap.add_argument('--out', default='Downloaded_files')
    ap.add_argument('--downloads', default=os.path.join(os.path.expanduser('~'), 'Downloads'))
    ap.add_argument('--resolved', default='resolved.json')
    ap.add_argument('--library', default='964')
    ap.add_argument('--batch', type=int, default=8)
    a = ap.parse_args()
    import urllib.parse

    br = json.load(open('browser_results.json', encoding='utf-8')) if os.path.exists('browser_results.json') else {}
    for pr in [p for p in a.pairs.split(',') if p]:
        sid, status = pr.split('|', 1)
        src = os.path.join(a.downloads, sid + '.pdf'); moved = False
        if os.path.exists(src):
            try:
                head = open(src, 'rb').read(5); sz = os.path.getsize(src)
                if head == b'%PDF-' and sz > 2500:
                    shutil.move(src, os.path.join(a.out, sid + '.pdf'))
                    br[sid] = {'status': 'OK', 'size': sz}; moved = True; print(f'  {sid}: OK {sz//1024}KB')
                else:
                    os.remove(src)
            except Exception as e:
                print(f'  {sid}: mv-err {e}')
        if not moved:
            br[sid] = {'status': status}; print(f'  {sid}: {status}')
        # move any supplement files that landed for this id
        for f in os.listdir(a.downloads):
            if f.startswith(sid + '_suppl'):
                try: shutil.move(os.path.join(a.downloads, f), os.path.join(a.out, f)); print(f'    + {f}')
                except Exception: pass
    json.dump(br, open('browser_results.json', 'w', encoding='utf-8'), indent=0)

    # clean stray numeric pdfs in downloads (failed/duplicate)
    for f in os.listdir(a.downloads):
        if f.lower().endswith('.pdf') and f[:-4].isdigit():
            try: os.remove(os.path.join(a.downloads, f))
            except Exception: pass

    # compute NEXT batch
    resolved = json.load(open(a.resolved, encoding='utf-8'))
    existing = {f.rsplit('.', 1)[0] for f in os.listdir(a.out) if f.lower().endswith('.pdf') and '_suppl' not in f}
    HARD = {'10.1016', '10.2139'}  # ScienceDirect / SSRN (Cloudflare) — skip in auto loop
    def is_hard(doi): return doi.split('/')[0] in HARD or 'annonc' in doi
    terminal = {k for k, v in br.items() if v.get('status', '') != 'retry'}
    pending = []
    for sid, rec in resolved.items():
        if not rec.get('doi') or sid in existing or sid in terminal: continue
        if is_hard(rec['doi']): continue
        pending.append((sid, f"https://libkey.io/libraries/{a.library}/" + urllib.parse.quote(rec['doi'], safe='/')))
    print(f"Total PDFs: {len(existing)} | pending (non-Cloudflare): {len(pending)}")
    print('NEXT:')
    for sid, url in pending[:a.batch]:
        print(f'{sid}\t{url}')

if __name__ == '__main__':
    main()
