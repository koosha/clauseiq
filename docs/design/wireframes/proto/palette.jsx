// Command palette — ⌘K / / opens it.
const { useState, useEffect, useRef, useMemo } = React;

function CommandPalette({ open, onClose, onRunQuery, onPasteMatch, recentQueries, currentQuery }){
  const [q, setQ] = useState(currentQuery || "");
  const [sel, setSel] = useState(0);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      setQ(currentQuery || "");
      setSel(0);
      setTimeout(() => inputRef.current?.focus(), 30);
    }
  }, [open, currentQuery]);

  const items = useMemo(() => {
    const list = [];
    const trimmed = q.trim();
    if (trimmed) {
      list.push({ kind:"run", label:`Search clauses for "${trimmed}"`, kbd:"↵", action:() => onRunQuery(trimmed) });
      list.push({ kind:"paste", label:`Paste as draft clause → find similar`, kbd:"⇧↵", action:() => onPasteMatch(trimmed) });
      // scoped
      const lower = trimmed.toLowerCase();
      const matchedFams = window.FAMILIES.filter(([k,l]) => lower.split(/\s+/).some(t => k.includes(t) || l.toLowerCase().includes(t))).slice(0,2);
      matchedFams.forEach(([k,l]) => {
        list.push({ kind:"scoped-fam", label:`Search only ${l}`, kbd:"", action:() => onRunQuery(trimmed, { family:[k] }) });
      });
      if (/\b(ny|new york)\b/i.test(trimmed)) list.push({ kind:"scoped-law", label:`Scope to New York governing law`, action:() => onRunQuery(trimmed, { law:["New York"] }) });
      if (/\b(ca|california)\b/i.test(trimmed)) list.push({ kind:"scoped-law", label:`Scope to California governing law`, action:() => onRunQuery(trimmed, { law:["California"] }) });
    } else {
      // No query — show families to browse
      window.FAMILIES.slice(0,6).forEach(([k,l]) => {
        list.push({ kind:"browse", label:`Browse ${l}`, action:() => onRunQuery("", { family:[k] }) });
      });
    }
    // Recent
    (recentQueries||[]).slice(0,3).forEach(r => {
      if (r !== trimmed) list.push({ kind:"recent", label:r, action:() => onRunQuery(r) });
    });
    return list;
  }, [q, recentQueries, onRunQuery, onPasteMatch]);

  useEffect(() => { setSel(s => Math.min(s, Math.max(0, items.length-1))); }, [items.length]);

  if (!open) return null;

  function onKey(e){
    if (e.key === "Escape") { e.preventDefault(); onClose(); return; }
    if (e.key === "ArrowDown") { e.preventDefault(); setSel(s => Math.min(items.length-1, s+1)); return; }
    if (e.key === "ArrowUp")   { e.preventDefault(); setSel(s => Math.max(0, s-1)); return; }
    if (e.key === "Enter") {
      e.preventDefault();
      const item = items[sel] || items[0];
      if (item) { item.action(); onClose(); }
    }
  }

  // group by kind for headers
  const groups = [];
  let last = null;
  items.forEach((it, i) => {
    const head = ({run:"Run query", paste:"Run query", "scoped-fam":"Scoped", "scoped-law":"Scoped", browse:"Browse", recent:"Recent"})[it.kind];
    if (head !== last) { groups.push({head, items:[]}); last = head; }
    groups[groups.length-1].items.push({...it, _i:i});
  });

  return (
    <div className="pal-scrim" onClick={onClose}>
      <div className="pal" onClick={e=>e.stopPropagation()}>
        <div className="pal-input">
          <span className="chev">&gt;</span>
          <input
            ref={inputRef}
            value={q}
            onChange={e=>setQ(e.target.value)}
            onKeyDown={onKey}
            placeholder="Describe the clause you want, or paste draft language…"
            className="pal-q"
          />
          <span className="kbd">esc</span>
        </div>
        <div className="pal-list">
          {groups.map((g, gi) => (
            <div className="pal-grp" key={gi}>
              {g.head && <h6>{g.head}</h6>}
              {g.items.map(it => (
                <div
                  key={it._i}
                  className={"pal-item" + (it._i===sel ? " sel":"")}
                  onMouseEnter={()=>setSel(it._i)}
                  onClick={()=>{ it.action(); onClose(); }}
                >
                  <span className="ic">
                    {it.kind==="run" && "⌕"}
                    {it.kind==="paste" && "¶"}
                    {it.kind==="scoped-fam" && "#"}
                    {it.kind==="scoped-law" && "§"}
                    {it.kind==="browse" && "▸"}
                    {it.kind==="recent" && "↻"}
                  </span>
                  <span className="lbl">{it.label}</span>
                  <span className="sp"></span>
                  {it.kbd && <span className="kbd">{it.kbd}</span>}
                </div>
              ))}
            </div>
          ))}
          {!items.length && (
            <div className="pal-grp"><div className="pal-item" style={{color:"var(--ink-3)"}}>No matches.</div></div>
          )}
        </div>
        <div className="pal-foot">
          <span><span className="kbd">↑</span> <span className="kbd">↓</span> navigate</span>
          <span><span className="kbd">↵</span> select</span>
          <span style={{flex:1}}></span>
          <span>ClauseIQ · palette</span>
        </div>
      </div>
    </div>
  );
}

window.CommandPalette = CommandPalette;
