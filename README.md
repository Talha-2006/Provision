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
