// Contract viewer (drill-in) and Export modal.
const { useEffect: useEffect_v, useState: useState_v } = React;

function ContractViewer({ clauseId, onClose, onPin, isPinned }){
  const clause = window.CLAUSES.find(c => c.id === clauseId);
  if (!clause) return null;
  const contract = window.CONTRACTS.find(c => c.id === clause.contract);

  // Surrounding clauses from same contract
  const sibs = window.CLAUSES.filter(c => c.contract === contract.id);
  const idx = sibs.findIndex(c => c.id === clauseId);

  useEffect_v(() => {
    function onKey(e){
      if (e.key === "Escape") { e.preventDefault(); onClose(); }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function copyText(){
    navigator.clipboard?.writeText(clause.text);
  }

  return (
    <div className="modal-scrim" onClick={onClose}>
      <div className="cv" onClick={e=>e.stopPropagation()}>
        <div className="cv-top">
          <div className="cv-trail">
            <span className="cv-back" onClick={onClose}>← Back to results</span>
            <span className="sep">·</span>
            <b>{contract.title}</b>
            <span className="sep">›</span>
            <span>{clause.article}</span>
            <span className="sep">›</span>
            <b>{clause.section} {clause.title}</b>
          </div>
          <div className="cv-actions">
            <button className="bar-btn" onClick={copyText}>Copy clause</button>
            <button className={"bar-btn" + (isPinned?" active":"")} onClick={()=>onPin(clause.id)}>{isPinned ? "📌 Pinned" : "📌 Pin"}</button>
            <button className="bar-btn" onClick={onClose}>Close <span className="kbd">esc</span></button>
          </div>
        </div>
        <div className="cv-body">
          <aside className="cv-meta">
            <div className="mk">Contract</div>
            <div className="mv">{contract.title}</div>
            <div className="mk">Counterparty</div>
            <div className="mv">{contract.counterparty}</div>
            <div className="mk">Signed</div>
            <div className="mv">{contract.signed}</div>
            <div className="mk">Governing law</div>
            <div className="mv">{contract.law}</div>
            <div className="mk">Pages</div>
            <div className="mv">{contract.pages}</div>
            <div className="mk">Clause id</div>
            <div className="mv mono">{clause.id} · {clause.section}</div>
            <div className="mk">Family</div>
            <div className="mv mono">{clause.family}</div>

            <div className="mk" style={{marginTop:18}}>Other clauses in this contract</div>
            <div className="cv-sibs">
              {sibs.map((s,i) => (
                <a className={"sib" + (s.id===clauseId?" cur":"")} key={s.id} href={"#"+s.id}
                   onClick={e=>{e.preventDefault(); document.getElementById("cv-sec-"+s.id)?.scrollIntoView({block:"center", behavior:"smooth"});}}>
                  <span className="sn">{s.section}</span>
                  <span className="st">{s.title}</span>
                </a>
              ))}
            </div>
          </aside>
          <div className="cv-doc">
            <div className="doc-head-fake">
              <div className="dh-eyebrow">Master Services Agreement</div>
              <div className="dh-title">{contract.title}</div>
              <div className="dh-sub">Vendor Co. ↔ {contract.counterparty} · Executed {contract.signed} · Governed by {contract.law} law</div>
            </div>
            {sibs.map((s,i) => (
              <section className={"doc-sec" + (s.id===clauseId?" focal":"")} key={s.id} id={"cv-sec-"+s.id}>
                <div className="ds-head">
                  <span className="ds-num">{s.section}</span>
                  <span className="ds-title">{s.title}</span>
                  {s.id===clauseId && <span className="ds-tag">matched</span>}
                </div>
                <div className="ds-body">{s.text}</div>
              </section>
            ))}
            <section className="doc-sec faded">
              <div className="ds-head"><span className="ds-num">§ — </span><span className="ds-title">Additional sections not extracted</span></div>
              <div className="ds-body" style={{color:"var(--ink-4)"}}>This is a prototype; only extracted clauses are shown. In production, the full contract text would render here with the matched clause highlighted in context.</div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}

function ExportModal({ pinnedIds, onClose }){
  const pinned = pinnedIds.map(id => window.CLAUSES.find(c => c.id===id)).filter(Boolean);
  const [tmpl, setTmpl] = useState_v("Blank MSA");
  const [cite, setCite] = useState_v("Word comments");

  useEffect_v(() => {
    function onKey(e){ if (e.key==="Escape") onClose(); }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const grouped = {};
  pinned.forEach(c => { (grouped[c.family] = grouped[c.family]||[]).push(c); });

  function doDownload(){
    // Build a fake .docx-ish text file as a stand-in
    const lines = [];
    lines.push("MASTER SERVICES AGREEMENT");
    lines.push("DRAFT — assembled by ClauseIQ — " + new Date().toISOString().slice(0,10));
    lines.push("");
    Object.entries(grouped).forEach(([fam, list], i) => {
      lines.push(`${i+1}. ${window.familyLabel(fam).toUpperCase()}`);
      list.forEach((c,j) => {
        lines.push(`  ${i+1}.${j+1} ${c.title}`);
        lines.push(`    ${c.text}`);
        lines.push(`    [comment: cited from ${window.CONTRACTS.find(x=>x.id===c.contract).title} ${c.section}]`);
        lines.push("");
      });
    });
    const blob = new Blob([lines.join("\n")], { type:"text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "ClauseIQ-draft.txt";
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    onClose();
  }

  return (
    <div className="modal-scrim" onClick={onClose}>
      <div className="export" onClick={e=>e.stopPropagation()}>
        <div className="cv-top">
          <div className="cv-trail">
            <b>Export draft</b>
            <span className="sep">·</span>
            <span>{pinned.length} clauses · {new Set(pinned.map(p=>p.contract)).size} contracts</span>
          </div>
          <div className="cv-actions">
            <button className="bar-btn" onClick={onClose}>Cancel</button>
            <button className="bar-btn primary" onClick={doDownload} disabled={!pinned.length}>Download draft ↓</button>
          </div>
        </div>
        <div className="export-body">
          <div className="ex-left">
            <div className="ex-eyebrow">Section order · {pinned.length} pinned clauses, grouped by family</div>
            {!pinned.length && <div style={{color:"var(--ink-3)",padding:"24px 4px",fontSize:13}}>Nothing pinned yet. Press <span className="kbd">p</span> on a result to pin it.</div>}
            {Object.entries(grouped).map(([fam, list], i) => (
              <div key={fam} className="ex-grp">
                <div className="ex-grp-head">§ {i+1} · {window.familyLabel(fam)} <span className="ex-count">{list.length}</span></div>
                {list.map((c,j) => (
                  <div className="ex-tile" key={c.id}>
                    <div className="ex-th">
                      <span className="ex-tt">{i+1}.{j+1} · {c.title}</span>
                      <span className="ex-tm">⋮⋮ {window.CONTRACTS.find(x=>x.id===c.contract).title.split(" ")[0]} {c.section}</span>
                    </div>
                    <div className="ex-tx">{c.text}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div className="ex-right">
            <div className="ex-controls">
              <span className="pill ink" onClick={()=>setTmpl(tmpl==="Blank MSA"?"Firm template":"Blank MSA")} style={{cursor:"pointer"}}>Template · {tmpl}</span>
              <span className="pill" onClick={()=>setCite(cite==="Word comments"?"Footnotes":"Word comments")} style={{cursor:"pointer"}}>Citations · {cite}</span>
              <span className="pill">Numbering · auto</span>
            </div>
            <div className="ex-preview">
              <div className="ep-title">MASTER SERVICES AGREEMENT</div>
              <div className="ep-sub">DRAFT · assembled by ClauseIQ · {new Date().toISOString().slice(0,10)}</div>
              {Object.entries(grouped).slice(0,3).map(([fam, list], i) => (
                <div key={fam} className="ep-sec">
                  <div className="ep-h">{i+1}. {window.familyLabel(fam).toUpperCase()}.</div>
                  {list.slice(0,2).map((c,j) => (
                    <div key={c.id}>
                      <div className="ep-p"><b>{i+1}.{j+1} {c.title}.</b> {c.text}</div>
                      {cite==="Word comments" && <div className="ep-cite">▸ Word comment: cited from {window.CONTRACTS.find(x=>x.id===c.contract).title} {c.section}</div>}
                      {cite==="Footnotes" && <div className="ep-cite">[{i+1}.{j+1}] {window.CONTRACTS.find(x=>x.id===c.contract).title} {c.section}</div>}
                    </div>
                  ))}
                </div>
              ))}
              {!pinned.length && <div style={{color:"var(--ink-4)",padding:"40px 0",textAlign:"center",fontSize:13}}>No pinned clauses to preview.</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

window.ContractViewer = ContractViewer;
window.ExportModal = ExportModal;
