#!/usr/bin/env python3
"""Build a self-contained, searchable/sortable/filterable HTML apply list.

Usage:
    python3 build_interactive_list.py programs.json --config config.json --out "apply_list.html"

Pure standard library. See scripts/README.md for the schemas. Opens offline in any browser.
"""
import argparse, json

def load(p):
    with open(p) as f: return json.load(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("programs")
    ap.add_argument("--config", default=None)
    ap.add_argument("--out", default="apply_list.html")
    a = ap.parse_args()
    progs = load(a.programs)
    cfg = load(a.config) if a.config else {}
    applicant = cfg.get("applicant", "Applicant")
    specialty = cfg.get("specialty", "Internal Medicine")
    cycle = cfg.get("cycle", "")
    affinity = cfg.get("affinity_label", "Affinity")

    # normalize + order
    sO = {"Gold": 0, "Silver": 1, "": 2}; tO = {"Reach": 0, "Target": 1, "Safety": 2}
    def gg(o, k, d=""):
        v = o.get(k); return v if v not in (None, "") else d
    rows = []
    for o in progs:
        rows.append(dict(
            name=str(gg(o, "name")), state=gg(o, "state"), div=gg(o, "division", "—"),
            tier=gg(o, "tier", "Target"), signal=gg(o, "signal"),
            type=gg(o, "type", gg(o, "university")), nonus=gg(o, "nonus_img"),
            affinity=gg(o, "affinity"), visa=gg(o, "visa"), fellow=gg(o, "fellowship"),
            re_gold=gg(o, "re_gold", "—"), url=gg(o, "url"),
            same_school=bool(o.get("same_school")), verified=bool(o.get("verified")),
            notes=gg(o, "notes")))
    rows.sort(key=lambda r: (0 if r["signal"] else 1, sO.get(r["signal"], 2), tO.get(r["tier"], 1), r["name"]))
    for i, r in enumerate(rows, 1): r["rank"] = i
    from collections import Counter
    tc = Counter(r["tier"] for r in rows)
    ng = sum(1 for r in rows if r["signal"] == "Gold"); ns = sum(1 for r in rows if r["signal"] == "Silver")
    nlive = sum(1 for r in rows if r["verified"])
    data = json.dumps(rows).replace("</", "<\\/")
    title = f"{specialty} apply list — {applicant}"

    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>
 :root{{--paper:#F6F7F9;--ink:#16212B;--muted:#51606E;--faint:#7C8896;--line:#E1E5EA;--line2:#EEF1F4;--teal:#0E6E68;--teal-ink:#0A4F4A;--reach:#6C4FB0;--reach-bg:#EFEAF7;--target:#1F7A4D;--target-bg:#E4F1EA;--safety:#B0781E;--safety-bg:#F6ECD8;--gold:#7A5C00;--gold-bg:#F4E5B8;--silver:#495260;--silver-bg:#E6E9ED;--aff:#0A6B3B;--serif:"Charter","Iowan Old Style",Georgia,serif;--sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--mono:ui-monospace,"SF Mono",Menlo,monospace;}}
 *{{box-sizing:border-box}}html,body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans)}}
 .wrap{{max-width:1340px;margin:0 auto;padding:24px 18px 80px}}h1{{font-family:var(--serif);font-size:24px;margin:0 0 3px}}
 .eyebrow{{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--teal);font-weight:600}}
 .sub{{color:var(--muted);font-size:13.5px;margin:0 0 14px;max-width:96ch}}
 .bar{{position:sticky;top:0;z-index:5;background:var(--paper);padding:11px 0;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-bottom:6px}}
 input#q{{font:inherit;font-size:13px;padding:8px 12px;border:1px solid var(--line);border-radius:8px;min-width:200px;background:#fff}}select{{font:inherit;font-size:13px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:#fff}}
 .tg{{font-family:var(--mono);font-size:11px;font-weight:600;text-transform:uppercase;padding:6px 11px;border-radius:20px;border:1px solid var(--line);background:#fff;cursor:pointer;color:var(--muted);user-select:none}}
 .tg.on{{color:#fff}}.tg.on[data-k=Reach]{{background:var(--reach);border-color:var(--reach)}}.tg.on[data-k=Target]{{background:var(--target);border-color:var(--target)}}.tg.on[data-k=Safety]{{background:var(--safety);border-color:var(--safety)}}
 .tg.on[data-k=Gold]{{background:var(--gold);border-color:var(--gold)}}.tg.on[data-k=Silver]{{background:var(--silver);border-color:var(--silver)}}.tg.on[data-k=Aff]{{background:var(--aff);border-color:var(--aff)}}.tg.on[data-k=Both]{{background:var(--teal);border-color:var(--teal)}}.tg.on[data-k=Live]{{background:var(--teal-ink);border-color:var(--teal-ink)}}
 .count{{margin-left:auto;font-family:var(--mono);font-size:12px;color:var(--faint)}}.count b{{color:var(--teal-ink)}}
 .legend{{display:flex;flex-wrap:wrap;gap:6px 15px;font-size:11.5px;color:var(--muted);margin:8px 0 12px}}.legend .i{{display:flex;align-items:center;gap:5px}}
 .tblwrap{{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:#fff}}table{{border-collapse:collapse;width:100%;min-width:1140px;font-size:12px}}
 thead th{{position:sticky;top:0;background:#EDF0F3;text-align:left;padding:8px 9px;font-family:var(--mono);font-size:9.5px;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--line);cursor:pointer;white-space:nowrap;z-index:1}}
 thead th.sorted::after{{content:" \\25B4";color:var(--teal)}}thead th.sorted.desc::after{{content:" \\25BE"}}
 td{{padding:7px 9px;border-bottom:1px solid var(--line2);vertical-align:top}}tr.r:hover td{{background:#FAFBFC}}.tnum{{font-variant-numeric:tabular-nums}}
 .prog{{font-weight:600;line-height:1.22}}.aff{{color:var(--teal);font-weight:700}}.live{{color:var(--teal-ink);font-weight:700;font-size:10px}}
 .note{{color:var(--muted);font-size:10.5px;line-height:1.3;margin-top:2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;max-width:42ch}}
 .chip{{display:inline-block;font-family:var(--mono);font-size:10px;font-weight:600;padding:2px 7px;border-radius:20px;text-transform:uppercase;white-space:nowrap}}
 .chip.Reach{{background:var(--reach-bg);color:var(--reach)}}.chip.Target{{background:var(--target-bg);color:var(--target)}}.chip.Safety{{background:var(--safety-bg);color:var(--safety)}}.chip.Gold{{background:var(--gold-bg);color:var(--gold)}}.chip.Silver{{background:var(--silver-bg);color:var(--silver)}}
 .affdot{{width:8px;height:8px;border-radius:50%;background:var(--aff);display:inline-block;margin-right:4px}}.reg{{color:var(--target);font-weight:700}}.ren{{color:var(--faint)}}
 .divh td{{background:var(--ink);color:#fff;font-family:var(--mono);font-size:11px;text-transform:uppercase;padding:7px 9px;font-weight:600}}
 a{{color:var(--teal-ink)}}.foot{{margin-top:14px;font-size:11px;color:var(--faint);max-width:96ch}}@media print{{.bar{{position:static}}thead th{{position:static}}.note{{-webkit-line-clamp:unset}}}}
</style></head><body><div class="wrap">
 <div class="eyebrow">{specialty} · residency apply list{(" · " + cycle) if cycle else ""}</div>
 <h1>{title}</h1>
 <p class="sub">{len(rows)} programs · {tc.get('Reach',0)} reach / {tc.get('Target',0)} target / {tc.get('Safety',0)} safety · {ng} Gold + {ns} Silver signals · {nlive} <span class="live">live-checked</span> on the program's own roster. "RE Gold-signal" = interview rate with a Gold signal vs none. Click a header to sort; use the search + filters.</p>
 <div class="bar"><input id="q" type="search" placeholder="Search…" oninput="render()">
  <select id="div" onchange="render()"><option value="">All divisions</option></select>
  <span class="tg" data-k="Reach" onclick="tg(this)">Reach</span><span class="tg" data-k="Target" onclick="tg(this)">Target</span><span class="tg" data-k="Safety" onclick="tg(this)">Safety</span>
  <span class="tg" data-k="Gold" onclick="tg(this)">Gold</span><span class="tg" data-k="Silver" onclick="tg(this)">Silver</span>
  <span class="tg" data-k="Aff" onclick="tg(this)">{affinity}</span><span class="tg" data-k="Both" onclick="tg(this)">Both-visa</span><span class="tg" data-k="Live" onclick="tg(this)">Live-checked</span>
  <span class="count" id="count"></span></div>
 <div class="legend"><span class="i"><span class="chip Reach">Reach</span><span class="chip Target">Target</span><span class="chip Safety">Safety</span></span><span class="i"><span class="chip Gold">Gold</span>/<span class="chip Silver">Silver</span></span><span class="i"><span class="affdot"></span>{affinity}</span><span class="i"><span class="aff">◆</span>own-school tie</span><span class="i"><span class="live">✓</span>live-checked</span></div>
 <div class="tblwrap"><table><thead><tr>
  <th data-c="rank" onclick="srt('rank')">#</th><th data-c="signal" onclick="srt('signal')">Signal</th><th data-c="name" onclick="srt('name')">Program</th><th data-c="state" onclick="srt('state')">St</th><th data-c="tier" onclick="srt('tier')">Tier</th>
  <th data-c="type" onclick="srt('type')">Type</th><th data-c="nonus" onclick="srt('nonus')">Non-US IMG</th><th data-c="affinity" onclick="srt('affinity')">{affinity} residents</th><th data-c="visa" onclick="srt('visa')">Visa</th><th data-c="fellow" onclick="srt('fellow')">Fellowship</th><th data-c="re_gold" onclick="srt('re_gold')">RE Gold-sig</th>
 </tr></thead><tbody id="tb"></tbody></table></div>
 <p class="foot">Program websites are the source of truth; aggregator figures are labeled where used. Re-confirm in Residency Explorer + program sites before finalizing.</p>
</div><script>
const DATA={data};const tO={{"Reach":0,"Target":1,"Safety":2}};let sc="rank",sd=1;const act={{tier:new Set(),sig:new Set(),aff:false,both:false,live:false}};
{{const ds=[...new Set(DATA.map(r=>r.div))].filter(Boolean).sort();const sel=document.getElementById("div");ds.forEach(d=>{{const o=document.createElement("option");o.value=d;o.textContent=d;sel.appendChild(o);}});}}
function tg(el){{const k=el.dataset.k;el.classList.toggle("on");if(["Reach","Target","Safety"].includes(k))act.tier.has(k)?act.tier.delete(k):act.tier.add(k);else if(["Gold","Silver"].includes(k))act.sig.has(k)?act.sig.delete(k):act.sig.add(k);else if(k=="Aff")act.aff=el.classList.contains("on");else if(k=="Both")act.both=el.classList.contains("on");else if(k=="Live")act.live=el.classList.contains("on");render();}}
function srt(c){{if(sc===c)sd*=-1;else{{sc=c;sd=1;}}render();}}
function esc(s){{return (s==null?"":String(s)).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}}
function affpos(s){{return /strong|high|^\\s*\\d|roster-confirmed/i.test(s||"")&&!/not roster-confirmed|not roster|unknown|none/i.test(s||"");}}
function bothvisa(s){{return /h-1b/i.test(s||"")&&!/no h-1b|not.*h-1b|h-1b n|j-1 only|j1 only/i.test(s||"");}}
function render(){{const q=document.getElementById("q").value.toLowerCase().trim(),dv=document.getElementById("div").value;
 let rs=DATA.filter(r=>{{if(dv&&r.div!==dv)return false;if(act.tier.size&&!act.tier.has(r.tier))return false;if(act.sig.size&&!act.sig.has(r.signal))return false;
  if(act.aff&&!affpos(r.affinity))return false;if(act.both&&!bothvisa(r.visa))return false;if(act.live&&!r.verified)return false;
  if(q){{const b=(r.name+" "+r.state+" "+r.affinity+" "+r.fellow+" "+r.type+" "+r.notes+" "+r.visa).toLowerCase();if(!b.includes(q))return false;}}return true;}});
 rs.sort((a,b)=>{{let va=a[sc],vb=b[sc];if(sc=="tier"){{va=tO[va];vb=tO[vb];}}if(sc=="signal"){{const o={{Gold:0,Silver:1,"":2}};va=o[va];vb=o[vb];}}if(sc=="re_gold"){{va=parseFloat(va)||-1;vb=parseFloat(vb)||-1;}}if(typeof va=="string"){{va=va.toLowerCase();vb=String(vb).toLowerCase();}}if(va<vb)return -sd;if(va>vb)return sd;return a.rank-b.rank;}});
 const grp=(sc=="rank"&&!dv&&!act.tier.size&&!act.sig.size);let h="",cd=null;
 for(const r of rs){{if(grp&&r.div!==cd){{cd=r.div;const n=rs.filter(x=>x.div===cd).length;h+=`<tr class="divh"><td colspan="11">${{esc(cd)}} — ${{n}}</td></tr>`;}}
  const sig=r.signal?`<span class="chip ${{r.signal}}">${{r.signal}}</span>`:"";const ad=affpos(r.affinity)?`<span class="affdot"></span>`:"";
  const nm=`<div class="prog">${{esc(r.name)}}${{r.same_school?' <span class="aff" title="own-school tie">◆</span>':""}}${{r.verified?' <span class="live" title="live roster-checked">✓</span>':""}}${{r.url?` <a href="${{esc(r.url)}}" target="_blank" title="official site">↗</a>`:""}}</div><div class="note" title="${{esc(r.notes)}}">${{esc(r.notes)}}</div>`;
  const gc=r.re_gold==="—"||!r.re_gold?'<span class="ren">—</span>':`<span class="reg">${{esc(String(r.re_gold).split(" ")[0])}}</span>`;
  h+=`<tr class="r"><td class="tnum">${{r.rank}}</td><td>${{sig}}</td><td>${{nm}}</td><td>${{esc(r.state)}}</td><td><span class="chip ${{r.tier}}">${{r.tier}}</span></td><td>${{esc(r.type)}}</td><td class="tnum">${{esc(r.nonus)}}</td><td>${{ad}}${{esc(r.affinity)}}</td><td>${{esc(r.visa)}}</td><td>${{esc(r.fellow)}}</td><td>${{gc}}</td></tr>`;}}
 document.getElementById("tb").innerHTML=h;document.getElementById("count").innerHTML=`<b>${{rs.length}}</b> of ${{DATA.length}}`;
 document.querySelectorAll("thead th").forEach(t=>{{t.classList.remove("sorted","desc");if(t.dataset.c===sc){{t.classList.add("sorted");if(sd<0)t.classList.add("desc");}}}});}}
render();
</script></body></html>'''
    with open(a.out, "w") as f:
        f.write(html)
    print(f"Saved {a.out}  ({len(rows)} programs, {ng} Gold + {ns} Silver, {nlive} live-verified)")

if __name__ == "__main__":
    main()
