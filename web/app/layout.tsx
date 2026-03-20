import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sauti — Harmful Speech Detection",
  description:
    "Detect harmful, distressing, and manipulative language in Swahili, Sheng, and English.",
  keywords: ["content moderation", "Kenya", "Swahili", "harmful speech", "NLP"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 text-gray-900 antialiased">
        <nav className="border-b border-gray-200 bg-white px-6 py-4">
          <div className="mx-auto flex max-w-5xl items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xl font-semibold tracking-tight text-emerald-700">
                sauti
              </span>
              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-600">
                beta
              </span>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-500">
              <a href="/" className="hover:text-gray-900">
                Analyze
              </a>
              <a href="/dashboard" className="hover:text-gray-900">
                Dashboard
              </a>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="hover:text-gray-900"
              >
                API docs
              </a>
            </div>
          </div>
        </nav>
        <main className="mx-auto max-w-5xl px-6 py-10">{children}</main>
        <footer className="mt-20 border-t border-gray-200 py-8 text-center text-xs text-gray-400">
          Sauti · Built for East Africa · Apache 2.0
        </footer>
      </body>
    </html>
  );
}
