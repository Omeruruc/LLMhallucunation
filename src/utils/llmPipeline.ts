/**
 * Tüm LLM çağrıları Python FastAPI (app.py) üzerinden yapılır.
 * Geliştirmede Vite /api → http://127.0.0.1:8000 proxy kullanılır.
 * Üretimde .env: VITE_API_BASE_URL=https://api.alanadiniz.com
 */

const JSON_HEADERS = { 'Content-Type': 'application/json' };

function apiUrl(path: string): string {
  const base = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(
    /\/$/,
    ''
  );
  return base ? `${base}${path}` : path;
}

export async function fetchAgentResponse(
  agentNumber: number,
  question: string,
  previousResponse: string,
  temperature: number,
  maxTokens = 768,
  topP = 0.9,
): Promise<string> {
  const res = await fetch(apiUrl('/api/agent'), {
    method: 'POST',
    headers: JSON_HEADERS,
    body: JSON.stringify({
      agentNumber,
      question,
      previousResponse,
      temperature,
      maxTokens,
      topP,
    }),
  });

  const raw = await res.text();
  if (!res.ok) {
    let detail = raw.slice(0, 500);
    try {
      const j = JSON.parse(raw) as { detail?: string | unknown };
      if (typeof j.detail === 'string') {
        detail = j.detail;
      }
    } catch {
      /* metin olduğu gibi */
    }
    throw new Error(detail || res.statusText);
  }

  const data = JSON.parse(raw) as { text: string };
  if (typeof data.text !== 'string') {
    throw new Error('Beklenmeyen API yanıtı.');
  }
  return data.text.trim();
}
