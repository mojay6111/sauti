import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Sauti — Harmful Speech Detection for East Africa",
  description: "Real-time detection of hate speech, manipulation, gaslighting and distress-triggering language in Swahili, Sheng and English.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "var(--font-body)" }}>

        <nav style={{
          position: "sticky", top: 0, zIndex: 50,
          borderBottom: "1px solid var(--border)",
          background: "rgba(10,10,15,0.85)",
          backdropFilter: "blur(12px)",
          padding: "0 2rem",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          height: "56px",
        }}>
          <Link href="/" className="nav-logo">
            sauti
            <span className="nav-badge">v0.1 BETA</span>
          </Link>

          <div style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
            <Link href="/"          className="nav-link">Demo</Link>
            <Link href="/dashboard" className="nav-link">Dashboard</Link>
            <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="nav-link">API Docs</a>
            <a href="https://github.com/mojay6111/sauti" target="_blank" rel="noreferrer" className="nav-gh">GitHub ↗</a>
          </div>
        </nav>

        {children}

        <footer style={{
          borderTop: "1px solid var(--border)",
          padding: "2rem",
          textAlign: "center",
          color: "var(--text-dim)",
          fontSize: "13px",
          fontFamily: "var(--font-mono)",
          letterSpacing: "0.03em",
        }}>
          SAUTI · BUILT FOR EAST AFRICA · APACHE 2.0 · 🇰🇪
        </footer>

      </body>
    </html>
  );
}
