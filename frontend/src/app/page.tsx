"use client";

import { FormEvent, useState } from "react";

const suggestions = [
  "Incorporating in Ontario",
  "Hiring my first employee",
  "Canadian sales tax basics",
];

function ArrowIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M5 12h14M13 6l6 6-6 6" />
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

export default function Home() {
  const [question, setQuestion] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
  }

  return (
    <main className="site-shell">
      <div className="background-grid" />
      <div className="red-haze red-haze-top" />
      <div className="red-haze red-haze-center" />

      <nav className="topbar" aria-label="Main navigation">
        <a className="brand" href="#" aria-label="Provision home">
          <span className="brand-mark">
            <ShieldMark />
          </span>
          <span>PROVISION</span>
        </a>

        <div className="nav-links">
          <a href="#how-it-works">How it works</a>
          <a href="#sources">Sources</a>
          <span className="jurisdiction-pill">
            <span className="maple-leaf">✦</span>
            Canada
          </span>
        </div>
      </nav>

      <section className="hero" aria-labelledby="hero-heading">
        <div className="eyebrow">
          <span className="eyebrow-dot" />
          Citation-grounded compliance research
        </div>

        <h1 id="hero-heading">
          Build your company.
          <span>Know the rules.</span>
        </h1>

        <p className="hero-copy">
          Source-backed answers for Canadian startup compliance, from
          incorporation to your first hire.
        </p>

        <div className="prompt-stage">
          <div className="prompt-glow" />
          <form className="prompt-card" onSubmit={handleSubmit}>
            <label htmlFor="compliance-question">
              What do you need to know?
            </label>
            <div className="prompt-row">
              <textarea
                id="compliance-question"
                name="question"
                rows={1}
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="Ask about incorporation, taxes, hiring, permits..."
              />
              <button
                type="submit"
                aria-label="Ask Provision"
                disabled={!question.trim()}
              >
                <ArrowIcon />
              </button>
            </div>
            <div className="prompt-meta">
              <span>
                <kbd>Enter</kbd> to ask
              </span>
              <span>Official sources prioritized</span>
            </div>
          </form>
        </div>

        <div className="suggestions" aria-label="Example questions">
          <span>Try asking</span>
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => setQuestion(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </section>

      <footer className="footer-note">
        <span className="status-dot" />
        General information, not legal or accounting advice
      </footer>
    </main>
  );
}
