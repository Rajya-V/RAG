# Knowledge Copilot Frontend

React + Vite single-page app; no login or signup. Palette: Cotton `#EDEBDD`, Cherry Red `#810100`, Maroon `#630000`, Noir Black `#1B1717`.

## Run
1. Open a terminal in this folder.
2. Run `npm install`.
3. Copy `.env.example` to `.env` if needed. Default API: `http://localhost:8000`.
4. Run `npm run dev` and open the URL Vite prints (normally `http://localhost:5173`).

## Expected FastAPI endpoints
- `GET /health`
- `POST /documents/upload` (multipart field `file`)
- `POST /ask/` (JSON: `query`, `top_k`, `document_id`)
- `POST /search/` (JSON: `query`, `top_k`, `document_id`)

If browser requests fail but endpoints work in FastAPI docs, enable CORS in FastAPI for `http://localhost:5173` and `http://127.0.0.1:5173`. Results are rendered from actual API responses; use “View response details” to inspect response shape.
