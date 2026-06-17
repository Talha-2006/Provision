import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import { getEnabledSources } from "@/lib/sources";
import MobileNav from "../mobile-nav";

export const metadata: Metadata = {
  title: "Sources | Provision",
  description:
    "Official and high-trust sources used by Provision for Canadian startup compliance research.",
};

function ArrowUpRightIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <path d="M7 17 17 7M8 7h9v9" />
    </svg>
  );
}

function ShieldMark() {
  return (
    <svg aria-hidden="true" viewBox="0 0 32 38" fill="none">
      <path
        d="M16 2 28 7v9.4C28 25.2 23.1 32 16 36 8.9 32 4 25.2 4 16.4V7l12-5Z"
        stroke="currentColor"
        strokeWidth="2"
      />
      <path d="m10.5 18 3.5 3.5 7.5-8" stroke="currentColor" strokeWidth="2" />
    </svg>
  );
}

function formatLabel(value: string) {
  return value.replaceAll("_", " ");
}

export default function SourcesPage() {
  const enabledSources = getEnabledSources();

  return (
    <main className="site-shell sources-shell">
      <div className="background-grid" />
      <div className="red-haze red-haze-top" />
      <div className="sources-haze" />

      <nav className="topbar" aria-label="Main navigation">
        <Link className="brand" href="/" aria-label="Provision home">
          <span className="brand-mark">
            <ShieldMark />
          </span>
          <span>PROVISION</span>
        </Link>

        <div className="nav-actions">
          <div className="nav-links">
            <Link href="/about">About</Link>
            <Link className="nav-link-active" href="/sources">
              Sources
            </Link>
            <span className="jurisdiction-pill">
              <Image
                className="canada-flag"
                src="/canada-flag.svg"
                width={18}
                height={12}
                alt=""
                unoptimized
              />
              Canada
            </span>
          </div>
          <MobileNav activePage="sources" />
        </div>
      </nav>

      <section className="sources-content" aria-labelledby="sources-heading">
        <div className="sources-intro">
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            Research library
          </div>
          <div className="sources-heading-row">
            <div>
              <h1 id="sources-heading">Trusted sources.</h1>
              <p>
                Provision prioritizes official legislation, government
                guidance, and regulator resources. Its answers are derived from
                the sources in this research library.
              </p>
            </div>
            <span className="source-count">
              <strong>{enabledSources.length}</strong>
              sources
            </span>
          </div>
        </div>

        <div className="sources-grid">
          {enabledSources.map((source, index) => (
            <a
              className="source-card"
              href={source.url}
              key={source.id}
              aria-label={`${source.title}, opens official source`}
            >
              <div className="source-card-top">
                <span className="source-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="source-link-icon">
                  <ArrowUpRightIcon />
                </span>
              </div>

              <h2>{source.title}</h2>

              <div className="source-meta">
                <span>{source.jurisdiction}</span>
                <span>{formatLabel(source.topic)}</span>
                <span>{formatLabel(source.source_type)}</span>
              </div>

              <span className="source-domain">
                {new URL(source.url).hostname.replace("www.", "")}
              </span>
            </a>
          ))}
        </div>
      </section>

      <footer className="footer-note sources-footer">
        <span className="status-dot" />
        Sources are maintained in data/sources.json
      </footer>
    </main>
  );
}
