"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_DEMO_API_KEY ?? "dev-local-key-do-not-use-in-prod";

const LABEL_CONFIG: Record<string, { color: string; bg: string; dot: string; label: string }> = {
  hate_speech:        { color: "#ff4d6d", bg: "rgba(255,77,109,0.08)",  dot: "#ff4d6d", label: "Hate Speech" },
  offensive_language: { color: "#ff8c42", bg: "rgba(255,140,66,0.08)",  dot: "#ff8c42", label: "Offensive Language" },
  distress_trigger:   { color: "#ffd166", bg: "rgba(255,209,102,0.08)", dot: "#ffd166", label: "Distress Trigger" },
  gaslighting:        { color: "#c77dff", bg: "rgba(199,125,255,0.08)", dot: "#c77dff", label: "Gaslighting" },
  manipulation:       { color: "#7c6aff", bg: "rgba(124,106,255,0.08)", dot: "#7c6aff", label: "Manipulation" },
  ambiguous:          { color: "#5a5a7a", bg: "rgba(90,90,122,0.08)",   dot: "#5a5a7a", label: "Ambiguous" },
  clean:              { color: "#00e5a0", bg: "rgba(0,229,160,0.08)",   dot: "#00e5a0", label: "Clean" },
};

const SEVERITY_LABEL = ["", "Minimal", "Low", "Moderate", "High", "Severe"];

const EXAMPLES = [
  { lang: "SW", text: "Wote Somali ni terrorists na wezi sana" },
  { lang: "SH", text: "Wewe ni mjinga kabisa, hujui kitu manze" },
  { lang: "EN", text: "You're just being too sensitive as always" },
  { lang: "MX", text: "Tutakukumbuka vizuri baada ya uchaguzi hii" },
];

const HOW_IT_WORKS = [
  { step: "01", title: "Submit text", desc: "Paste any text in Swahili, Sheng, English, or code-switched." },
  { step: "02", title: "Language detection", desc: "The system identifies the language automatically." },
  { step: "03", title: "ML classification", desc: "A trained classifier scores the text across 6 harm categories." },
  { step: "04", title: "Explainable result", desc: "Each prediction includes confidence, severity, and flagging for human review." },
];

const LANG_BADGES = [
  { code: "SW", name: "Swahili", status: "live",    color: "#00e5a0" },
  { code: "SH", name: "Sheng",   status: "beta",   color: "#ffd166" },
  { code: "EN", name: "English", status: "live",    color: "#00e5a0" },
  { code: "MX", name: "Mixed",   status: "live",    color: "#00e5a0" },
  { code: "LG", name: "Luganda", status: "planned", color: "#5a5a7a" },
  { code: "RW", name: "Kinyarwanda", status: "planned", color: "#5a5a7a" },
];

type Prediction = { label: string; confidence: number; severity: number | null };
type Result = {
  prediction_id: string; text: string; language_detected: string;
  predictions: Prediction[]; flagged_for_review: boolean;
  model_version: string; processing_time_ms: number;
};

