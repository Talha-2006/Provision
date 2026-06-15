# Provision

Provision is a citation-grounded RAG system for Canadian startup compliance
research. It provides general, source-backed information and does not replace a
qualified lawyer or accountant.

## Ask A Question

After ingestion has created `backend/vectorstore/chroma`, add
`OPENAI_API_KEY` to `backend/.env`, then run from the `backend` directory:

```powershell
python src/ask.py "Do federally incorporated companies need to file annual returns?"
```

Use `--k` to change the number of retrieved chunks:

```powershell
python src/ask.py "What annual filings are required?" --k 8
```

The CLI prints a source-grounded answer, checklist, risk level, professional-help
recommendation, insufficient-context flag, and citation metadata.

## Run The API

From the `backend` directory, start the FastAPI development server:

```powershell
uvicorn api.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to test `GET /health`, `POST /ask`, and
`POST /retrieve-debug` through Swagger UI. The API uses the existing vector
store and does not run ingestion.

## Run The Frontend

The frontend is a Next.js application. From the `frontend` directory:

```powershell
npm install
npm run dev
```

Open `http://localhost:3000` to view the Provision landing page. Keep the
FastAPI server running at `http://127.0.0.1:8000`; questions are sent to
`POST /ask` with `k=5`, then the answer and citations are displayed on the main
page.

To use a different backend URL, copy `frontend/.env.example` to
`frontend/.env.local` and change `PROVISION_API_URL`. Visit
`http://localhost:3000/sources` to browse the enabled research sources defined
in `data/sources.json`, or `http://localhost:3000/about` to learn about the
project, its scope, and how its retrieval pipeline works.
