// ClauseIQ prototype — fake corpus + naive retrieval.
// Good-enough to feel real, not a benchmark.

const CONTRACTS = [
  { id:"acme",     title:"Acme SaaS MSA",          counterparty:"Acme Corp",        signed:"2023-06-14", law:"New York",   pages:38 },
  { id:"globex",   title:"Globex Master Agreement", counterparty:"Globex Inc.",      signed:"2024-02-20", law:"New York",   pages:42 },
  { id:"initech",  title:"Initech Services MSA",   counterparty:"Initech LLC",      signed:"2022-11-03", law:"New York",   pages:31 },
  { id:"hooli",    title:"Hooli Platform MSA",     counterparty:"Hooli",            signed:"2023-09-09", law:"California", pages:54 },
  { id:"piedpiper",title:"Pied Piper SaaS MSA",    counterparty:"Pied Piper",       signed:"2024-01-15", law:"New York",   pages:27 },
  { id:"sterling", title:"Sterling Cooper MSA",    counterparty:"Sterling Cooper",  signed:"2023-03-30", law:"Delaware",   pages:36 },
  { id:"vandelay", title:"Vandelay Industries MSA",counterparty:"Vandelay Ind.",    signed:"2022-08-22", law:"New York",   pages:29 },
  { id:"dunder",   title:"Dunder Mifflin SaaS",    counterparty:"Dunder Mifflin",   signed:"2024-05-04", law:"Pennsylvania", pages:33 },
];

const FAMILIES = [
  ["limitation_of_liability","Limitation of liability"],
  ["indemnification",        "Indemnification"],
  ["confidentiality",        "Confidentiality"],
  ["termination",            "Termination"],
  ["payment_terms",          "Payment terms"],
  ["fees_pricing",           "Fees & pricing"],
  ["term_renewal",           "Term & renewal"],
  ["warranties",             "Warranties & disclaimers"],
  ["governing_law",          "Governing law"],
  ["assignment",             "Assignment"],
  ["force_majeure",          "Force majeure"],
  ["data_security",          "Data security"],
];