export default function HomePage() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function analyze(inputText?: string) {
    const target = inputText ?? text;
    if (!target.trim()) return;
    setLoading(true); setResult(null); setError(null);
    try {
      const res = await fetch(`${API_URL}/v1/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
        body: JSON.stringify({ text: target }),
      });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail ?? `HTTP ${res.status}`); }
      setResult(await res.json());
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally { setLoading(false); }
  }

  const top = result?.predictions?.[0];

  return (
    <main style={{ maxWidth: "960px", margin: "0 auto", padding: "0 2rem 6rem" }}>

      {/* ── Hero ── */}
      <section className="afu" style={{ padding: "2.5rem 0 1.5rem", textAlign: "center" }}>

        {/* Live indicator */}
        <div style={{
          display: "inline-flex", alignItems: "center", gap: "7px",
          background: "var(--bg-card)", border: "1px solid var(--border)",
          borderRadius: "999px", padding: "5px 14px 5px 10px",
          fontSize: "12px", color: "var(--text-muted)",
          fontFamily: "var(--font-mono)", marginBottom: "2rem",
        }}>
          <span style={{
            width: "7px", height: "7px", borderRadius: "50%",
            background: "var(--accent)",
            animation: "pulse-dot 2s ease-in-out infinite",
            boxShadow: "0 0 6px var(--accent)",
            display: "inline-block",
          }} />
          LIVE · Kenya · v0.1
        </div>

        <h1 style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(1.8rem, 4vw, 3rem)",
          fontWeight: 800,
          letterSpacing: "-0.04em",
          lineHeight: 1.05,
          marginBottom: "1.5rem",
          color: "var(--text)",
        }}>
          Detect harmful speech<br />
          <span style={{
            background: "linear-gradient(135deg, var(--accent) 0%, var(--blue) 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}>in East African languages</span>
        </h1>

        <p style={{
          color: "var(--text-muted)", fontSize: "18px",
          maxWidth: "520px", margin: "0 auto 3rem",
          fontWeight: 300, lineHeight: 1.7,
        }}>
          Real-time AI detection of hate speech, manipulation, gaslighting,
          and distress-triggering content in Swahili, Sheng, and English.
        </p>

        {/* Language badges */}
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "8px", marginBottom: "3rem" }}>
          {LANG_BADGES.map(l => (
            <span key={l.code} style={{
              fontFamily: "var(--font-mono)", fontSize: "11px",
              padding: "4px 12px", borderRadius: "999px",
              border: `1px solid ${l.color}33`,
              background: `${l.color}0d`,
              color: l.color, letterSpacing: "0.05em",
            }}>
              {l.name}
              <span style={{ opacity: 0.5, marginLeft: "6px" }}>
                {l.status === "live" ? "●" : l.status === "beta" ? "◐" : "○"}
              </span>
            </span>
          ))}
        </div>
      </section>

      {/* ── Analyzer ── */}
      <section className="afu1" style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "16px", padding: "2rem",
        marginBottom: "5rem",
        animation: loading ? "glow-pulse 1.5s ease-in-out infinite" : "none",
      }}>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) analyze(); }}
          placeholder="Andika hapa... / Type here... / Andika Sheng..."
          rows={4}
          style={{
            width: "100%", background: "var(--bg-raised)",
            border: "1px solid var(--border)", borderRadius: "10px",
            padding: "1rem 1.25rem", color: "var(--text)",
            fontSize: "15px", lineHeight: 1.6, resize: "none",
            fontFamily: "var(--font-body)", outline: "none",
            transition: "border-color 0.2s",
          }}
          onFocus={e => (e.target.style.borderColor = "var(--accent)")}
          onBlur={e => (e.target.style.borderColor = "var(--border)")}
        />

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "1rem", flexWrap: "wrap", gap: "12px" }}>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {EXAMPLES.map(ex => (
              <button key={ex.lang} onClick={() => { setText(ex.text); analyze(ex.text); }}
                style={{
                  fontFamily: "var(--font-mono)", fontSize: "11px",
                  padding: "5px 12px", borderRadius: "6px",
                  border: "1px solid var(--border-hi)",
                  background: "transparent", color: "var(--text-muted)",
                  cursor: "pointer", transition: "all 0.15s", letterSpacing: "0.03em",
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--accent)"; e.currentTarget.style.color = "var(--accent)"; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border-hi)"; e.currentTarget.style.color = "var(--text-muted)"; }}
              >
                {ex.lang}
              </button>
            ))}
          </div>

          <button onClick={() => analyze()} disabled={loading || !text.trim()}
            style={{
              fontFamily: "var(--font-display)", fontWeight: 600,
              fontSize: "14px", padding: "9px 24px", borderRadius: "8px",
              background: loading ? "var(--bg-raised)" : "var(--accent)",
              color: loading ? "var(--text-muted)" : "#000",
              border: "none", cursor: loading || !text.trim() ? "not-allowed" : "pointer",
              opacity: !text.trim() ? 0.4 : 1,
              transition: "all 0.15s", letterSpacing: "-0.01em",
            }}
          >
            {loading ? "Analyzing..." : "Analyze →"}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div style={{
            marginTop: "1rem", padding: "12px 16px", borderRadius: "8px",
            background: "rgba(255,77,109,0.08)", border: "1px solid rgba(255,77,109,0.2)",
            color: "var(--red)", fontSize: "14px",
          }}>{error}</div>
        )}

        {/* Results */}
        {result && (
          <div style={{ marginTop: "1.5rem" }}>

            {/* Summary bar */}
            <div style={{
              display: "flex", alignItems: "center", gap: "1rem",
              background: "var(--bg-raised)", borderRadius: "10px",
              padding: "1rem 1.25rem", marginBottom: "1rem",
              border: "1px solid var(--border)", flexWrap: "wrap",
            }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: "11px", color: "var(--text-dim)", fontFamily: "var(--font-mono)", marginBottom: "6px", letterSpacing: "0.05em" }}>TOP DETECTION</div>
                {top && (
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{
                      fontSize: "13px", fontWeight: 500,
                      padding: "4px 12px", borderRadius: "999px",
                      background: LABEL_CONFIG[top.label]?.bg,
                      color: LABEL_CONFIG[top.label]?.color,
                      border: `1px solid ${LABEL_CONFIG[top.label]?.color}33`,
                    }}>
                      {LABEL_CONFIG[top.label]?.label ?? top.label}
                    </span>
                    {top.severity && (
                      <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                        {SEVERITY_LABEL[top.severity]}
                      </span>
                    )}
                  </div>
                )}
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: "11px", color: "var(--text-dim)", fontFamily: "var(--font-mono)", marginBottom: "4px", letterSpacing: "0.05em" }}>LANGUAGE</div>
                <div style={{ fontSize: "13px", fontFamily: "var(--font-mono)", color: "var(--accent)" }}>{result.language_detected.toUpperCase()}</div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: "11px", color: "var(--text-dim)", fontFamily: "var(--font-mono)", marginBottom: "4px", letterSpacing: "0.05em" }}>LATENCY</div>
                <div style={{ fontSize: "13px", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>{result.processing_time_ms}ms</div>
              </div>
            </div>

            {/* Human review flag */}
            {result.flagged_for_review && (
              <div style={{
                padding: "10px 16px", borderRadius: "8px", marginBottom: "1rem",
                background: "rgba(255,209,102,0.06)", border: "1px solid rgba(255,209,102,0.2)",
                color: "var(--yellow)", fontSize: "13px", fontFamily: "var(--font-mono)",
              }}>
                ⚑ Flagged for human review — confidence is low or content is ambiguous
              </div>
            )}

            {/* Prediction cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "10px" }}>
              {result.predictions.map(p => {
                const cfg = LABEL_CONFIG[p.label] ?? LABEL_CONFIG.clean;
                return (
                  <div key={p.label} style={{
                    background: cfg.bg, border: `1px solid ${cfg.color}22`,
                    borderRadius: "10px", padding: "1rem",
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
                      <span style={{ fontSize: "13px", fontWeight: 500, color: cfg.color }}>
                        {cfg.label}
                      </span>
                      {p.severity && (
                        <span style={{ fontSize: "11px", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                          {SEVERITY_LABEL[p.severity]}
                        </span>
                      )}
                    </div>
                    {/* Confidence bar */}
                    <div style={{ height: "3px", background: "rgba(255,255,255,0.06)", borderRadius: "2px", marginBottom: "6px" }}>
                      <div style={{
                        height: "100%", borderRadius: "2px",
                        background: cfg.color, opacity: 0.7,
                        width: `${Math.round(p.confidence * 100)}%`,
                        transition: "width 0.6s ease",
                      }} />
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                      {Math.round(p.confidence * 100)}%
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ marginTop: "1rem", fontSize: "11px", color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
              {result.prediction_id} · {result.model_version}
            </div>
          </div>
        )}
      </section>

      {/* ── How it works ── */}
      <section className="afu2" style={{ marginBottom: "5rem" }}>
        <div style={{ marginBottom: "2.5rem" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--accent)", letterSpacing: "0.1em", marginBottom: "12px" }}>
            HOW IT WORKS
          </div>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: "2rem", fontWeight: 700, letterSpacing: "-0.03em" }}>
            From text to insight in milliseconds
          </h2>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1px", background: "var(--border)", borderRadius: "12px", overflow: "hidden" }}>
          {HOW_IT_WORKS.map((item, i) => (
            <div key={i} style={{ background: "var(--bg-card)", padding: "1.75rem" }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--accent)", marginBottom: "1rem", letterSpacing: "0.05em" }}>
                {item.step}
              </div>
              <div style={{ fontFamily: "var(--font-display)", fontWeight: 600, fontSize: "15px", marginBottom: "8px", letterSpacing: "-0.02em" }}>
                {item.title}
              </div>
              <div style={{ color: "var(--text-muted)", fontSize: "13px", lineHeight: 1.6 }}>
                {item.desc}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── API Quick Start ── */}
      <section className="afu3" style={{ marginBottom: "5rem" }}>
        <div style={{ marginBottom: "2.5rem" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--accent)", letterSpacing: "0.1em", marginBottom: "12px" }}>
            API QUICK START
          </div>
          <h2 style={{ fontFamily: "var(--font-display)", fontSize: "2rem", fontWeight: 700, letterSpacing: "-0.03em" }}>
            Integrate in 3 lines
          </h2>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1px", background: "var(--border)", borderRadius: "12px", overflow: "hidden" }}>
          {[
            {
              lang: "cURL",
              code: `curl -X POST https://api.sauti.africa/v1/analyze \\
  -H "X-API-Key: YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Wewe ni mjinga kabisa"}'`,
            },
            {
              lang: "Python",
              code: `import httpx

r = httpx.post(
  "https://api.sauti.africa/v1/analyze",
  headers={"X-API-Key": "YOUR_KEY"},
  json={"text": "Tutakukumbuka"},
)
print(r.json()["predictions"])`,
            },
          ].map(ex => (
            <div key={ex.lang} style={{ background: "var(--bg-card)", padding: "1.75rem" }}>
              <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)", marginBottom: "1rem", letterSpacing: "0.05em" }}>
                {ex.lang}
              </div>
              <pre style={{
                fontFamily: "var(--font-mono)", fontSize: "12px",
                color: "var(--text-muted)", lineHeight: 1.8,
                whiteSpace: "pre-wrap", wordBreak: "break-all",
              }}>
                {ex.code}
              </pre>
            </div>
          ))}
        </div>

        <div style={{ marginTop: "1rem", display: "flex", gap: "12px" }}>
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
            style={{
              fontFamily: "var(--font-mono)", fontSize: "12px",
              padding: "8px 18px", borderRadius: "7px",
              border: "1px solid var(--accent)",
              color: "var(--accent)", textDecoration: "none",
              transition: "all 0.15s",
              background: "transparent",
            }}
            onMouseEnter={e => (e.currentTarget.style.background = "var(--accent-dim)")}
            onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
          >
            Full API Reference →
          </a>
          <a href="/dashboard"
            style={{
              fontFamily: "var(--font-mono)", fontSize: "12px",
              padding: "8px 18px", borderRadius: "7px",
              border: "1px solid var(--border-hi)",
              color: "var(--text-muted)", textDecoration: "none",
              transition: "all 0.15s",
            }}
            onMouseEnter={e => (e.currentTarget.style.borderColor = "var(--border-hi)")}
            onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--border)")}
          >
            Get API Key →
          </a>
        </div>
      </section>

    </main>
  );
}
