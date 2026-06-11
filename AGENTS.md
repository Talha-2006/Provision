# AGENTS.md

## Project overview

Provision is a citation-grounded RAG system for Canadian startup compliance research.

The goal is to help startup founders ask compliance-related questions and receive source-backed answers, checklists, citations, and professional-help warnings. Provision is not a legal advice tool and should not claim to replace a lawyer or accountant.

## Repository structure

```text
PROVISION/
├── backend/              # Python backend: LangChain, OpenAI, Chroma, FastAPI
│   ├── api/              # FastAPI app
│   ├── evals/            # Evaluation questions and evaluation scripts
│   ├── src/              # RAG pipeline code
│   ├── .env              # Local secrets, never commit
│   └── requirements.txt
│
├── data/
│   └── sources.json      # Public source list and metadata
│
├── docs/
│   ├── architecture.md
│   └── evaluation.md
│
├── .gitignore
├── AGENTS.md
└── README.md
```

## Build priority

Focus on the backend RAG pipeline before building the frontend.

Build in this order:

1. Source loading
2. Text extraction and cleaning
3. Chunking
4. OpenAI embeddings
5. Chroma vector store
6. Retrieval testing
7. Answer generation with citations
8. Guardrails
9. Evaluation
10. FastAPI API
11. Docker/deployment
12. Frontend

Do not create a frontend unless explicitly asked.

## Tech stack

Backend:

* Python
* LangChain
* OpenAI
* ChromaDB
* FastAPI
* Pydantic
* python-dotenv
* BeautifulSoup
* requests
* PyMuPDF
* LangSmith later for tracing/evaluation

Frontend later:

* Next.js
* React
* TypeScript
* Tailwind CSS

## Environment rules

Use `backend/.env` for local secrets.

Never commit:

* `.env`
* OpenAI API keys
* LangSmith API keys
* local vector stores
* raw downloaded data if large
* virtual environments
* `__pycache__`
* `node_modules`

Use `backend/.env.example` for placeholder environment variables.

## Coding conventions

General:

* Keep code simple and readable.
* Prefer small focused modules over large files.
* Add clear function names and docstrings for important pipeline functions.
* Do not over-engineer early versions.
* Avoid adding new dependencies unless they clearly help the current task.

Python:

* Use type hints where practical.
* Use Pydantic models for API request and response schemas.
* Keep RAG logic in `backend/src/`, not directly inside FastAPI route handlers.
* FastAPI routes should call pipeline functions rather than containing retrieval/generation logic directly.

## RAG rules

The RAG system should:

* Use official or high-trust sources first.
* Preserve metadata for every document and chunk.
* Store source title, URL, jurisdiction, province, topic, and source type.
* Return citations with answers.
* Say when retrieved sources are insufficient.
* Avoid unsupported claims.
* Prefer checklists for action-oriented compliance answers.

Do not hide citations. Citations are a core feature of this project.

## Legal/compliance safety rules

Provision must not present itself as a lawyer, law firm, accountant, or legal advice provider.

The system may provide:

* general source-backed compliance research
* summaries of retrieved official sources
* checklists
* risk flags
* recommendations to consult a qualified lawyer or accountant

The system must avoid:

* definitive legal advice for a specific situation
* instructions for avoiding taxes, regulations, or legal obligations
* promises that a document or action is legally sufficient
* claims that the user is fully compliant

Use professional-help warnings for legal, tax, employment, or high-risk business questions.

## Testing and verification

When changing backend code:

* Run the relevant script if it exists.
* Check imports.
* Check that paths work from the expected working directory.
* Do not call paid APIs repeatedly unless necessary.
* Prefer small test runs before full ingestion.

As the project matures, add and use:

```bash
python src/test_retrieval.py
python src/ask.py
python evals/evaluate.py
uvicorn api.main:app --reload
```

Only run commands that exist in the current repo.

## API design rules

FastAPI should expose the RAG system cleanly.

Planned endpoints:

* `GET /health`
* `POST /ask`
* `POST /retrieve-debug`

The `/ask` endpoint should retrieve from an existing vector store and generate an answer.

Do not scrape, chunk, or embed documents inside `/ask`.

## Documentation expectations

Update documentation when behavior changes.

Important docs:

* `README.md` for setup, usage, and project overview
* `docs/architecture.md` for pipeline architecture
* `docs/evaluation.md` for evaluation method and results

README should explain:

* what Provision does
* what it does not do
* tech stack
* architecture
* setup steps
* how to ingest sources
* how to ask a question
* evaluation results when available

## Done means

A task is done only when:

* the code matches the requested change
* obvious errors/import issues are checked
* relevant scripts are run when available
* citations and metadata are preserved for RAG changes
* no secrets or generated junk files are added
* documentation is updated if behavior changed
