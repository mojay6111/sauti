"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEV_KEY = process.env.NEXT_PUBLIC_DEMO_API_KEY ?? "dev-local-key-do-not-use-in-prod";

const LABELS = [
  { id: "hate_speech",        color: "#ff4d6d", desc: "Targets a group by ethnicity, religion, or gender" },
  { id: "offensive_language", color: "#ff8c42", desc: "Personal insults or degrading language" },
  { id: "distress_trigger",   color: "#ffd166", desc: "Content designed to cause fear or panic" },
  { id: "gaslighting",        color: "#c77dff", desc: "Denies or distorts someone's perception of reality" },
  { id: "manipulation",       color: "#7c6aff", desc: "Coercive or emotionally exploitative tactics" },
  { id: "ambiguous",          color: "#5a5a7a", desc: "Context-dependent — routed for human review" },
  { id: "clean",              color: "#00e5a0", desc: "No harmful content detected" },
];

const STATUS_CARDS = [
  { label: "API Status",     value: "Online",   sub: "v0.1.0",        accent: "#00e5a0" },
  { label: "Model",          value: "Baseline", sub: "TF-IDF + LR",   accent: "#7c6aff" },
  { label: "Requests today", value: "—",        sub: "tracking soon", accent: "#5a5a7a" },
  { label: "Flagged",        value: "—",        sub: "pending review", accent: "#ffd166" },
];

