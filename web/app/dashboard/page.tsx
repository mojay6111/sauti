"use client";

import { useState } from "react";

const LABEL_COUNTS = [
  { label: "hate_speech",        color: "bg-red-400",    count: 0 },
  { label: "offensive_language", color: "bg-orange-400", count: 0 },
  { label: "distress_trigger",   color: "bg-yellow-400", count: 0 },
  { label: "gaslighting",        color: "bg-purple-400", count: 0 },
  { label: "manipulation",       color: "bg-pink-400",   count: 0 },
  { label: "ambiguous",          color: "bg-gray-400",   count: 0 },
  { label: "clean",              color: "bg-emerald-400",count: 0 },
];

export default function DashboardPage() {
  const [copied, setCopied] = useState(false);
  const devKey = "dev-local-key-do-not-use-in-prod";

  function copyKey() {
    navigator.clipboard.writeText(devKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="space-y-10">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold">Developer Dashboard</h1>
        <p className="text-gray-500 mt-1 text-sm">
          API keys, usage, and model status. Production key management coming in v0.2.
        </p>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: "API Status",     value: "Online",   sub: "v0.1.0",        ok: true  },
          { label: "Model",          value: "Baseline", sub: "TF-IDF + LR",   ok: true  },
          { label: "Requests today", value: "—",        sub: "tracking soon", ok: null  },
          { label: "Pending review", value: "—",        sub: "flagged items",  ok: null  },
        ].map((card) => (
          <div
            key={card.label}
            className="rounded-xl border border-gray-200 bg-white p-4 space-y-1"
          >
            <p className="text-xs text-gray-400">{card.label}</p>
            <p className="text-xl font-semibold">{card.value}</p>
            <p className="text-xs text-gray-400">{card.sub}</p>
            {card.ok !== null && (
              <span
                className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                  card.ok
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-gray-50 text-gray-500"
                }`}
              >
                {card.ok ? "● live" : "● soon"}
              </span>
            )}
          </div>
        ))}
      </div>

      {/* API key */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
        <div>
          <h2 className="font-medium">Your API key</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            Include this in every request as the <code className="bg-gray-100 px-1 rounded text-xs">X-API-Key</code> header.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <code className="flex-1 rounded-lg bg-gray-50 border border-gray-200 px-4 py-2.5 text-sm font-mono text-gray-700 overflow-x-auto">
            {devKey}
          </code>
          <button
            onClick={copyKey}
            className="rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm hover:border-gray-300 transition min-w-[80px]"
          >
            {copied ? "Copied ✓" : "Copy"}
          </button>
        </div>

        <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-700">
          ⚠️  This is the local dev key. For production, generate a secure key with:{" "}
          <code className="font-mono">python -c "import secrets; print(secrets.token_urlsafe(32))"</code>{" "}
          and set it in your <code className="font-mono">.env</code> file.
        </div>
      </div>

      {/* Quick start */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
        <h2 className="font-medium">Quick start</h2>
        <div className="space-y-3">
          {[
            {
              title: "cURL",
              code: `curl -X POST http://localhost:8000/v1/analyze \\
  -H "X-API-Key: ${devKey}" \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Wewe ni mjinga kabisa"}'`,
            },
            {
              title: "Python",
              code: `import httpx

r = httpx.post(
    "http://localhost:8000/v1/analyze",
    headers={"X-API-Key": "${devKey}"},
    json={"text": "Tutakukumbuka baada ya uchaguzi"},
)
print(r.json())`,
            },
            {
              title: "JavaScript",
              code: `const res = await fetch("http://localhost:8000/v1/analyze", {
  method: "POST",
  headers: {
    "X-API-Key": "${devKey}",
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ text: "Wewe ni mjinga kabisa" }),
});
const data = await res.json();
console.log(data.predictions);`,
            },
          ].map((ex) => (
            <div key={ex.title} className="space-y-1.5">
              <p className="text-xs font-medium text-gray-500">{ex.title}</p>
              <pre className="rounded-lg bg-gray-900 text-gray-100 p-4 text-xs overflow-x-auto leading-relaxed">
                {ex.code}
              </pre>
            </div>
          ))}
        </div>
      </div>

      {/* Label reference */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
        <h2 className="font-medium">Label reference</h2>
        <div className="grid gap-2 sm:grid-cols-2">
          {[
            { id: "hate_speech",        desc: "Targets a group by ethnicity, religion, gender, etc." },
            { id: "offensive_language", desc: "Personal insults or degrading language" },
            { id: "distress_trigger",   desc: "Content designed to cause fear or panic" },
            { id: "gaslighting",        desc: "Denies or distorts someone's perception of reality" },
            { id: "manipulation",       desc: "Coercive or emotionally exploitative tactics" },
            { id: "ambiguous",          desc: "Context-dependent — routed for human review" },
            { id: "clean",              desc: "No harmful content detected" },
          ].map((item) => (
            <div key={item.id} className="flex gap-3 rounded-lg border border-gray-100 p-3">
              <code className="text-xs font-mono text-gray-600 bg-gray-50 px-1.5 py-0.5 rounded self-start shrink-0">
                {item.id}
              </code>
              <p className="text-xs text-gray-500">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Links */}
      <div className="flex flex-wrap gap-3 text-sm">
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noreferrer"
          className="rounded-lg border border-gray-200 bg-white px-4 py-2 hover:border-gray-300 transition"
        >
          API docs (Swagger) ↗
        </a>
        <a
          href="http://localhost:8000/health"
          target="_blank"
          rel="noreferrer"
          className="rounded-lg border border-gray-200 bg-white px-4 py-2 hover:border-gray-300 transition"
        >
          Health check ↗
        </a>
        <a
          href="http://localhost:8080"
          target="_blank"
          rel="noreferrer"
          className="rounded-lg border border-gray-200 bg-white px-4 py-2 hover:border-gray-300 transition"
        >
          Label Studio (annotation) ↗
        </a>
      </div>

    </div>
  );
}
