Server for querying Perplexity API by book title

Overview
- Exposes a FastAPI server with endpoints that accept JSON.
- Forwards queries to Perplexity's Chat Completions API and returns the response.

Endpoints
- POST `/ask`
  - Request JSON: `{ "title": "The Adventures of Sherlock Holmes" }` or `{ "query": "..." }`
  - Optional: `{ "model": "..." }` to override model
  - Response JSON: `{ "answer": "...", "model": "...", "usage": { ... }, "raw": { ... } }`

- POST `/ask_text`
  - Request JSON: `{ "key": "<IDENT_TOKEN>", "text": "<book title or hint>", "model": "optional-model" }`
  - Behavior: server composes a Russian prompt asking for exactly 10 labeled lines (free text, not JSON), no bullets or numbers, no blank lines:
    - `Автор: ...`
    - `Страна: ...`
    - `Язык: ...`
    - `Первая публикация: ...`
    - `Годы: ...`
    - `Жанр: ...`
    - `Герои: ...`
    - `Сюжет: ...`
    - `Город: ...`
    - `Контекст: ...`
  - Auth note: field `key` is your client identification token. The server compares it with `CLIENT_IDENT_KEY` from `.env` (simple `str1 == str2`). On mismatch — 401. Perplexity API key is taken from `PERPLEXITY_API_KEY` in `.env`.
  - Response JSON: `{ "answer": "...", "model": "...", "usage": { ... }, "raw": { ... } }`

- POST `/search_text`
  - Request JSON: `{ "key": "<IDENT_TOKEN>", "text": "<query>", "count": 5, "include_snippets": true }`
  - Behavior: calls Perplexity Search API (`/search`) with given query and options.
  - Auth note: same as `/ask_text` — compares `key` to `CLIENT_IDENT_KEY`.
  - Response JSON: `{ "results": [...] }` (raw API response under `results`).

Setup
1) Create `.env` in `server_pplx` (or project root) with:
   PERPLEXITY_API_KEY=your_api_key_here
   CLIENT_IDENT_KEY=your_client_key_here

2) Install deps:
   pip install -r server_pplx/requirements.txt

Run
- Development:
  uvicorn server_pplx.app:app --reload --host 0.0.0.0 --port 8080

Example
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"title":"The Adventures of Sherlock Holmes"}'

curl -X POST http://localhost:8080/ask_text \
  -H "Content-Type: application/json" \
  -d '{"key":"USER-IDENT-123", "text":"The Adventures of Sherlock Holmes"}'

Notes
- Uses env var `PERPLEXITY_API_KEY`. Do not commit real keys.
- Uses env var `CLIENT_IDENT_KEY` to validate `key` from requests.
- Default model: `llama-3.1-sonar-small-128k-online`.
