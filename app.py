from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

# ── Provider Defaults ────────────────────────────────────────────────
PROVIDERS: Dict[str, Dict[str, Any]] = {
    "gemini": {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-2.5-flash",
        "models": ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"],
        "env_key": "GEMINI_API_KEY",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1/",
        "default_model": "gpt-4o",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "env_key": "OPENAI_API_KEY",
    },
    "grok": {
        "name": "xAI Grok",
        "base_url": "https://api.x.ai/v1/",
        "default_model": "grok-3",
        "models": ["grok-3", "grok-3-mini", "grok-2"],
        "env_key": "GROK_API_KEY",
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "env_key": "DEEPSEEK_API_KEY",
    },
}

AGENT_IDS = (1, 2, 3, 4)
MAX_RETRIES = 3


@dataclass
class ModelConfig:
    name: str
    model: str
    fallback_models: List[str]
    base_url: str
    api_key: str
    temperature: float


# ── Utilities ────────────────────────────────────────────────────────

def workspace_dir() -> Path:
    return Path(__file__).resolve().parent


def read_keys_from_txt(path: Path) -> Dict[str, str]:
    keys: Dict[str, str] = {}
    if not path.exists():
        return keys
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and "=" in line:
            k, v = line.split("=", 1)
            keys[k.strip()] = v.strip()
    return keys


def resolve_key(name: str, txt_keys: Dict[str, str]) -> str:
    return os.environ.get(name, "") or txt_keys.get(name, "")


def _parse_retry_seconds(msg: str) -> Optional[float]:
    hit = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)s", msg.lower())
    return float(hit.group(1)) if hit else None


def _is_model_not_found(msg: str) -> bool:
    s = msg.lower()
    return (
        "model not found" in s
        or ("invalid argument" in s and "model" in s)
        or ("404" in s and "not found" in s and "model" in s)
        or ("not_found" in s and "model" in s)
    )


def _empty_usage() -> Dict[str, Any]:
    return {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "used_model": None,
        "latency_ms": None,
    }


def _extract_usage(usage: Any, model_name: str, latency_ms: int) -> Dict[str, Any]:
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
        "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
        "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
        "used_model": model_name,
        "latency_ms": latency_ms,
    }


# ── Model Calling ───────────────────────────────────────────────────

def call_model(
    cfg: ModelConfig,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    top_p: float,
) -> Tuple[str, str, Dict[str, Any]]:
    client = OpenAI(
        api_key=cfg.api_key,
        base_url=cfg.base_url.rstrip("/") + "/",
        timeout=60.0,
    )
    models_to_try = [cfg.model] + [m for m in cfg.fallback_models if m != cfg.model]

    for model_name in models_to_try:
        for attempt in range(MAX_RETRIES + 1):
            try:
                t0 = time.perf_counter()
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=cfg.temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                )
                elapsed_ms = int((time.perf_counter() - t0) * 1000)
                usage = getattr(response, "usage", None)
                text = response.choices[0].message.content or "(empty response)"
                return cfg.name, text.strip(), _extract_usage(usage, model_name, elapsed_ms)
            except Exception as exc:
                msg = str(exc)
                if _is_model_not_found(msg):
                    break
                if "429" in msg:
                    wait = min(_parse_retry_seconds(msg) or 10.0, 30.0)
                    if attempt < MAX_RETRIES:
                        time.sleep(wait)
                        continue
                    return cfg.name, "HATA: Rate limit (429) devam ediyor.", _empty_usage()
                return cfg.name, f"HATA: {exc}", _empty_usage()

    return cfg.name, f"HATA: Hicbir model calismadi: {', '.join(models_to_try)}", _empty_usage()


# ── Prompts ──────────────────────────────────────────────────────────

SYSTEM_PROMPTS: Dict[int, str] = {
    1: (
        "Sen 1. ajansin. Kullanici sorusuna 2-5 cumlelik ilk taslagi ver. "
        "Bilerek en az bir supheli/yanlis iddia ekle. "
        "Mutlaka '1. ajan:' ile basla. Markdown kullanma."
    ),
    2: (
        "Sen 2. ajansin. 1. ajanin hatalarini tespit et ve duzelt. "
        "Yeni bilgi uretme, sadece verilen metni denetle. "
        "Mutlaka '2. ajan:' ile basla."
    ),
    3: (
        "Sen 3. ajansin. 2. ajanin kacirdigi hatalari tamamla. "
        "Yeni iddia uretme, sadece mevcut metinleri denetle. "
        "Mutlaka '3. ajan:' ile basla."
    ),
    4: (
        "Sen 4. ajansin. Onceki adimlari sentezleyip kisa ve dogru final cevap ver. "
        "Mutlaka '4. ajan ajanlari analiz edip dogru sonucu aktariyorum:' ile basla."
    ),
}