const CLAUSES = [
  // Limitation of liability
  { id:"cl_001", contract:"initech", section:"§8.2", title:"Cap at 12 months of fees", family:"limitation_of_liability",
    text:"Except for breaches of confidentiality or indemnification obligations, each party's total aggregate liability arising out of or relating to this Agreement shall not exceed the fees paid by Customer in the twelve (12) months preceding the event giving rise to the claim.",
    article:"Article 8 — Warranties & Liability", pages:"14–15" },
  { id:"cl_002", contract:"acme", section:"§8.3", title:"Liability cap with IP indemnity carve-out", family:"limitation_of_liability",
    text:"Notwithstanding the foregoing, the liability cap in Section 8.2 shall not apply to (i) a party's indemnification obligations for third-party intellectual property claims, (ii) breaches of confidentiality, or (iii) a party's gross negligence or willful misconduct.",
    article:"Article 8 — Liability", pages:"19" },
  { id:"cl_003", contract:"globex", section:"§9.1", title:"Mutual liability cap, greater-of formula", family:"limitation_of_liability",
    text:"Each party's aggregate liability under this Agreement shall not exceed the greater of (a) twelve (12) months of fees paid by Customer in the twelve months preceding the claim or (b) five hundred thousand dollars ($500,000).",
    article:"Article 9 — Liability", pages:"22–23" },
  { id:"cl_004", contract:"piedpiper", section:"§7.4", title:"Exclusion of indirect damages", family:"limitation_of_liability",
    text:"In no event shall either party be liable for any indirect, incidental, special, consequential, or punitive damages, including loss of profits, data, or goodwill, even if advised of the possibility of such damages.",
    article:"Article 7 — Liability", pages:"12" },
  { id:"cl_005", contract:"sterling", section:"§8.4", title:"Super-cap for gross negligence", family:"limitation_of_liability",
    text:"The liability cap set forth in Section 8.2 shall be increased to three (3) times the fees paid in the prior twelve months for claims arising out of a party's gross negligence or willful misconduct.",
    article:"Article 8 — Liability", pages:"17" },
  { id:"cl_006", contract:"hooli", section:"§8.5", title:"Uncapped obligations carve-out", family:"limitation_of_liability",
    text:"Nothing in this Agreement shall limit a party's liability for (a) fraud or fraudulent misrepresentation; (b) death or personal injury caused by negligence; (c) breaches of Section 11 (Confidentiality); or (d) payment of undisputed fees.",
    article:"Article 8 — Liability", pages:"24" },
  { id:"cl_007", contract:"vandelay", section:"§8.1", title:"Single-party cap (vendor only)", family:"limitation_of_liability",
    text:"Vendor's total aggregate liability shall not exceed the fees paid by Customer in the twelve (12) months preceding the claim. Customer's liability shall be uncapped for amounts owed for services rendered under any Order Form.",
    article:"Article 8 — Liability", pages:"15" },

  // Termination
  { id:"cl_010", contract:"acme", section:"§9.2", title:"Termination for material breach (30-day cure)", family:"termination",
    text:"Either party may terminate this Agreement for material breach by the other party upon thirty (30) days' written notice, provided that the breaching party shall have such thirty (30) day period to cure the breach to the reasonable satisfaction of the non-breaching party.",
    article:"Article 9 — Term & Termination", pages:"20" },
  { id:"cl_011", contract:"globex", section:"§11.3", title:"Termination for convenience (60 days)", family:"termination",
    text:"Customer may terminate this Agreement for convenience upon sixty (60) days' prior written notice to Vendor, with no early termination fee.",
    article:"Article 11 — Termination", pages:"26" },
  { id:"cl_012", contract:"hooli", section:"§5.4", title:"Termination on insolvency", family:"termination",
    text:"Either party may terminate this Agreement immediately upon written notice if the other party becomes insolvent, makes a general assignment for the benefit of creditors, or files a petition in bankruptcy.",
    article:"Article 5 — Term & Termination", pages:"15" },
  { id:"cl_013", contract:"dunder", section:"§10.2", title:"Effect of termination — survival", family:"termination",
    text:"Upon termination of this Agreement, the following provisions shall survive: Sections 8 (Confidentiality), 9 (Limitation of Liability), 12 (Indemnification), and any payment obligations accrued prior to termination.",
    article:"Article 10 — Termination", pages:"22" },

  // Confidentiality
  { id:"cl_020", contract:"acme", section:"§11.1", title:"Confidentiality with 5-year survival", family:"confidentiality",
    text:"Each party shall hold in confidence all Confidential Information disclosed by the other party and shall not use such information except as required to perform this Agreement. The obligations under this Section shall survive for five (5) years following termination of this Agreement.",
    article:"Article 11 — Confidentiality", pages:"28" },
  { id:"cl_021", contract:"globex", section:"§11.2", title:"Mutual NDA-style confidentiality", family:"confidentiality",
    text:"Each Party shall use the same degree of care to protect the other Party's Confidential Information as it uses to protect its own, but in no event less than reasonable care. This obligation shall survive for a period of three (3) years.",
    article:"Article 11 — Confidentiality", pages:"30" },
  { id:"cl_022", contract:"initech", section:"§10.1", title:"Perpetual obligation for trade secrets", family:"confidentiality",
    text:"The confidentiality obligations under this Section shall survive for five (5) years, provided that with respect to trade secrets, such obligation shall continue for as long as the information qualifies as a trade secret under applicable law.",
    article:"Article 10 — Confidentiality", pages:"21" },

  // Payment / fees
  { id:"cl_030", contract:"acme", section:"§4.1", title:"Net-30 payment terms", family:"payment_terms",
    text:"Customer shall pay all undisputed invoices within thirty (30) days of receipt. Late payments shall accrue interest at the lesser of 1.5% per month or the maximum rate permitted by law.",
    article:"Article 4 — Fees & Payment", pages:"8" },
  { id:"cl_031", contract:"globex", section:"§3.1", title:"Subscription fees", family:"fees_pricing",
    text:"Customer shall pay Vendor subscription fees as set forth in the applicable Order Form. Subscription fees are non-refundable except as expressly provided herein.",
    article:"Article 3 — Fees", pages:"7" },
  { id:"cl_032", contract:"hooli", section:"§3.4", title:"Annual price increase cap (5%)", family:"fees_pricing",
    text:"Vendor may increase fees upon renewal by no more than five percent (5%) over the fees in the prior term, provided Vendor gives Customer at least sixty (60) days' written notice prior to renewal.",
    article:"Article 3 — Fees", pages:"9" },

  // Term & renewal
  { id:"cl_040", contract:"hooli", section:"§5.1", title:"36-month initial term, 12-month auto-renewal", family:"term_renewal",
    text:"The initial term of this Agreement shall be thirty-six (36) months from the Effective Date. Thereafter, this Agreement shall automatically renew for successive twelve (12) month terms unless either party gives written notice of non-renewal at least sixty (60) days prior to the end of the then-current term.",
    article:"Article 5 — Term", pages:"12" },
  { id:"cl_041", contract:"acme", section:"§2.1", title:"Initial 1-year term, opt-in renewal", family:"term_renewal",
    text:"The initial term of this Agreement is one (1) year. Renewal shall require mutual written agreement of the parties; this Agreement shall not auto-renew.",
    article:"Article 2 — Term", pages:"4" },

  // Indemnification
  { id:"cl_050", contract:"acme", section:"§10.1", title:"Vendor IP indemnification", family:"indemnification",
    text:"Vendor shall defend, indemnify, and hold harmless Customer from and against any third-party claim alleging that the Service infringes or misappropriates such third party's intellectual property rights, and shall pay any damages finally awarded against Customer.",
    article:"Article 10 — Indemnification", pages:"24" },
  { id:"cl_051", contract:"globex", section:"§10.2", title:"Customer indemnification for misuse", family:"indemnification",
    text:"Customer shall indemnify Vendor against any third-party claim arising from Customer's use of the Service in violation of this Agreement or applicable law, including misuse of Customer Data.",
    article:"Article 10 — Indemnification", pages:"25" },

  // Warranties
  { id:"cl_060", contract:"initech", section:"§7.1", title:"Service warranty (30 days)", family:"warranties",
    text:"Vendor warrants that the Service will perform substantially in accordance with the Documentation for a period of thirty (30) days following the Effective Date. Customer's exclusive remedy for breach of this warranty shall be re-performance or, if Vendor cannot re-perform, refund of fees paid for the affected Service.",
    article:"Article 7 — Warranties", pages:"13" },
  { id:"cl_061", contract:"vandelay", section:"§7.2", title:"As-is disclaimer", family:"warranties",
    text:"EXCEPT AS EXPRESSLY SET FORTH HEREIN, THE SERVICE IS PROVIDED \"AS IS\" AND VENDOR DISCLAIMS ALL OTHER WARRANTIES, EXPRESS OR IMPLIED, INCLUDING ANY WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.",
    article:"Article 7 — Warranties", pages:"14" },

  // Governing law
  { id:"cl_070", contract:"acme", section:"§14.1", title:"NY law, SDNY venue", family:"governing_law",
    text:"This Agreement shall be governed by the laws of the State of New York, without regard to its conflict of laws principles. The parties consent to the exclusive jurisdiction of the state and federal courts located in New York County, New York.",
    article:"Article 14 — General", pages:"35" },
  { id:"cl_071", contract:"hooli", section:"§14.1", title:"California law, JAMS arbitration", family:"governing_law",
    text:"This Agreement shall be governed by the laws of the State of California. Any dispute arising under this Agreement shall be resolved by binding arbitration administered by JAMS in San Francisco, California.",
    article:"Article 14 — General", pages:"50" },

  // Assignment
  { id:"cl_080", contract:"globex", section:"§13.1", title:"No assignment without consent (M&A carve-out)", family:"assignment",
    text:"Neither party may assign this Agreement without the prior written consent of the other party, except that either party may assign this Agreement to a successor in interest in connection with a merger, acquisition, or sale of all or substantially all of its assets, upon written notice.",
    article:"Article 13 — General", pages:"38" },

  // Force majeure
  { id:"cl_090", contract:"sterling", section:"§14.5", title:"Standard force majeure", family:"force_majeure",
    text:"Neither party shall be liable for any failure or delay in performance under this Agreement to the extent such failure or delay is caused by circumstances beyond its reasonable control, including acts of God, war, terrorism, pandemic, government action, or failure of utilities or telecommunications.",
    article:"Article 14 — General", pages:"32" },

  // Data security
  { id:"cl_100", contract:"hooli", section:"§12.1", title:"SOC 2 + breach notification (72 hrs)", family:"data_security",
    text:"Vendor shall maintain a SOC 2 Type II certified information security program and shall notify Customer of any confirmed Security Incident affecting Customer Data within seventy-two (72) hours of discovery.",
    article:"Article 12 — Security", pages:"40" },
  { id:"cl_101", contract:"dunder", section:"§9.3", title:"Encryption in transit and at rest", family:"data_security",
    text:"Vendor shall encrypt all Customer Data in transit using TLS 1.2 or higher and at rest using AES-256 or equivalent industry-standard encryption.",
    article:"Article 9 — Security", pages:"19" },
];