export default function DashboardPage() {
  const [copied, setCopied] = useState(false);
  const [healthData, setHealthData] = useState<any>(null);
  const [checking, setChecking] = useState(false);

  function copyKey() {
    navigator.clipboard.writeText(DEV_KEY);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function checkHealth() {
    setChecking(true);
    try {
      const r = await fetch(`${API_URL}/health`);
      setHealthData(await r.json());
    } catch {
      setHealthData({ status: "unreachable" });
    } finally {
      setChecking(false);
    }
  }

  return (
    <main style={{ maxWidth: "960px", margin: "0 auto", padding: "3rem 2rem 6rem" }}>

      {/* Header */}
      <div style={{ marginBottom: "3rem" }} className="afu">
        <div style={{
          fontFamily: "var(--font-mono)", fontSize: "11px",
          color: "var(--accent)", letterSpacing: "0.1em", marginBottom: "12px",
        }}>
          DEVELOPER DASHBOARD
        </div>
        <h1 style={{
          fontFamily: "var(--font-display)", fontSize: "2.5rem",
          fontWeight: 800, letterSpacing: "-0.04em", marginBottom: "8px",
        }}>
          Build with Sauti
        </h1>
        <p style={{ color: "var(--text-muted)", fontSize: "15px", fontWeight: 300 }}>
          API keys, model status, and integration guides.
        </p>
      </div>

      {/* Status cards */}
      <div className="afu1" style={{
        display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
        gap: "1px", background: "var(--border)",
        borderRadius: "12px", overflow: "hidden", marginBottom: "2rem",
      }}>
        {STATUS_CARDS.map(card => (
          <div key={card.label} style={{ background: "var(--bg-card)", padding: "1.5rem" }}>
            <div style={{
              fontFamily: "var(--font-mono)", fontSize: "10px",
              color: "var(--text-dim)", letterSpacing: "0.08em", marginBottom: "12px",
            }}>
              {card.label.toUpperCase()}
            </div>
            <div style={{
              fontFamily: "var(--font-display)", fontSize: "1.75rem",
              fontWeight: 700, letterSpacing: "-0.03em",
              color: card.accent, marginBottom: "4px",
            }}>
              {card.value}
            </div>
            <div style={{ fontSize: "12px", color: "var(--text-dim)" }}>{card.sub}</div>
          </div>
        ))}
      </div>

      {/* Health check */}
      <div className="afu1" style={{
        background: "var(--bg-card)", border: "1px solid var(--border)",
        borderRadius: "12px", padding: "1.5rem", marginBottom: "2rem",
        display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "1rem",
      }}>
        <div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)", letterSpacing: "0.08em", marginBottom: "6px" }}>
            API HEALTH
          </div>
          {healthData ? (
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{
                width: "8px", height: "8px", borderRadius: "50%",
                background: healthData.status === "ok" ? "var(--accent)" : "var(--red)",
                display: "inline-block",
                boxShadow: healthData.status === "ok" ? "0 0 8px var(--accent)" : "0 0 8px var(--red)",
              }} />
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "13px", color: "var(--text)" }}>
                {healthData.status === "ok"
                  ? `Online · model: ${healthData.model_version} · uptime: ${Math.round(healthData.uptime_seconds)}s`
                  : "Unreachable — is Docker running?"}
              </span>
            </div>
          ) : (
            <div style={{ color: "var(--text-muted)", fontSize: "13px" }}>Click to check API status</div>
          )}
        </div>
        <button onClick={checkHealth} disabled={checking} style={{
          fontFamily: "var(--font-mono)", fontSize: "12px",
          padding: "8px 18px", borderRadius: "7px",
          border: "1px solid var(--border-hi)",
          background: "transparent", color: "var(--text-muted)",
          cursor: "pointer", transition: "all 0.15s",
          letterSpacing: "0.03em",
        }}>
          {checking ? "Checking..." : "Check health →"}
        </button>
      </div>

      {/* API Key */}
      <div className="afu2" style={{
        background: "var(--bg-card)", border: "1px solid var(--border)",
        borderRadius: "12px", padding: "1.5rem", marginBottom: "2rem",
      }}>
        <div style={{ fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--text-dim)", letterSpacing: "0.08em", marginBottom: "1rem" }}>
          YOUR API KEY
        </div>
        <div style={{ display: "flex", gap: "10px", marginBottom: "1rem" }}>
          <code style={{
            flex: 1, background: "var(--bg-raised)",
            border: "1px solid var(--border)", borderRadius: "8px",
            padding: "10px 14px", fontFamily: "var(--font-mono)",
            fontSize: "13px", color: "var(--accent)",
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
          }}>
            {DEV_KEY}
          </code>
          <button onClick={copyKey} style={{
            fontFamily: "var(--font-mono)", fontSize: "12px",
            padding: "10px 18px", borderRadius: "8px",
            border: "1px solid var(--border-hi)",
            background: copied ? "var(--accent-dim)" : "transparent",
            color: copied ? "var(--accent)" : "var(--text-muted)",
            cursor: "pointer", transition: "all 0.2s", whiteSpace: "nowrap",
          }}>
            {copied ? "Copied ✓" : "Copy"}
          </button>
        </div>
        <div style={{
          background: "rgba(255,209,102,0.06)", border: "1px solid rgba(255,209,102,0.15)",
          borderRadius: "8px", padding: "10px 14px",
          fontFamily: "var(--font-mono)", fontSize: "11px", color: "var(--yellow)",
          lineHeight: 1.6,
        }}>
          ⚠ Dev key only. For production generate with:{" "}
          <code style={{ color: "var(--text-muted)" }}>
            python -c "import secrets; print(secrets.token_urlsafe(32))"
          </code>
        </div>
      </div>

      {/* Quick start */}
      <div className="afu3" style={{ marginBottom: "2rem" }}>
        <div style={{
          fontFamily: "var(--font-mono)", fontSize: "11px",
          color: "var(--accent)", letterSpacing: "0.1em", marginBottom: "1.5rem",
        }}>
          QUICK START
        </div>
        <div style={{
          display: "grid", gridTemplateColumns: "1fr 1fr",
          gap: "1px", background: "var(--border)",
          borderRadius: "12px", overflow: "hidden",
        }}>
          {[
            {
              lang: "cURL",
              code: `curl -X POST http://localhost:8000/v1/analyze \\
  -H "X-API-Key: ${DEV_KEY.slice(0, 16)}..." \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Wewe ni mjinga kabisa"}'`,
            },
            {
              lang: "JavaScript",
              code: `const res = await fetch(
  "http://localhost:8000/v1/analyze",
  {
    method: "POST",
    headers: { "X-API-Key": "YOUR_KEY" },
    body: JSON.stringify({ text: "..." }),
  }
);
const data = await res.json();`,
            },
          ].map(ex => (
            <div key={ex.lang} style={{ background: "var(--bg-card)", padding: "1.5rem" }}>
              <div style={{
                fontFamily: "var(--font-mono)", fontSize: "10px",
                color: "var(--text-dim)", letterSpacing: "0.08em", marginBottom: "1rem",
              }}>
                {ex.lang}
              </div>
              <pre style={{
                fontFamily: "var(--font-mono)", fontSize: "11px",
                color: "var(--text-muted)", lineHeight: 1.8,
                whiteSpace: "pre-wrap", wordBreak: "break-all",
              }}>
                {ex.code}
              </pre>
            </div>
          ))}
        </div>
      </div>

      {/* Label reference */}
      <div className="afu4">
        <div style={{
          fontFamily: "var(--font-mono)", fontSize: "11px",
          color: "var(--accent)", letterSpacing: "0.1em", marginBottom: "1.5rem",
        }}>
          LABEL REFERENCE
        </div>
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          gap: "1px", background: "var(--border)",
          borderRadius: "12px", overflow: "hidden",
        }}>
          {LABELS.map(item => (
            <div key={item.id} style={{ background: "var(--bg-card)", padding: "1.25rem", display: "flex", gap: "12px", alignItems: "flex-start" }}>
              <span style={{
                width: "8px", height: "8px", borderRadius: "50%",
                background: item.color, flexShrink: 0, marginTop: "5px",
                boxShadow: `0 0 6px ${item.color}66`,
              }} />
              <div>
                <code style={{
                  fontFamily: "var(--font-mono)", fontSize: "11px",
                  color: item.color, display: "block", marginBottom: "4px",
                }}>
                  {item.id}
                </code>
                <p style={{ fontSize: "12px", color: "var(--text-muted)", lineHeight: 1.5 }}>
                  {item.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

    </main>
  );
}