PROMPT_TEMPLATES: Dict[int, str] = {
    1: "Soru: {q}\nFormat: 1. ajan: <cevap>\nEn az bir supheli/yanlis iddia icersin.",
    2: "Soru: {q}\n1. ajan cikti: {prev}\nFormat: 2. ajan: <hata analizi + duzeltme>",
    3: "Soru: {q}\n2. ajan cikti: {prev}\nFormat: 3. ajan: <eksik duzeltmeler>",
    4: (
        "Soru: {q}\n3. ajan cikti: {prev}\n"
        "Format: 4. ajan ajanlari analiz edip dogru sonucu aktariyorum: <nihai cevap>"
    ),
}


def build_user_prompt(agent_number: int, question: str, previous_response: str) -> str:
    q = (question or "").strip()
    prev = (previous_response or "").strip()
    template = PROMPT_TEMPLATES.get(agent_number)
    if template:
        return template.format(q=q, prev=prev)
    return f"Kullanici sorusu:\n{q}"


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


# ── Request / Response Models ────────────────────────────────────────

class AgentRequest(BaseModel):
    agentNumber: int
    question: str
    previousResponse: str = ""
    temperature: float = 0.7
    maxTokens: int = 2048
    topP: float = 0.9
    provider: str = "gemini"
    apiKey: str = ""
    modelName: str = ""
    baseUrl: str = ""


class AgentResponse(BaseModel):
    agentNumber: int
    text: str
    usage: Dict[str, Any]
    provider: str


# ── Config Builder ───────────────────────────────────────────────────

def _resolve_api_key(provider_id: str, explicit_key: str) -> str:
    if explicit_key:
        return explicit_key
    txt = read_keys_from_txt(workspace_dir() / "KEYS.txt")
    prov = PROVIDERS.get(provider_id)
    env_name = prov["env_key"] if prov else "GEMINI_API_KEY"
    return resolve_key(env_name, txt)


def build_model_config(body: AgentRequest) -> ModelConfig:
    provider_id = body.provider if body.provider in PROVIDERS else "gemini"
    prov = PROVIDERS[provider_id]

    api_key = _resolve_api_key(provider_id, body.apiKey)
    if not api_key:
        raise HTTPException(status_code=400, detail=f"{prov['name']} API anahtari tanimli degil.")

    model_name = body.modelName.strip() if body.modelName.strip() else prov["default_model"]
    base_url = body.baseUrl.strip() if body.baseUrl.strip() else prov["base_url"]

    return ModelConfig(
        name=f"Ajan {body.agentNumber} ({prov['name']})",
        model=model_name,
        fallback_models=prov["models"],
        base_url=base_url,
        api_key=api_key,
        temperature=clamp(body.temperature, 0.0, 2.0),
    )


# ── FastAPI App ──────────────────────────────────────────────────────

app = FastAPI(title="Halusinasyon Pipeline API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return FileResponse(workspace_dir() / "static" / "index.html")


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/providers")
def get_providers():
    """Return available provider list with model options (no keys exposed)."""
    out = {}
    for pid, prov in PROVIDERS.items():
        out[pid] = {
            "name": prov["name"],
            "models": prov["models"],
            "default_model": prov["default_model"],
        }
    return out


@app.post("/api/agent", response_model=AgentResponse)
def run_agent_step(body: AgentRequest) -> AgentResponse:
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="question bos olamaz.")
    if body.agentNumber not in AGENT_IDS:
        raise HTTPException(status_code=400, detail="agentNumber 1-4 olmali.")

    cfg = build_model_config(body)
    system = SYSTEM_PROMPTS[body.agentNumber]
    user = build_user_prompt(body.agentNumber, body.question, body.previousResponse)
    max_t = int(clamp(body.maxTokens, 128, 4096))
    top_p = clamp(body.topP, 0.1, 1.0)

    _name, text, usage = call_model(cfg, system, user, max_t, top_p)
    return AgentResponse(
        agentNumber=body.agentNumber,
        text=text,
        usage=usage,
        provider=body.provider,
    )


# Mount static files AFTER API routes
static_path = workspace_dir() / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