// --- Naive but plausible retrieval -----------------------------------------
const STOP = new Set("a an the of for to and or in on at by with from as is be are this that".split(" "));

function tokenize(s){ return (s||"").toLowerCase().match(/[a-z0-9]+/g)?.filter(t=>!STOP.has(t)&&t.length>1) || []; }

// Synonym boosts so "cap on liability" matches "aggregate liability"
const SYNONYMS = {
  cap:["aggregate","limit","limited","capped"],
  liability:["liable","damages"],
  fees:["fee","payment","paid"],
  twelve:["12"],
  months:["month","mo"],
  ip:["intellectual","property"],
  carve:["exclusion","exclude"],
  termination:["terminate","terminated"],
  breach:["material","breached"],
  cure:["period"],
  convenience:["without","cause"],
  confidentiality:["confidential","nda"],
  renewal:["renew","auto"],
  notice:["written"],
};

function expandedTokens(q){
  const base = tokenize(q);
  const out = new Set(base);
  base.forEach(t => (SYNONYMS[t]||[]).forEach(s => out.add(s)));
  return [...out];
}

function scoreClause(clause, qTokens){
  const text = (clause.text + " " + clause.title).toLowerCase();
  let s = 0, matched = new Set();
  qTokens.forEach(t => {
    const re = new RegExp("\\b" + t + "\\b", "g");
    const m = text.match(re);
    if (m) { s += m.length * (t.length>3?1.4:1); matched.add(t); }
  });
  // Family hint: if query contains family token, big boost
  const fam = clause.family.replace(/_/g," ");
  qTokens.forEach(t => { if (fam.includes(t)) s += 2; });
  // Length-normalize lightly
  s = s / (1 + Math.log(text.length/200));
  return { score: s, matched: [...matched] };
}

