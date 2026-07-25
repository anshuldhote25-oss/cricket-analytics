import { useState, useRef, useEffect } from "react";

const DARK = "#0A0E1A";
const SURFACE = "#111827";
const CARD = "#1A2235";
const BORDER = "#243050";
const AMBER = "#F59E0B";
const AMBER_DIM = "#D97706";
const AMBER_BRIGHT = "#FCD34D";
const TEAL = "#14B8A6";
const PURPLE = "#A78BFA";
const CORAL = "#F87171";
const SKY = "#38BDF8";
const GREEN = "#4ADE80";
const TEXT = "#F1F5F9";
const MUTED = "#64748B";
const DIM = "#94A3B8";

const css = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: ${DARK}; font-family: 'Inter','Segoe UI',system-ui,sans-serif; }
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: ${BORDER}; border-radius: 2px; }
  textarea { font-family: inherit; }
  @keyframes blink { 0%,100%{opacity:.3} 50%{opacity:1} }
  @keyframes slidein { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
  @keyframes shimmer { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
  .msg-in { animation: slidein 0.2s ease; }
  .pill-btn:hover { background: ${BORDER} !important; color: ${TEXT} !important; }
  .send:hover:not(:disabled) { background: #B45309 !important; }
  .icon-btn:hover { background: ${BORDER} !important; }
  .db-row:hover { background: rgba(245,158,11,0.05) !important; }
  .ex-card:hover { border-color: ${AMBER} !important; background: rgba(245,158,11,0.06) !important; transform: translateY(-1px); transition: all 0.15s; }
`;

const VIEWS = [
  { key: "batting_summary", label: "Batting", icon: "🏏", color: AMBER, desc: "Runs, strike rate, boundaries" },
  { key: "bowling_summary", label: "Bowling", icon: "⚾", color: TEAL, desc: "Wickets, economy, averages" },
  { key: "phase_batting", label: "Phase batting", icon: "📊", color: PURPLE, desc: "Stats by powerplay / middle / death" },
  { key: "phase_bowling", label: "Phase bowling", icon: "📈", color: SKY, desc: "Bowling stats by phase" },
  { key: "fielding_summary", label: "Fielding", icon: "🧤", color: GREEN, desc: "Catches, stumpings, run outs" },
  { key: "bowler_discipline", label: "Discipline", icon: "🎯", color: CORAL, desc: "Wides, no balls, extras" },
];

const EXAMPLES = [
  { q: "Top 10 T20 batters by strike rate", color: AMBER, icon: "🏏" },
  { q: "Best economy bowlers in the powerplay", color: TEAL, icon: "⚾" },
  { q: "Top U19 female batters by total runs", color: PURPLE, icon: "👩" },
  { q: "Who took the most catches this season?", color: GREEN, icon: "🧤" },
  { q: "Best leg-spin bowlers in SMAT by wickets", color: SKY, icon: "🌀" },
  { q: "Which teams give the most wides?", color: CORAL, icon: "⚠️" },
];

function Dots() {
  return (
    <div style={{ display: "flex", gap: 5, alignItems: "center", padding: "10px 14px" }}>
      {[AMBER, TEAL, PURPLE].map((c, i) => (
        <div key={i} style={{
          width: 7, height: 7, borderRadius: "50%", background: c,
          animation: `blink 1.2s ${i * 0.2}s ease-in-out infinite`
        }} />
      ))}
    </div>
  );
}

function DataBrowser({ onClose, onAsk }) {
  const [activeView, setActiveView] = useState(VIEWS[0]);
  const [rows, setRows] = useState([]);
  const [cols, setCols] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("");

  const loadView = async (view) => {
    setActiveView(view);
    setLoading(true);
    setFilter("");
    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: `Show me all data from ${view.key} limit 50` }),
      });
      const data = await res.json();
      if (data.success && data.rows?.length) { setCols(data.columns); setRows(data.rows); }
      else { setCols([]); setRows([]); }
    } catch { setCols([]); setRows([]); }
    setLoading(false);
  };

  useEffect(() => { loadView(VIEWS[0]); }, []);

  const filtered = filter
    ? rows.filter(r => Object.values(r).some(v => String(v ?? "").toLowerCase().includes(filter.toLowerCase())))
    : rows;

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.8)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100 }}>
      <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, width: "92vw", maxWidth: 1000, height: "84vh", display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div style={{ padding: "14px 18px", borderBottom: `1px solid ${BORDER}`, display: "flex", alignItems: "center", gap: 12, background: CARD }}>
          <span style={{ fontSize: 20 }}>🗃</span>
          <div>
            <div style={{ color: TEXT, fontWeight: 700, fontSize: 14 }}>Database browser</div>
            <div style={{ color: MUTED, fontSize: 11 }}>Browse views and raw data directly</div>
          </div>
          <input placeholder="Filter rows..." value={filter} onChange={e => setFilter(e.target.value)}
            style={{ marginLeft: "auto", background: DARK, border: `1px solid ${BORDER}`, borderRadius: 8, color: TEXT, padding: "6px 12px", fontSize: 13, outline: "none", width: 200 }} />
          <button onClick={onClose} className="icon-btn" style={{ background: "none", border: `1px solid ${BORDER}`, borderRadius: 8, color: MUTED, padding: "5px 10px", cursor: "pointer", fontSize: 20, lineHeight: 1 }}>×</button>
        </div>

        <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
          <div style={{ width: 200, borderRight: `1px solid ${BORDER}`, padding: "10px 8px", overflowY: "auto", flexShrink: 0, background: CARD }}>
            <div style={{ fontSize: 10, color: MUTED, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", padding: "4px 8px 10px" }}>Analytics views</div>
            {VIEWS.map(v => (
              <button key={v.key} onClick={() => loadView(v)} style={{
                width: "100%", display: "flex", alignItems: "center", gap: 9,
                background: activeView.key === v.key ? `${v.color}15` : "transparent",
                border: activeView.key === v.key ? `1px solid ${v.color}40` : "1px solid transparent",
                borderRadius: 8, padding: "8px 10px", cursor: "pointer", textAlign: "left", marginBottom: 3
              }}>
                <span style={{ fontSize: 18 }}>{v.icon}</span>
                <div>
                  <div style={{ color: activeView.key === v.key ? v.color : TEXT, fontSize: 13, fontWeight: 600 }}>{v.label}</div>
                  <div style={{ color: MUTED, fontSize: 10, lineHeight: 1.3, marginTop: 1 }}>{v.desc}</div>
                </div>
              </button>
            ))}
            <div style={{ borderTop: `1px solid ${BORDER}`, margin: "10px 8px 8px", paddingTop: 10 }}>
              <div style={{ fontSize: 10, color: MUTED, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 8 }}>Quick ask</div>
              {["Top batters this season", "Best economy bowlers", "Most catches taken"].map((q, i) => (
                <button key={i} onClick={() => { onClose(); onAsk(q); }} style={{
                  width: "100%", background: "none", border: `1px solid ${BORDER}`,
                  borderRadius: 6, color: MUTED, fontSize: 11, padding: "5px 8px",
                  cursor: "pointer", textAlign: "left", marginBottom: 4
                }}>→ {q}</button>
              ))}
            </div>
          </div>

          <div style={{ flex: 1, overflow: "auto", padding: 16 }}>
            {loading ? (
              <div style={{ color: MUTED, fontSize: 13, padding: 20, display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ color: activeView.color }}>{activeView.icon}</span> Loading {activeView.label}...
              </div>
            ) : filtered.length === 0 ? (
              <div style={{ color: MUTED, fontSize: 13, padding: 20 }}>No rows found.</div>
            ) : (
              <>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                  <span style={{ fontSize: 16 }}>{activeView.icon}</span>
                  <span style={{ color: activeView.color, fontWeight: 600, fontSize: 13 }}>{activeView.label}</span>
                  <span style={{ color: MUTED, fontSize: 12 }}>— {filtered.length} rows</span>
                </div>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                  <thead>
                    <tr>
                      {cols.map(c => (
                        <th key={c} style={{ background: DARK, color: MUTED, fontWeight: 700, fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em", padding: "7px 10px", textAlign: "left", whiteSpace: "nowrap", position: "sticky", top: 0, borderBottom: `1px solid ${BORDER}` }}>
                          {c.replace(/_/g, " ")}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((row, i) => (
                      <tr key={i} className="db-row" style={{ borderBottom: `1px solid ${BORDER}` }}>
                        {cols.map(c => (
                          <td key={c} style={{ padding: "6px 10px", color: typeof row[c] === "number" ? activeView.color : TEXT, whiteSpace: "nowrap" }}>
                            {row[c] === null || row[c] === undefined ? <span style={{ color: MUTED }}>—</span> : String(row[c])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ResultTable({ cols, rows }) {
  if (!rows?.length) return null;
  return (
    <div style={{ overflowX: "auto", marginTop: 10, borderRadius: 8, border: `1px solid ${BORDER}` }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
        <thead>
          <tr>
            <th style={{ background: DARK, color: MUTED, fontWeight: 700, fontSize: 10, textTransform: "uppercase", letterSpacing: "0.07em", padding: "7px 10px", textAlign: "center", width: 36 }}>#</th>
            {cols.map(c => (
              <th key={c} style={{ background: DARK, color: MUTED, fontWeight: 700, fontSize: 10, textTransform: "uppercase", letterSpacing: "0.07em", padding: "7px 10px", textAlign: "left", whiteSpace: "nowrap" }}>
                {c.replace(/_/g, " ")}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => {
            const rankColors = [AMBER_BRIGHT, DIM, "#CD7F32"];
            const rankColor = i < 3 ? rankColors[i] : MUTED;
            return (
              <tr key={i} style={{ borderTop: `1px solid ${BORDER}`, background: i % 2 ? "rgba(255,255,255,0.01)" : "transparent" }}>
                <td style={{ padding: "7px 10px", color: rankColor, fontWeight: 700, textAlign: "center", fontSize: i < 3 ? 14 : 12 }}>
                  {i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : i + 1}
                </td>
                {cols.map((c, ci) => (
                  <td key={c} style={{ padding: "7px 10px", color: ci === 0 ? TEXT : typeof row[c] === "number" ? TEAL : DIM, whiteSpace: "nowrap", fontWeight: ci === 0 ? 500 : 400 }}>
                    {row[c] === null || row[c] === undefined ? <span style={{ color: MUTED }}>—</span> : String(row[c])}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Message({ msg }) {
  const [showSql, setShowSql] = useState(false);

  if (msg.type === "user") return (
    <div className="msg-in" style={{ display: "flex", justifyContent: "flex-end", marginBottom: 14 }}>
      <div style={{ background: `linear-gradient(135deg, ${AMBER_DIM}, #92400E)`, color: "#fff", borderRadius: "14px 14px 3px 14px", padding: "9px 15px", fontSize: 14, maxWidth: 520 }}>
        {msg.text}
      </div>
    </div>
  );

  if (msg.type === "thinking") return (
    <div className="msg-in" style={{ marginBottom: 14 }}>
      <div style={{ background: CARD, border: `1px solid ${BORDER}`, borderRadius: "3px 14px 14px 14px", display: "inline-block" }}>
        <Dots />
      </div>
    </div>
  );

  return (
    <div className="msg-in" style={{ marginBottom: 18 }}>
      <div style={{ background: CARD, border: `1px solid ${BORDER}`, borderRadius: "3px 14px 14px 14px", padding: "14px 16px", maxWidth: 820 }}>
        {msg.success ? (
          <>
            <div style={{ color: GREEN, fontSize: 13.5, marginBottom: msg.assumptions ? 4 : 10, display: "flex", alignItems: "flex-start", gap: 7 }}>
              <span style={{ marginTop: 1, flexShrink: 0 }}>✓</span>
              <span style={{ color: TEXT }}>{msg.explanation}</span>
            </div>
            {msg.assumptions && <div style={{ color: MUTED, fontSize: 12, fontStyle: "italic", marginBottom: 10, paddingLeft: 20 }}>ℹ {msg.assumptions}</div>}
            {msg.rows?.length > 0
              ? <ResultTable cols={msg.columns} rows={msg.rows} />
              : <div style={{ color: MUTED, fontSize: 13, marginTop: 6 }}>No results found. Try relaxing the filters.</div>
            }
            {msg.rows?.length > 0 && <div style={{ color: MUTED, fontSize: 11, marginTop: 6 }}>{msg.row_count} result{msg.row_count !== 1 ? "s" : ""}</div>}
            {msg.sql && (
              <>
                <button onClick={() => setShowSql(s => !s)} style={{ background: "none", border: "none", color: MUTED, fontSize: 11, cursor: "pointer", marginTop: 6, padding: 0 }}>
                  {showSql ? "▲ hide SQL" : "▼ show SQL"}
                </button>
                {showSql && <pre style={{ background: "#0D1117", border: `1px solid ${BORDER}`, borderRadius: 6, padding: "10px 12px", fontSize: 11.5, color: "#7DD3FC", overflowX: "auto", marginTop: 6, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>{msg.sql}</pre>}
              </>
            )}
          </>
        ) : (
          <div style={{ color: CORAL, fontSize: 13, display: "flex", gap: 6 }}>
            <span>✗</span>{msg.explanation || msg.error || "Something went wrong. Please try again."}
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showDB, setShowDB] = useState(false);
  const [showExamples, setShowExamples] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const sendQuestion = async (q) => {
    if (!q?.trim() || loading) return;
    const question = q.trim();
    setInput(""); setShowExamples(false);
    setMessages(prev => [...prev, { type: "user", text: question }, { type: "thinking" }]);
    setLoading(true);
    try {
      const res = await fetch("/api/query", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      const data = await res.json();
      setMessages(prev => [...prev.filter(m => m.type !== "thinking"), { type: "assistant", ...data }]);
    } catch {
      setMessages(prev => [...prev.filter(m => m.type !== "thinking"), { type: "assistant", success: false, explanation: "Connection error. Make sure the server is running." }]);
    }
    setLoading(false);
    setTimeout(() => inputRef.current?.focus(), 100);
  };

  return (
    <>
      <style>{css}</style>
      {showDB && <DataBrowser onClose={() => setShowDB(false)} onAsk={sendQuestion} />}

      <div style={{ height: "100vh", display: "flex", flexDirection: "column", background: DARK, color: TEXT }}>

        {/* Header */}
        <header style={{ background: SURFACE, borderBottom: `1px solid ${BORDER}`, padding: "0 20px", height: 54, display: "flex", alignItems: "center", gap: 14, flexShrink: 0 }}>
          <div style={{ width: 34, height: 34, background: `linear-gradient(135deg, ${AMBER_DIM}, #92400E)`, borderRadius: 9, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>🏏</div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, color: TEXT, letterSpacing: "-0.01em" }}>Cricket Analytics</div>
            <div style={{ fontSize: 11, color: MUTED }}>AI scouting platform</div>
          </div>

          {/* Format pills */}
          <div style={{ display: "flex", gap: 6, marginLeft: 20 }}>
            {["T20", "ODI", "First Class"].map((f, i) => (
              <span key={f} style={{ background: [AMBER, TEAL, PURPLE][i] + "20", border: `1px solid ${[AMBER, TEAL, PURPLE][i]}40`, color: [AMBER, TEAL, PURPLE][i], borderRadius: 20, fontSize: 11, fontWeight: 600, padding: "3px 10px" }}>{f}</span>
            ))}
          </div>

          <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
            <button className="icon-btn" onClick={() => setShowDB(true)} style={{
              background: `${AMBER}15`, border: `1px solid ${AMBER}40`, borderRadius: 8,
              color: AMBER, fontSize: 12, fontWeight: 600, padding: "6px 14px", cursor: "pointer",
              display: "flex", alignItems: "center", gap: 6
            }}>
              🗃 Browse data
            </button>
            <button className="icon-btn" onClick={() => setMessages([])} style={{
              background: "none", border: `1px solid ${BORDER}`, borderRadius: 8,
              color: MUTED, fontSize: 12, padding: "6px 12px", cursor: "pointer"
            }}>Clear</button>
          </div>
        </header>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "24px 20px" }}>
          <div style={{ maxWidth: 860, margin: "0 auto" }}>

            {messages.length === 0 && (
              <div style={{ textAlign: "center", marginTop: 50 }}>
                <div style={{ fontSize: 52, marginBottom: 14 }}>🏏</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: TEXT, marginBottom: 8, letterSpacing: "-0.02em" }}>
                  Ask anything about the data
                </div>
                <div style={{ fontSize: 14, color: MUTED, maxWidth: 420, margin: "0 auto 32px", lineHeight: 1.7 }}>
                  Player performance, match stats, fielding, bowling discipline — ask in plain English and get instant answers.
                </div>

                {/* Stat bar */}
                <div style={{ display: "flex", justifyContent: "center", gap: 24, marginBottom: 36 }}>
                  {[
                    { val: "235", label: "Players", color: AMBER },
                    { val: "88", label: "Matches", color: TEAL },
                    { val: "19.5K", label: "Deliveries", color: PURPLE },
                    { val: "11", label: "Tournaments", color: CORAL },
                  ].map(s => (
                    <div key={s.label} style={{ textAlign: "center" }}>
                      <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.val}</div>
                      <div style={{ fontSize: 11, color: MUTED }}>{s.label}</div>
                    </div>
                  ))}
                </div>

                {/* Example cards */}
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, maxWidth: 680, margin: "0 auto" }}>
                  {EXAMPLES.map((ex, i) => (
                    <button key={i} onClick={() => sendQuestion(ex.q)} className="ex-card" style={{
                      background: CARD, border: `1px solid ${BORDER}`, borderRadius: 12,
                      color: TEXT, fontSize: 13, padding: "12px 14px", cursor: "pointer",
                      textAlign: "left", lineHeight: 1.4, display: "flex", flexDirection: "column", gap: 6
                    }}>
                      <span style={{ fontSize: 18 }}>{ex.icon}</span>
                      <span style={{ color: ex.color, fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em" }}>Ask →</span>
                      <span>{ex.q}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => <Message key={i} msg={msg} />)}
            <div ref={bottomRef} />
          </div>
        </div>

        {/* Input bar */}
        <div style={{ borderTop: `1px solid ${BORDER}`, background: SURFACE, padding: "12px 20px" }}>
          <div style={{ maxWidth: 860, margin: "0 auto" }}>
            {messages.length > 0 && (
              <div style={{ marginBottom: 8 }}>
                <button onClick={() => setShowExamples(s => !s)} style={{ background: "none", border: "none", color: MUTED, fontSize: 12, cursor: "pointer", padding: 0 }}>
                  {showExamples ? "▲ hide examples" : "▼ quick examples"}
                </button>
                {showExamples && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                    {EXAMPLES.map((ex, i) => (
                      <button key={i} onClick={() => sendQuestion(ex.q)} className="pill-btn" style={{
                        background: `${ex.color}12`, border: `1px solid ${ex.color}30`,
                        borderRadius: 20, color: ex.color, fontSize: 12, padding: "4px 12px", cursor: "pointer"
                      }}>{ex.q}</button>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div style={{ display: "flex", gap: 10, alignItems: "flex-end" }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendQuestion(input); } }}
                placeholder="Ask a question… e.g. Top T20 batters by strike rate"
                rows={1}
                disabled={loading}
                style={{
                  flex: 1, background: CARD, border: `1px solid ${BORDER}`, borderRadius: 10,
                  color: TEXT, fontSize: 14, padding: "10px 14px", outline: "none",
                  resize: "none", minHeight: 44, maxHeight: 120, lineHeight: 1.5
                }}
              />
              <button
                className="send"
                onClick={() => sendQuestion(input)}
                disabled={loading || !input.trim()}
                style={{
                  background: `linear-gradient(135deg, ${AMBER_DIM}, #92400E)`,
                  border: "none", borderRadius: 10, color: "#fff",
                  fontSize: 13, fontWeight: 700, padding: "10px 20px", cursor: "pointer",
                  height: 44, flexShrink: 0,
                  opacity: loading || !input.trim() ? 0.4 : 1,
                  transition: "all 0.15s"
                }}
              >{loading ? "..." : "Ask →"}</button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
