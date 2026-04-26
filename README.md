# Gemini 4-Agent FastAPI Backend

Minimal FastAPI backend for a 4-agent Gemini pipeline.

## Setup

Python 3.10+ required.

```bash
pip install -r requirements.txt
```

Create `.env`:

```env
GEMINI_API_KEY=your_key
```

Optional:

- `GEMINI_MODEL` (default: `gemini-2.5-flash`)
- `GEMINI_OPENAI_BASE_URL` (default: Google OpenAI-compatible endpoint)

`KEYS.txt` is also supported as fallback:

```txt
GEMINI_API_KEY=your_key
```

## Run

```bash
uvicorn app:app --reload --port 8000
```

## Endpoints

- `GET /api/health`
- `POST /api/agent`

Example request:

```json
{
  "agentNumber": 1,
  "question": "Mars'ta su var mi?",
  "previousResponse": "",
  "temperature": 0.7,
  "maxTokens": 2048,
  "topP": 0.9
}
```
