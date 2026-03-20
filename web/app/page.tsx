"use client";

import { useState } from "react";
import clsx from "clsx";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_DEMO_API_KEY ?? "dev-local-key-do-not-use-in-prod";

const LABEL_META: Record<string, { color: string; bg: string; label: string }> = {
  hate_speech:        { color: "text-red-700",    bg: "bg-red-50 border-red-200",    label: "Hate Speech" },
  offensive_language: { color: "text-orange-700", bg: "bg-orange-50 border-orange-200", label: "Offensive Language" },
  distress_trigger:   { color: "text-yellow-700", bg: "bg-yellow-50 border-yellow-200", label: "Distress Trigger" },
  gaslighting:        { color: "text-purple-700", bg: "bg-purple-50 border-purple-200", label: "Gaslighting" },
  manipulation:       { color: "text-pink-700",   bg: "bg-pink-50 border-pink-200",   label: "Manipulation" },
  ambiguous:          { color: "text-gray-600",   bg: "bg-gray-50 border-gray-200",   label: "Ambiguous" },
  clean:              { color: "text-emerald-700",bg: "bg-emerald-50 border-emerald-200", label: "Clean" },
};

const SEVERITY_LABEL = ["", "Mild", "Low", "Moderate", "High", "Severe"];

const EXAMPLES = [
  { lang: "Swahili", text: "Wote Somali ni terrorists na wezi sana" },
  { lang: "Sheng",   text: "Wewe ni mjinga kabisa, hujui kitu manze" },
  { lang: "English", text: "You're just being too sensitive as always" },
  { lang: "Mixed",   text: "Tutakukumbuka vizuri baada ya uchaguzi hii" },
];

type Prediction = {
  label: string;
  confidence: number;
  severity: number | null;
};

type Result = {
  prediction_id: string;
  text: string;
  language_detected: string;
  predictions: Prediction[];
  flagged_for_review: boolean;
  model_version: string;
  processing_time_ms: number;
};

export default function AnalyzePage() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function analyze(inputText?: string) {
    const target = inputText ?? text;
    if (!target.trim()) return;

    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/v1/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": API_KEY,
        },
        body: JSON.stringify({ text: target, explain: false }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }

      const data: Result = await res.json();
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  function loadExample(exampleText: string) {
    setText(exampleText);
    analyze(exampleText);
  }

  const topPrediction = result?.predictions?.[0];
  const isFlagged = result?.flagged_for_review;

  return (
    <div className="space-y-10">

      {/* Hero */}
      <div className="space-y-2">
        <h1 className="text-3xl font-semibold tracking-tight">
          Harmful speech detection
        </h1>
        <p className="text-gray-500 max-w-xl">
          Analyzes text for hate speech, manipulation, gaslighting, and distress-triggering
          language. Supports <strong>Swahili</strong>, <strong>Sheng</strong>, English, and
          code-switched text.
        </p>
      </div>

      {/* Input */}
      <div className="space-y-3">
        <textarea
          className="w-full rounded-xl border border-gray-200 bg-white p-4 text-sm leading-relaxed
                     shadow-sm outline-none focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100
                     resize-none transition"
          rows={5}
          placeholder="Andika hapa... / Type here... / Andika Sheng..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) analyze();
          }}
        />

        <div className="flex items-center justify-between">
          <div className="flex flex-wrap gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex.lang}
                onClick={() => loadExample(ex.text)}
                className="rounded-full border border-gray-200 bg-white px-3 py-1 text-xs
                           text-gray-500 hover:border-emerald-300 hover:text-emerald-700 transition"
              >
                Try {ex.lang}
              </button>
            ))}
          </div>

          <button
            onClick={() => analyze()}
            disabled={loading || !text.trim()}
            className="rounded-xl bg-emerald-600 px-5 py-2 text-sm font-medium text-white
                       hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition"
          >
            {loading ? "Analyzing..." : "Analyze →"}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">

          {/* Summary bar */}
          <div className="flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-4">
            <div className="flex-1 space-y-0.5">
              <p className="text-xs text-gray-400">Top detection</p>
              {topPrediction && (
                <div className="flex items-center gap-2">
                  <span
                    className={clsx(
                      "rounded-full border px-3 py-0.5 text-xs font-medium",
                      LABEL_META[topPrediction.label]?.bg,
                      LABEL_META[topPrediction.label]?.color
                    )}
                  >
                    {LABEL_META[topPrediction.label]?.label ?? topPrediction.label}
                  </span>
                  {topPrediction.severity && (
                    <span className="text-xs text-gray-400">
                      Severity: {SEVERITY_LABEL[topPrediction.severity]}
                    </span>
                  )}
                </div>
              )}
            </div>
            <div className="text-right space-y-0.5">
              <p className="text-xs text-gray-400">Language</p>
              <p className="text-sm font-medium uppercase tracking-wide text-gray-600">
                {result.language_detected}
              </p>
            </div>
            <div className="text-right space-y-0.5">
              <p className="text-xs text-gray-400">Time</p>
              <p className="text-sm text-gray-600">{result.processing_time_ms}ms</p>
            </div>
          </div>

          {/* Human review flag */}
          {isFlagged && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
              This prediction has been flagged for human review — confidence is low or the content
              is ambiguous.
            </div>
          )}

          {/* All predictions */}
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-gray-500">All detections</h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {result.predictions.map((p) => (
                <div
                  key={p.label}
                  className={clsx(
                    "rounded-xl border p-4 space-y-2",
                    LABEL_META[p.label]?.bg ?? "bg-gray-50 border-gray-200"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={clsx(
                        "text-sm font-medium",
                        LABEL_META[p.label]?.color ?? "text-gray-700"
                      )}
                    >
                      {LABEL_META[p.label]?.label ?? p.label}
                    </span>
                    {p.severity && (
                      <span className="text-xs text-gray-400">
                        {SEVERITY_LABEL[p.severity]}
                      </span>
                    )}
                  </div>
                  {/* Confidence bar */}
                  <div className="h-1.5 w-full rounded-full bg-white/60">
                    <div
                      className="h-1.5 rounded-full bg-current opacity-50 transition-all"
                      style={{ width: `${Math.round(p.confidence * 100)}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-400">
                    {Math.round(p.confidence * 100)}% confidence
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Prediction ID / model */}
          <p className="text-xs text-gray-300">
            id: {result.prediction_id} · model: {result.model_version}
          </p>
        </div>
      )}
    </div>
  );
}
