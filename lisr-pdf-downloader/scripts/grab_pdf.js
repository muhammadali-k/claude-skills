// grab_pdf.js — in-page PDF grab, run via the Claude-in-Chrome javascript_tool on a tab that has
// navigated (once) to a LibKey URL and redirected to the publisher PDF.
//
// Usage: substitute the filename, paste as the javascript_tool `text`. Run ONE per fresh tab; never
// re-navigate a tab after grabbing (Chrome cancels the pending download). Returns a status string:
//   "<id>.pdf|OK<size>"  success (a file download was triggered)
//   "<id>.pdf|LIBKEY"    still on libkey.io (no redirect -> no full text, or set the "remember PDF" pref once)
//   "<id>.pdf|CF:<host>" Cloudflare "verify you are human" wall (do NOT bypass)
//   "<id>.pdf|FAIL:<host>" no PDF found
//
// Wrapped in an IIFE so reruns don't hit "Identifier already declared"; each fetch has an
// AbortController timeout so one slow request can't freeze the batch.

await (async () => {
  const F = '__ID__.pdf';                       // <-- replace __ID__ with the study ID
  let R = '';
  const T = async (u) => {                      // timed fetch -> blob (or 0)
    try {
      const c = new AbortController(); const t = setTimeout(() => c.abort(), 18000);
      const r = await fetch(u, { credentials: 'include', signal: c.signal });
      const b = await r.blob(); clearTimeout(t); return b;
    } catch (e) { return 0; }
  };
  const ok = (b) => b && b.type && b.type.includes('pdf') && b.size > 1500;
  const P = (ms) => new Promise(r => setTimeout(r, ms));
  const H = location.hostname;
  if (H.includes('libkey')) return F + '|LIBKEY';
  if (/just a moment|verify you are human|attention required/i.test(document.title)) return F + '|CF:' + H;
  let b = await T(location.href);              // strategy 1: page itself is the PDF (NEJM, Springer)
  if (!ok(b)) {                                // strategy 2: find a pdf iframe/embed/link (Atypon wrappers)
    for (let k = 0; k < 2 && !ok(b); k++) {
      let q = [...document.querySelectorAll('iframe,embed,object')].map(e => e.src || e.data)
        .filter(s => s && /pdf/i.test(s));
      [...document.querySelectorAll('a')].forEach(a => { if (a.href && /pdfdirect|epdf|\/pdf\/|\.pdf(\?|$)/i.test(a.href)) q.push(a.href); });
      q.sort((x, y) => (/pdfdirect/i.test(y) ? 1 : 0) - (/pdfdirect/i.test(x) ? 1 : 0));
      for (const c of q) { const bb = await T(c); if (ok(bb)) { b = bb; break; } }
      if (!ok(b)) await P(1500);
    }
  }
  if (ok(b)) {
    const u = URL.createObjectURL(b); const a = document.createElement('a');
    a.href = u; a.download = F; document.body.appendChild(a); a.click();
    await P(2500);                              // let the download flush BEFORE the tab is reused/closed
    return F + '|OK' + b.size;
  }
  return F + '|FAIL:' + H;
})()


// ---------------------------------------------------------------------------------------------
// SUPPLEMENT VARIANT — run on a publisher ARTICLE LANDING PAGE (not the PDF) to collect supplements.
// Returns "<id>|SUPP:<n>" after triggering downloads named <id>_suppl<n>.<ext>. Best-effort.
//
// await (async () => {
//   const SID = '__ID__';
//   const T = async (u) => { try { const c=new AbortController(); const t=setTimeout(()=>c.abort(),18000);
//     const r=await fetch(u,{credentials:'include',signal:c.signal}); const b=await r.blob(); clearTimeout(t); return b; } catch(e){ return 0; } };
//   const P = (ms)=>new Promise(r=>setTimeout(r,ms));
//   // collect candidate supplement links: by section text OR by file extension
//   const exts = /\.(pdf|docx?|xlsx?|pptx?|csv|zip|tif{1,2}|jpe?g|png)(\?|$)/i;
//   const cand = new Set();
//   document.querySelectorAll('a[href]').forEach(a => {
//     const txt = (a.textContent || '') + ' ' + a.href;
//     if (/suppl|appendix|additional file|data supplement|supporting information|media/i.test(txt) || exts.test(a.href))
//       cand.add(a.href);
//   });
//   let n = 0;
//   for (const url of [...cand]) {
//     const b = await T(url);
//     if (b && b.size > 1500 && !/text\/html/i.test(b.type)) {
//       n++; let ext = (url.match(exts) || [,''])[1] || (b.type.split('/')[1] || 'dat'); ext = ext.replace('jpeg','jpg');
//       const a = document.createElement('a'); a.href = URL.createObjectURL(b);
//       a.download = `${SID}_suppl${n}.${ext}`; document.body.appendChild(a); a.click(); await P(2000);
//     }
//   }
//   return SID + '|SUPP:' + n;
// })()
