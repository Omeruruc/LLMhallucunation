# Multi-Model 4-Agent FastAPI Pipeline

FastAPI backend and static web UI for a 4-agent hallucination check pipeline.

- Agent 1 is fixed to Google Gemini for the first draft.
- Agents 2, 3, and 4 are configured by the user from the UI.
- Each agent has its own provider, model, API key, and temperature setting.

## Setup

Python 3.10+ required.

```bash
pip install -r requirements.txt
```

Create `.env`:

```env
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
GROK_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
```

Only `GEMINI_API_KEY` is required for Agent 1. The other keys can also be entered directly in the UI.

`KEYS.txt` is supported as a fallback:

```txt
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
GROK_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
```

## Run

```bash
uvicorn app:app --reload --port 8000
```

Open `http://localhost:8000`.

## Endpoints

- `GET /`
- `GET /api/health`
- `GET /api/providers`
- `POST /api/agent`

Example request:

```json
{
  "agentNumber": 1,
  "question": "Mars'ta su var mi?",
  "previousResponse": "",
  "temperature": 0.7,
  "maxTokens": 2048,
  "topP": 0.9,
  "provider": "gemini",
  "apiKey": "",
  "modelName": "gemini-2.5-flash"
}
```
