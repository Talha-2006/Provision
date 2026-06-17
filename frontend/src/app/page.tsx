"use client";

import Image from "next/image";
import {
  FormEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import MobileNav from "./mobile-nav";

const suggestions = [
  "Do federally incorporated Canadian corporations need to file annual returns?",
  "Does PIPEDA apply to a SaaS startup that collects customer emails?",
  "What should I know before hiring my first employee in Canada?",
];

type Citation = {
  title: string;
  url: string;
  chunk_id: string;
  topic: string;
  jurisdiction: string;
  province: string;
};

type ProvisionResponse = {
  answer: string;
  checklist: string[];
  citations: Citation[];
  risk_level: "low" | "medium" | "high";
  professional_help_recommended: boolean;
  insufficient_context: boolean;
};

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
  const disclaimerDialogRef = useRef<HTMLDialogElement>(null);
  const requestController = useRef<AbortController | null>(null);
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState<string | null>(
    null,
  );
  const [response, setResponse] = useState<ProvisionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const dialog = disclaimerDialogRef.current;

    if (dialog && !dialog.open) {
      dialog.showModal();
    }

    return () => {
      requestController.current?.abort();

      if (dialog?.open) {
        dialog.close();
      }
    };
  }, []);

  function acceptDisclaimer() {
    disclaimerDialogRef.current?.close();
  }

  async function askQuestion() {
    const nextQuestion = question.trim();

    if (!nextQuestion || isLoading) {
      return;
    }

    setSubmittedQuestion(nextQuestion);
    setQuestion("");
    setResponse(null);
    setError(null);
    setIsLoading(true);

    requestController.current?.abort();
    const controller = new AbortController();
    requestController.current = controller;

    try {
      const apiResponse = await fetch("/api/ask", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: nextQuestion,
          k: 5,
        }),
        signal: controller.signal,
      });

      const data = (await apiResponse.json()) as
        | ProvisionResponse
        | { detail?: string };

      if (!apiResponse.ok) {
        throw new Error(
          "detail" in data && data.detail
            ? data.detail
            : "Provision could not generate an answer.",
        );
      }

      setResponse(data as ProvisionResponse);
    } catch (requestError) {
      if (
        requestError instanceof DOMException &&
        requestError.name === "AbortError"
      ) {
        return;
      }

      setError(
        requestError instanceof Error
          ? requestError.message
          : "Provision could not generate an answer.",
      );
    } finally {
      if (requestController.current === controller) {
        requestController.current = null;
        setIsLoading(false);
      }
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    askQuestion();
  }

  function handleQuestionKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      askQuestion();
    }
  }

  function resetConversation() {
    requestController.current?.abort();
    requestController.current = null;
    setQuestion("");
    setSubmittedQuestion(null);
    setResponse(null);
    setError(null);
    setIsLoading(false);
  }

  return (
    <main
      className={`site-shell ${submittedQuestion ? "conversation-active" : ""}`}
    >
      <div className="background-grid" />
      <div className="red-haze red-haze-top" />
      <div className="red-haze red-haze-center" />

      <nav className="topbar" aria-label="Main navigation">
        <a
          className="brand"
          href="#"
          aria-label="Provision home"
          onClick={resetConversation}
        >
          <span className="brand-mark">
            <ShieldMark />
          </span>
          <span>PROVISION</span>
        </a>

        <div className="nav-actions">
          <div className="nav-links">
            <a href="/about">About</a>
            <a href="/sources">Sources</a>
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
          <MobileNav />
        </div>
      </nav>

      <section
        className={`hero ${submittedQuestion ? "hero-chatting" : ""}`}
        aria-labelledby="hero-heading"
      >
        <div
          className="intro-content"
          aria-hidden={Boolean(submittedQuestion)}
        >
          <div className="eyebrow">
            <span className="eyebrow-dot" />
            Citation-grounded compliance research
          </div>

          <h1 id="hero-heading">
            Build your startup.
            <span>Know the rules.</span>
          </h1>

          <p className="hero-copy">
            Source-backed answers for Canadian startup compliance, from
            incorporation to your first hire.
          </p>
        </div>

        <div
          className="conversation"
          aria-live="polite"
          aria-busy={isLoading}
        >
          {submittedQuestion && (
            <>
              <div className="message-row message-row-user">
                <div className="message-block">
                  <span className="message-author">You</span>
                  <div className="user-message">{submittedQuestion}</div>
                </div>
              </div>

              <div className="message-row message-row-provision">
                <span className="assistant-mark">
                  <ShieldMark />
                </span>
                {isLoading && (
                  <div className="loading-response">
                    <div className="loading-heading">
                      <span>Provision is researching</span>
                      <span className="loading-dots" aria-hidden="true">
                        <i />
                        <i />
                        <i />
                      </span>
                    </div>
                    <p>Reviewing official federal and provincial sources</p>
                    <div className="answer-skeleton" aria-hidden="true">
                      <span />
                      <span />
                      <span />
                    </div>
                  </div>
                )}

                {error && (
                  <div className="answer-error" role="alert">
                    <strong>Unable to generate an answer</strong>
                    <p>{error}</p>
                  </div>
                )}

                {response && (
                  <article className="answer-response">
                    <div className="answer-heading">
                      <span>Provision</span>
                    </div>

                    {response.insufficient_context && (
                      <div className="answer-notice">
                        The available sources may be insufficient for a complete
                        answer.
                      </div>
                    )}

                    <div className="answer-copy">{response.answer}</div>

                    {response.citations.length > 0 && (
                      <section className="answer-section">
                        <h2>Sources</h2>
                        <div className="answer-citations">
                          {response.citations.map((citation, index) => (
                            <a
                              href={citation.url}
                              key={citation.chunk_id}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <span>{index + 1}</span>
                              <div>
                                <strong>{citation.title}</strong>
                                <small>
                                  {citation.jurisdiction}
                                  {citation.province !== "Not available"
                                    ? ` · ${citation.province}`
                                    : ""}
                                </small>
                              </div>
                            </a>
                          ))}
                        </div>
                      </section>
                    )}

                  </article>
                )}
              </div>
            </>
          )}
        </div>

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
                onKeyDown={handleQuestionKeyDown}
                placeholder="Ask about incorporation, taxes, hiring, permits..."
              />
              <button
                type="submit"
                aria-label="Ask Provision"
                disabled={!question.trim() || isLoading}
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

        {!submittedQuestion && (
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
        )}
      </section>

      <footer className="footer-note">
        <span className="status-dot" />
        General information, not legal or accounting advice
      </footer>

      <dialog
        ref={disclaimerDialogRef}
        className="legal-dialog"
        aria-labelledby="legal-dialog-title"
        aria-describedby="legal-dialog-description"
        onCancel={(event) => event.preventDefault()}
      >
        <div className="legal-dialog-card">
          <span className="legal-dialog-mark">
            <ShieldMark />
          </span>

          <div className="legal-dialog-eyebrow">Before you continue</div>
          <h2 id="legal-dialog-title">Important information</h2>
          <p id="legal-dialog-description" className="legal-dialog-lead">
            Provision provides general, citation-grounded compliance research.
            It is not a lawyer, law firm, accountant, or substitute for advice
            from a qualified professional.
          </p>

          <ul className="legal-dialog-points">
            <li>
              Information may be incomplete, inaccurate, or out of date, and
              may not apply to your circumstances or jurisdiction.
            </li>
            <li>
              Using Provision does not create a lawyer-client,
              accountant-client, fiduciary, or other professional relationship.
            </li>
            <li>
              Do not rely on Provision as definitive legal, tax, accounting,
              employment, or regulatory advice, or as confirmation that you are
              compliant.
            </li>
            <li>
              Verify important information in the cited official sources and
              consult a qualified lawyer or accountant before acting on
              high-risk matters or deadlines.
            </li>
          </ul>

          <button
            className="legal-dialog-button"
            type="button"
            onClick={acceptDisclaimer}
            autoFocus
          >
            I understand and agree to continue
          </button>
          <p className="legal-dialog-footnote">
            By continuing, you acknowledge these limitations.
          </p>
        </div>
      </dialog>
    </main>
  );
}
