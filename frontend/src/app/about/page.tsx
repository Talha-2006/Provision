import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import MobileNav from "../mobile-nav";

export const metadata: Metadata = {
  title: "About | Provision",
  description:
    "Learn how Provision supports citation-grounded Canadian startup compliance research.",
};

const topics = [
  "Federal incorporation obligations",
  "Annual returns",
  "Individuals with significant control",
  "Canadian privacy and PIPEDA basics",
  "GST/HST registration basics",
  "Payroll setup basics",
  "Employee vs contractor considerations",
  "Ontario business registration",
  "Permits and licences",
  "General startup compliance checklists",
];

const steps = [
  {
    title: "Ask",
    description: "A founder asks a Canadian startup compliance question.",
  },
  {
    title: "Retrieve",
    description:
      "Provision searches the vector database for relevant source chunks.",
  },
  {
    title: "Generate",
    description:
      "The model prepares a response using the retrieved context.",
  },
  {
    title: "Verify",
    description:
      "The response includes citations, checklists, and professional-help warnings.",
  },
];

const technologies = [
  "LangChain",
  "OpenAI",
  "ChromaDB",
  "FastAPI",
  "LangSmith",
  "Next.js",
  "React",
];

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

export default function AboutPage() {
  return (
    <main className="site-shell about-shell">
      <div className="background-grid" />
      <div className="red-haze red-haze-top" />
      <div className="about-haze" />

      <nav className="topbar" aria-label="Main navigation">
        <Link className="brand" href="/" aria-label="Provision home">
          <span className="brand-mark">
            <ShieldMark />
          </span>
          <span>PROVISION</span>
        </Link>

        <div className="nav-actions">
          <div className="nav-links">
            <Link className="nav-link-active" href="/about">
              About
            </Link>
            <Link href="/sources">Sources</Link>
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
          <MobileNav activePage="about" />
        </div>
      </nav>

      <div className="about-content">
        <header className="about-hero">
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            The project
          </div>
          <h1>About Provision</h1>
          <p>
            Provision helps Canadian startup founders research compliance
            obligations using official and high-trust sources.
          </p>
        </header>

        <section className="about-two-column" aria-label="About Provision">
          <article className="about-feature-card">
            <span className="about-card-index">01</span>
            <h2>What Provision is</h2>
            <p>
              Provision is a source-grounded compliance research assistant. It
              uses retrieval-augmented generation to find relevant source
              material and prepare responses supported by citations.
            </p>
          </article>

          <article className="about-feature-card">
            <span className="about-card-index">02</span>
            <h2>The problem it addresses</h2>
            <p>
              Early-stage founders can miss important compliance tasks because
              official information is spread across legislation, regulators,
              and government guidance. Provision organizes that material into
              answers, checklists, citations, and risk flags.
            </p>
          </article>
        </section>

        <section className="about-section" aria-labelledby="topics-heading">
          <div className="about-section-heading">
            <span>Coverage</span>
            <div>
              <h2 id="topics-heading">Topics Provision covers</h2>
              <p>
                Practical research areas that commonly arise while starting
                and operating a Canadian company.
              </p>
            </div>
          </div>

          <div className="about-topics-grid">
            {topics.map((topic, index) => (
              <article className="about-topic-card" key={topic}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <h3>{topic}</h3>
              </article>
            ))}
          </div>
        </section>

        <section className="about-section" aria-labelledby="process-heading">
          <div className="about-section-heading">
            <span>Process</span>
            <div>
              <h2 id="process-heading">How it works</h2>
              <p>
                Retrieval keeps the generated response tied to the source
                material selected for the question.
              </p>
            </div>
          </div>

          <ol className="about-steps">
            {steps.map((step, index) => (
              <li key={step.title}>
                <span className="about-step-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="about-scope-grid" aria-label="Scope and disclaimer">
          <article className="about-scope-card">
            <div className="about-card-label">Current scope</div>
            <h2>Canada first.</h2>
            <p>
              The MVP focuses on Canadian startup compliance, with particular
              attention to federal and Ontario obligations. Coverage is
              intentionally focused and may expand to additional provinces and
              topics later.
            </p>
          </article>

          <article className="about-disclaimer-card">
            <span className="about-disclaimer-mark">
              <ShieldMark />
            </span>
            <div>
              <div className="about-card-label">Important disclaimer</div>
              <h2>Research, not professional advice.</h2>
              <p>
                Provision does not provide legal, tax, accounting, or other
                professional advice. It is not a law firm and does not replace
                a lawyer or accountant.
              </p>
              <p>
                Consult qualified professionals before making decisions that
                involve legal, tax, employment, or regulatory risk.
              </p>
            </div>
          </article>
        </section>

        <section className="about-stack-section" aria-labelledby="stack-heading">
          <div>
            <div className="about-card-label">Project note</div>
            <h2 id="stack-heading">Built for grounded research.</h2>
            <p>
              Provision combines a Python retrieval pipeline and API with a
              responsive Next.js interface. LangSmith supports tracing and
              evaluation as the system develops.
            </p>
          </div>
          <div className="about-stack-list" aria-label="Technology stack">
            {technologies.map((technology) => (
              <span key={technology}>{technology}</span>
            ))}
          </div>
        </section>
      </div>

      <footer className="footer-note about-footer">
        <span className="status-dot" />
        General information, not legal or accounting advice
      </footer>
    </main>
  );
}