function search(query, filters){
  const qTokens = expandedTokens(query);
  let candidates = CLAUSES;
  if (filters.family && filters.family.length) {
    candidates = candidates.filter(c => filters.family.includes(c.family));
  }
  if (filters.law && filters.law.length) {
    candidates = candidates.filter(c => {
      const ct = CONTRACTS.find(x => x.id===c.contract);
      return ct && filters.law.includes(ct.law);
    });
  }
  if (filters.counterparty && filters.counterparty.length) {
    candidates = candidates.filter(c => {
      const ct = CONTRACTS.find(x => x.id===c.contract);
      return ct && filters.counterparty.includes(ct.counterparty);
    });
  }
  if (!query.trim() && (!filters.family || !filters.family.length) && (!filters.law||!filters.law.length) && (!filters.counterparty||!filters.counterparty.length)) {
    return [];
  }
  const scored = candidates.map(c => {
    const { score, matched } = qTokens.length ? scoreClause(c, qTokens) : { score: 1, matched: [] };
    const ct = CONTRACTS.find(x => x.id===c.contract);
    const norm = Math.min(0.99, 0.55 + score/8);
    return { clause:c, contract:ct, score: query.trim() ? norm : 0.5, matched };
  });
  let results = qTokens.length ? scored.filter(r => r.score > 0.55) : scored;
  results.sort((a,b)=>b.score-a.score);
  return results.slice(0, 20);
}

function highlight(text, tokens){
  if (!tokens || !tokens.length) return [{text, hit:false}];
  const re = new RegExp("\\b(" + tokens.map(t=>t.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")).join("|") + ")\\b","gi");
  const parts = [];
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push({text: text.slice(last, m.index), hit:false});
    parts.push({text: m[0], hit:true});
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push({text: text.slice(last), hit:false});
  return parts;
}

function familyLabel(token){ return (FAMILIES.find(f=>f[0]===token)||[token,token])[1]; }

function familyCounts(){
  const out = {};
  FAMILIES.forEach(([k])=>out[k]=0);
  CLAUSES.forEach(c => { out[c.family] = (out[c.family]||0)+1; });
  return out;
}
function lawCounts(){
  const out = {};
  CLAUSES.forEach(c => {
    const ct = CONTRACTS.find(x=>x.id===c.contract);
    if (ct) out[ct.law] = (out[ct.law]||0)+1;
  });
  return out;
}
function counterpartyCounts(){
  const out = {};
  CLAUSES.forEach(c => {
    const ct = CONTRACTS.find(x=>x.id===c.contract);
    if (ct) out[ct.counterparty] = (out[ct.counterparty]||0)+1;
  });
  return out;
}

Object.assign(window, {
  CONTRACTS, CLAUSES, FAMILIES,
  search, highlight, expandedTokens,
  familyLabel, familyCounts, lawCounts, counterpartyCounts,
});
