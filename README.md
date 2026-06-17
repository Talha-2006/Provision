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
`POST /retrieve-debug` through Swagger UI when debug endpoints are enabled.
The API uses the existing vector store and does not run ingestion.

`POST /ask` is rate limited by `ASK_RATE_LIMIT`, which defaults to
`5/minute`. `POST /retrieve-debug` is disabled by default with
`ENABLE_DEBUG_ENDPOINTS=false`; set it to `true` for local retrieval debugging.
When enabled, it is rate limited by `DEBUG_RATE_LIMIT`, which defaults to
`3/minute`.

## Run With Docker

From the repository root, build the backend image:

```powershell
docker build -t provision-backend ./backend
```

Run it with the local environment variables:

```powershell
docker run --rm -p 8000:8000 --env-file backend/.env provision-backend
```

The API is available at `http://127.0.0.1:8000`, with Swagger UI at
`http://127.0.0.1:8000/docs`. The existing Chroma vector store is copied into
the image during the build; `.env` is excluded and supplied only at runtime.

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
