// Main app — Workbench shell + state machine.
const { useState: uS, useEffect: uE, useMemo: uM, useRef: uR, useCallback: uC } = React;

const LS_KEY = "clauseiq_proto_v1";
function loadState(){
  try { return JSON.parse(localStorage.getItem(LS_KEY) || "{}"); } catch { return {}; }
}
function saveState(s){
  try { localStorage.setItem(LS_KEY, JSON.stringify(s)); } catch {}
}

function App(){
  const initial = loadState();
  const [query, setQuery]       = uS(initial.query || "");
  const [submitted, setSub]     = uS(initial.query || "");
  const [filters, setFilters]   = uS(initial.filters || { family:[], law:[], counterparty:[] });
  const [pinned, setPinned]     = uS(initial.pinned || []);
  const [recent, setRecent]     = uS(initial.recent || []);
  const [palOpen, setPal]       = uS(false);
  const [exportOpen, setExport] = uS(false);
  const [viewerId, setViewer]   = uS(null);
  const [pasteMode, setPaste]   = uS(false);
  const [pasteText, setPasteTx] = uS("");
  const [selIdx, setSelIdx]     = uS(0);
  const [loading, setLoading]   = uS(false);
  const [dockOpen, setDock]     = uS(initial.dockOpen ?? true);

  // persist
  uE(() => { saveState({ query: submitted, filters, pinned, recent, dockOpen }); }, [submitted, filters, pinned, recent, dockOpen]);

  // search
  const results = uM(() => window.search(submitted, filters), [submitted, filters]);
  const qTokens = uM(() => window.expandedTokens(submitted), [submitted]);

  uE(() => { setSelIdx(0); }, [submitted, filters]);

  const current = results[selIdx];

  // keyboard shortcuts
  uE(() => {
    function onKey(e){
      const t = e.target;
      const inField = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable);
      // Open palette
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault(); setPal(true); return;
      }
      if (e.key === "/" && !inField && !palOpen && !exportOpen && !viewerId) {
        e.preventDefault(); setPal(true); return;
      }
      if (e.key === "Escape") {
        if (palOpen) { setPal(false); return; }
      }
      if (palOpen || exportOpen || viewerId) return;
      if (inField) return;
      // Navigation + actions
      if (e.key === "j" || e.key === "ArrowDown") {
        if (results.length) { e.preventDefault(); setSelIdx(i => Math.min(results.length-1, i+1)); }
      } else if (e.key === "k" || e.key === "ArrowUp") {
        if (results.length) { e.preventDefault(); setSelIdx(i => Math.max(0, i-1)); }
      } else if (e.key === "p") {
        if (current) { e.preventDefault(); togglePin(current.clause.id); }
      } else if (e.key === "c") {
        if (current) { e.preventDefault(); navigator.clipboard?.writeText(current.clause.text); flash("Copied clause"); }
      } else if (e.key === "o") {
        if (current) { e.preventDefault(); setViewer(current.clause.id); }
      } else if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); setExport(true);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  // toast
  const [toast, setToast] = uS(null);
  function flash(msg){ setToast(msg); clearTimeout(flash._t); flash._t = setTimeout(()=>setToast(null), 1400); }

  function togglePin(id){
    setPinned(p => p.includes(id) ? p.filter(x=>x!==id) : [...p, id]);
    flash(pinned.includes(id) ? "Unpinned" : "Pinned to scratchpad");
  }
  const isPinned = (id) => pinned.includes(id);

  function runQuery(q, extraFilters){
    setLoading(true);
    setTimeout(() => setLoading(false), 280);
    setQuery(q);
    setSub(q);
    setPaste(false);
    if (extraFilters) {
      setFilters(f => ({...f, ...extraFilters}));
    }
    if (q.trim()) {
      setRecent(r => [q.trim(), ...r.filter(x => x !== q.trim())].slice(0, 8));
    }
  }
  function pasteMatch(text){
    setPaste(true); setPasteTx(text);
    setQuery(text); setSub(text);
    // auto-infer family roughly
    const lower = text.toLowerCase();
    let fam = null;
    if (/confidential|nda|trade secret/.test(lower)) fam = "confidentiality";
    else if (/liability|cap|aggregate/.test(lower)) fam = "limitation_of_liability";
    else if (/terminat|breach|cure/.test(lower)) fam = "termination";
    else if (/indemn/.test(lower)) fam = "indemnification";
    if (fam) setFilters(f => ({...f, family:[fam]}));
  }
  function clearFilter(kind, val){
    setFilters(f => ({...f, [kind]: f[kind].filter(x => x!==val)}));
  }
  function toggleFilter(kind, val){
    setFilters(f => ({...f, [kind]: f[kind].includes(val) ? f[kind].filter(x=>x!==val) : [...f[kind], val]}));
  }

  const famCounts = uM(() => window.familyCounts(), []);
  const lawCountsM = uM(() => window.lawCounts(), []);
  const cpCounts = uM(() => window.counterpartyCounts(), []);

  const hasQueryOrFilter = submitted.trim() || filters.family.length || filters.law.length || filters.counterparty.length;
  const filterCount = filters.family.length + filters.law.length + filters.counterparty.length;

  return (
    <div className="app">
      <Topbar
        query={submitted}
        onOpenPal={() => setPal(true)}
        pinnedCount={pinned.length}
        onOpenExport={() => setExport(true)}
        pasteMode={pasteMode}
        contractCount={window.CONTRACTS.length}
        clauseCount={window.CLAUSES.length}
      />

      <div className="main">
        <FilterRail
          filters={filters}
          famCounts={famCounts}
          lawCounts={lawCountsM}
          cpCounts={cpCounts}
          onToggle={toggleFilter}
          onClear={(k)=>setFilters(f=>({...f,[k]:[]}))}
        />

        <ResultsPanel
          query={submitted}
          loading={loading}
          results={results}
          selIdx={selIdx}
          onSelect={setSelIdx}
          onPin={togglePin}
          onOpen={(id)=>setViewer(id)}
          isPinned={isPinned}
          qTokens={qTokens}
          hasQueryOrFilter={hasQueryOrFilter}
          filters={filters}
          onClearFilter={clearFilter}
          pasteMode={pasteMode}
          pasteText={pasteText}
          onExitPaste={()=>{setPaste(false);setPasteTx("");}}
        />

        <PreviewPane
          item={current}
          qTokens={qTokens}
          onPin={togglePin}
          isPinned={current ? isPinned(current.clause.id) : false}
          onOpen={(id)=>setViewer(id)}
        />
      </div>

      <Dock
        open={dockOpen}
        onToggle={()=>setDock(d=>!d)}
        pinned={pinned}
        onUnpin={togglePin}
        onOpenExport={()=>setExport(true)}
        onView={(id)=>setViewer(id)}
      />

      <CommandPalette
        open={palOpen}
        onClose={()=>setPal(false)}
        onRunQuery={runQuery}
        onPasteMatch={pasteMatch}
        recentQueries={recent}
        currentQuery={query}
      />
      {viewerId && <ContractViewer clauseId={viewerId} onClose={()=>setViewer(null)} onPin={togglePin} isPinned={isPinned(viewerId)} />}
      {exportOpen && <ExportModal pinnedIds={pinned} onClose={()=>setExport(false)} />}

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

function Topbar({ query, onOpenPal, pinnedCount, onOpenExport, pasteMode, contractCount, clauseCount }){
  return (
    <div className="topbar">
      <div className="brand">Clause<span className="dot">IQ</span></div>
      <div className="searchbar" onClick={onOpenPal} title="Open command palette (⌘K)">
        <span className="chev">{pasteMode ? "¶" : ">"}</span>
        {query
          ? <span className="qtxt">{query}</span>
          : <span className="ph">{pasteMode ? "Paste-and-match active" : "Describe a clause, or paste draft language…"}</span>}
        <span className="sp"></span>
        <span className="kbd">⌘K</span>
      </div>
      <span className="pill">{clauseCount} clauses · {contractCount} contracts</span>
      <button className="bar-btn" onClick={onOpenExport} disabled={!pinnedCount}>
        {pinnedCount ? `${pinnedCount} pinned` : "0 pinned"}
      </button>
    </div>
  );
}

function FilterRail({ filters, famCounts, lawCounts, cpCounts, onToggle, onClear }){
  const [expandedFams, setExp] = uS(false);
  const fams = expandedFams ? window.FAMILIES : window.FAMILIES.slice(0,7);
  return (
    <aside className="rail">
      <div className="grp">
        <h4>Clause family {filters.family.length>0 && <span className="clear" onClick={()=>onClear("family")}>clear</span>}</h4>
        {fams.map(([k,l]) => (
          <div key={k} className={"opt" + (filters.family.includes(k)?" sel":"")} onClick={()=>onToggle("family",k)}>
            <span>{l}</span><span className="count">{famCounts[k]||0}</span>
          </div>
        ))}
        {!expandedFams && <div className="opt" onClick={()=>setExp(true)}><span className="more">Show all {window.FAMILIES.length} →</span></div>}
      </div>
      <div className="grp">
        <h4>Governing law {filters.law.length>0 && <span className="clear" onClick={()=>onClear("law")}>clear</span>}</h4>
        {Object.entries(lawCounts).map(([l,n]) => (
          <div key={l} className={"opt" + (filters.law.includes(l)?" sel":"")} onClick={()=>onToggle("law",l)}>
            <span>{l}</span><span className="count">{n}</span>
          </div>
        ))}
      </div>
      <div className="grp">
        <h4>Counterparty {filters.counterparty.length>0 && <span className="clear" onClick={()=>onClear("counterparty")}>clear</span>}</h4>
        {Object.entries(cpCounts).slice(0,6).map(([cp,n]) => (
          <div key={cp} className={"opt" + (filters.counterparty.includes(cp)?" sel":"")} onClick={()=>onToggle("counterparty",cp)}>
            <span>{cp}</span><span className="count">{n}</span>
          </div>
        ))}
      </div>
    </aside>
  );
}

function ResultsPanel({ query, loading, results, selIdx, onSelect, onPin, onOpen, isPinned, qTokens, hasQueryOrFilter, filters, onClearFilter, pasteMode, pasteText, onExitPaste }){
  if (!hasQueryOrFilter) return <EmptyHome />;
  if (loading) return <LoadingSkeleton />;
  return (
    <section className="results">
      {pasteMode && (
        <div className="paste-banner">
          <div className="pb-eyebrow">Pasted draft · click "exit" to switch back to query mode</div>
          <div className="pb-text">"{pasteText}"</div>
          <div className="pb-foot"><button className="bar-btn" onClick={onExitPaste}>Exit paste mode</button></div>
        </div>
      )}
      {(filters.family.length>0 || filters.law.length>0 || filters.counterparty.length>0) && (
        <div className="filter-chips">
          {filters.family.map(f => <span key={f} className="chip" onClick={()=>onClearFilter("family",f)}>family: {window.familyLabel(f)} <span className="x">×</span></span>)}
          {filters.law.map(l => <span key={l} className="chip" onClick={()=>onClearFilter("law",l)}>law: {l} <span className="x">×</span></span>)}
          {filters.counterparty.map(cp => <span key={cp} className="chip" onClick={()=>onClearFilter("counterparty",cp)}>cp: {cp} <span className="x">×</span></span>)}
        </div>
      )}
      <div className="results-head">
        <b>{results.length}</b> <span>results</span>
        <span className="sep">·</span><span>BM25 + kNN → RRF → rerank</span>
        <span className="sep">·</span><span>{(180 + Math.floor(Math.random()*40))} ms</span>
        <span style={{flex:1}}></span>
        <span className="pill">Relevance ↓</span>
      </div>
      {!results.length && <ZeroResults filters={filters} onClearFilter={onClearFilter} />}
      <div className="rows">
        {results.map((r, i) => (
          <ResultRow key={r.clause.id} idx={i+1} item={r} qTokens={qTokens} selected={i===selIdx}
            onClick={()=>onSelect(i)} onPin={()=>onPin(r.clause.id)} onOpen={()=>onOpen(r.clause.id)} pinned={isPinned(r.clause.id)} />
        ))}
      </div>
    </section>
  );
}

function ResultRow({ idx, item, qTokens, selected, onClick, onPin, onOpen, pinned }){
  const parts = window.highlight(item.clause.text, qTokens);
  return (
    <div className={"row" + (selected?" sel":"")} onClick={onClick} onDoubleClick={onOpen}>
      <div className="idx">{String(idx).padStart(2,"0")}</div>
      <div className="body">
        <div className="head">
          <span className="title">{item.clause.title}</span>
          <span className="pill fam">{item.clause.family}</span>
        </div>
        <div className="ctx">{item.contract.title} · <b>{item.contract.counterparty}</b> · {item.clause.section} · signed {item.contract.signed} · {item.contract.law}</div>
        <div className="clause">
          {parts.map((p,i) => p.hit ? <mark key={i}>{p.text}</mark> : <span key={i}>{p.text}</span>)}
        </div>
        <div className="meta">
          <span>score <b>{item.score.toFixed(2)}</b></span>
          {item.matched.length > 0 && <><span className="sep">·</span><span>matched: {item.matched.slice(0,4).join(" · ")}</span></>}
        </div>
      </div>
      <div className="act">
        <button className={pinned?"pinned":""} onClick={e=>{e.stopPropagation(); onPin();}} title="Pin (p)">📌</button>
        <button onClick={e=>{e.stopPropagation(); onOpen();}} title="Open contract (o)">↗</button>
      </div>
    </div>
  );
}

function PreviewPane({ item, qTokens, onPin, isPinned, onOpen }){
  if (!item) {
    return (
      <section className="preview">
        <div className="preview-head"><span className="trail">— select a result —</span></div>
        <div className="zero"><div className="ic">¶</div><h3>Preview appears here</h3><p>Selected clause will show in its contract context.</p></div>
      </section>
    );
  }
  const c = item.clause, ct = item.contract;
  const parts = window.highlight(c.text, qTokens);
  return (
    <section className="preview">
      <div className="preview-head">
        <span className="trail">{ct.title} › {c.article} › <b>{c.section} {c.title}</b></span>
        <button className={"bar-btn" + (isPinned?" active":"")} onClick={()=>onPin(c.id)}>{isPinned?"📌 Pinned":"📌 Pin"}</button>
        <button className="bar-btn" onClick={()=>{navigator.clipboard?.writeText(c.text);}}>Copy</button>
        <button className="bar-btn" onClick={()=>onOpen(c.id)}>Open ↗</button>
      </div>
      <div className="preview-body">
        <div className="doc-top">Master Services Agreement · Vendor Co. ↔ {ct.counterparty}</div>
        <h2>{c.article}</h2>
        <div className="focal">
          <div className="tag">{c.section} · {c.title} — matched</div>
          <div className="txt">{parts.map((p,i) => p.hit ? <mark key={i}>{p.text}</mark> : <span key={i}>{p.text}</span>)}</div>
        </div>
        <div className="ctx-line" style={{marginTop:18}}><b>Surrounding sections.</b> Other articles in {ct.title} include warranties, indemnification, term &amp; renewal, and general provisions. Click <span className="kbd">o</span> or "Open ↗" to read the full contract.</div>
      </div>
      <div className="preview-foot">
        <span>clause · <b>{c.id}</b></span>
        <span className="sep">·</span><span>confidence <b>high</b></span>
        <span className="sep">·</span><span>pages <b>{c.pages}</b></span>
        <span style={{flex:1}}></span>
        <span>use <span className="kbd">j</span>/<span className="kbd">k</span> to step</span>
      </div>
    </section>
  );
}

function Dock({ open, onToggle, pinned, onUnpin, onOpenExport, onView }){
  if (!open) {
    return (
      <div className="dock collapsed">
        <div className="dock-head">
          <span className="lbl">Scratchpad</span>
          <span className="pill">{pinned.length} clauses</span>
          <span style={{flex:1}}></span>
          <button className="bar-btn" onClick={onToggle}>Expand ↑</button>
        </div>
      </div>
    );
  }
  return (
    <div className="dock">
      <div className="dock-head">
        <span className="lbl">Scratchpad</span>
        <span className="pill">{pinned.length} {pinned.length===1?"clause":"clauses"} · {new Set(pinned.map(id=>window.CLAUSES.find(c=>c.id===id)?.contract).filter(Boolean)).size} contracts</span>
        <span style={{flex:1}}></span>
        <button className="bar-btn" disabled>Group by family</button>
        <button className="bar-btn primary" onClick={onOpenExport} disabled={!pinned.length}>Export draft <span className="kbd" style={{background:"transparent",border:"none",color:"rgba(255,255,255,.6)",marginLeft:4}}>⌘↵</span></button>
        <button className="bar-btn" onClick={onToggle}>Collapse ↓</button>
      </div>
      {!pinned.length ? (
        <div className="dock-empty">
          Press <span className="kbd">p</span> on a result to start collecting clauses for your draft.
        </div>
      ) : (
        <div className="dock-tiles">
          {pinned.map((id, i) => {
            const c = window.CLAUSES.find(x=>x.id===id);
            if (!c) return null;
            const ct = window.CONTRACTS.find(x=>x.id===c.contract);
            return (
              <div className="tile" key={id} onClick={()=>onView(id)}>
                <div className="th">
                  <span className="tt">{i+1} · {c.title}</span>
                  <span className="x" onClick={e=>{e.stopPropagation(); onUnpin(id);}}>×</span>
                </div>
                <div className="tm">{ct?.title.split(" ")[0]} {c.section}</div>
                <div className="tx">{c.text}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function EmptyHome(){
  return (
    <section className="results">
      <div className="empty-home">
        <div className="eh-title">Find a clause from your precedents.</div>
        <div className="eh-sub">Describe a clause in plain English, paste draft language, or pick a family to browse.</div>
        <div className="eh-tries">
          <span className="pill">cap on liability tied to 12 months of fees</span>
          <span className="pill">30-day cure period for breach</span>
          <span className="pill">auto-renewal with opt-out notice</span>
        </div>
        <div className="eh-kbd">
          <div className="ehk-head">Keyboard · always on</div>
          <div className="ehk-rows">
            <div><span className="kbd">/</span> open palette</div>
            <div><span className="kbd">⌘K</span> open palette</div>
            <div><span className="kbd">j</span> <span className="kbd">k</span> next / prev result</div>
            <div><span className="kbd">p</span> pin · <span className="kbd">c</span> copy · <span className="kbd">o</span> open</div>
            <div><span className="kbd">⌘↵</span> export draft</div>
          </div>
        </div>
      </div>
    </section>
  );
}

function LoadingSkeleton(){
  return (
    <section className="results">
      <div className="results-head"><span>Searching…</span><span className="sep">·</span><span>BM25 + kNN running</span></div>
      {[0,1,2,3].map(i => (
        <div className="row" key={i}>
          <div className="idx">—</div>
          <div className="body">
            <div className="shim" style={{width:"60%",margin:"4px 0 8px"}} />
            <div className="shim" style={{width:"40%",margin:"0 0 10px"}} />
            <div className="shim" style={{width:"95%",margin:"0 0 4px"}} />
            <div className="shim" style={{width:"88%",margin:"0 0 4px"}} />
            <div className="shim" style={{width:"70%"}} />
          </div>
        </div>
      ))}
    </section>
  );
}

function ZeroResults({ filters, onClearFilter }){
  return (
    <div style={{padding:"28px 18px"}}>
      <h3 style={{fontFamily:"var(--display)",fontWeight:600,fontSize:17,color:"var(--ink)",margin:"0 0 8px",letterSpacing:"-.01em"}}>No matching clauses.</h3>
      <p style={{color:"var(--ink-3)",fontSize:13,lineHeight:1.55,margin:"0 0 16px",maxWidth:340}}>Try broadening:</p>
      <div style={{display:"flex",flexDirection:"column",gap:8}}>
        {filters.law.map(l => <button key={l} className="bar-btn" style={{justifyContent:"flex-start"}} onClick={()=>onClearFilter("law",l)}><span style={{color:"var(--accent)",fontFamily:"var(--mono)"}}>×</span> Remove filter: <b style={{color:"var(--ink)",marginLeft:6}}>law = {l}</b></button>)}
        {filters.family.map(f => <button key={f} className="bar-btn" style={{justifyContent:"flex-start"}} onClick={()=>onClearFilter("family",f)}><span style={{color:"var(--accent)",fontFamily:"var(--mono)"}}>×</span> Remove filter: <b style={{color:"var(--ink)",marginLeft:6}}>family = {window.familyLabel(f)}</b></button>)}
        {filters.counterparty.map(cp => <button key={cp} className="bar-btn" style={{justifyContent:"flex-start"}} onClick={()=>onClearFilter("counterparty",cp)}><span style={{color:"var(--accent)",fontFamily:"var(--mono)"}}>×</span> Remove filter: <b style={{color:"var(--ink)",marginLeft:6}}>counterparty = {cp}</b></button>)}
      </div>
      <p style={{color:"var(--ink-4)",fontSize:11.5,fontFamily:"var(--mono)",margin:"18px 0 0",lineHeight:1.5}}>Tip: try broader phrasing — e.g. "long notice period" instead of "180 days".</p>
    </div>
  );
}

window.App = App;

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
