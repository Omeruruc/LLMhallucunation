"""
Python altyapı: ModelConfig + call_model (OpenAI SDK) ile çoklu sağlayıcı.
React frontend POST /api/agent ile ajan adımlarını çalıştırır.

Çalıştırma:  uvicorn app:app --reload --port 8000
(.env ve isteğe bağlı KEYS.txt proje kökünde)
"""
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
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

# ---------------------------------------------------------------------------
# Veri yapıları
# ---------------------------------------------------------------------------


@dataclass
class ModelConfig:
    name: str
    model: str
    fallback_models: List[str]
    base_url: str
    api_key: str
    temperature: float


# ---------------------------------------------------------------------------
# Anahtar okuma (.env + KEYS.txt — orijinal app.py ile aynı mantık)
# ---------------------------------------------------------------------------


def read_keys_from_txt(path: Path) -> Dict[str, str]:
    keys: Dict[str, str] = {}
    if not path.exists():
        return keys
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        keys[k.strip()] = v.strip()
    return keys


def resolve_key(name: str, txt_keys: Dict[str, str]) -> str:
    return os.environ.get(name, "") or txt_keys.get(name, "")


def workspace_dir() -> Path:
    return Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Tek model çağrısı — 429 için max 3 retry, 60 sn timeout
# ---------------------------------------------------------------------------


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


def call_model(
    cfg: ModelConfig,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    top_p: float,
    status_cb=None,
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Tek API çağrısı. 429 olursa max 3 kez bekle-tekrar dene.
    status_cb varsa her adımda çağırarak durum gösterir.
    """
    base = cfg.base_url.rstrip("/") + "/"
    client = OpenAI(api_key=cfg.api_key, base_url=base, timeout=60.0)
    models_to_try = [cfg.model] + [m for m in cfg.fallback_models if m != cfg.model]

    for model_name in models_to_try:
        for attempt in range(4):
            try:
                if status_cb:
                    if attempt == 0:
                        status_cb(f"{cfg.name} > {model_name} cagriliyor...")
                    else:
                        status_cb(f"{cfg.name} > {model_name} retry {attempt}/3...")

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
                text = response.choices[0].message.content or "(boş cevap)"
                return cfg.name, text.strip(), {
                    "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                    "completion_tokens": getattr(usage, "completion_tokens", None)
                    if usage
                    else None,
                    "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
                    "used_model": model_name,
                    "latency_ms": elapsed_ms,
                }

            except Exception as exc:
                msg = str(exc)

                if _is_model_not_found(msg):
                    if status_cb:
                        status_cb(f"{model_name} bulunamadi (404), siradaki modele geciliyor...")
                    break

                if "429" in msg:
                    wait = _parse_retry_seconds(msg) or 10.0
                    wait = min(wait, 30.0)
                    if attempt < 3:
                        if status_cb:
                            status_cb(
                                f"{cfg.name}: 429 hiz limiti - {wait:.0f}s bekleniyor "
                                f"(deneme {attempt+1}/3)..."
                            )
                        time.sleep(wait)
                        continue
                    return (
                        cfg.name,
                        (
                            "HATA: Hız limiti (429) — 3 retry sonra hâlâ aşılamadı. "
                            "Birkaç dakika bekleyip tekrar dene veya kotanı kontrol et."
                        ),
                        _empty_usage(),
                    )

                return cfg.name, f"HATA: {exc}", _empty_usage()

    return (
        cfg.name,
        f"HATA: Hiçbir model çalışmadı. Deneneler: {', '.join(models_to_try)}",
        _empty_usage(),
    )


# ---------------------------------------------------------------------------
# React pipeline — ajan “eğitimi”: sistem rolleri + adım adım kullanıcı talimatları
# ---------------------------------------------------------------------------

SYSTEM_PROMPTS: Dict[int, str] = {
    1: (
        "Sen 1. ajansın. Rolün: hızlı ve riskli ilk taslak üretmek. "
        "Kullanıcı sorusuna kapsamlı bir cevap ver; cevabın içine en az bir tane "
        "yanlış/şüpheli iddiayı özgüvenli bir dille kat (halüsinasyon simülasyonu). "
        "Halüsinasyon; yanlış tarih, yanlış rakam, gerçekte var olmayan kişi/kurum/kavram "
        "veya yanlış atıf biçiminde olabilir. "
        "Yanıtın 2-5 cümle uzunluğunda olsun. "
        "Mutlaka '1. ajan:' ile başla. "
        "Markdown, başlık, madde işareti kullanma."
    ),
    2: (
        "Sen 2. ajansın. Rolün: 1. ajanın cevabındaki TÜM hataları tek tek yakalayıp düzeltmek. "
        "Her iddiayı sırayla değerlendir: yer adı, yön, tarih, rakam, kişi/kurum adı, birim dahil tüm detayları doğrula. "
        "Eğer bahsedilen bir kişi veya kurum hakkında güvenilir hiçbir kaynak bulamazsan, "
        "'Bu kişi/kurum muhtemelen var değildir' şeklinde açıkça belirt — sadece 'doğrulanamaz' deme. "
        "Eğer bir iddia farklı kaynaklarda çelişkili veya tartışmalıysa (ör. bilimsel literatürde kesin uzlaşı yoksa), "
        "bunu 'Bu konu tartışmalıdır; bazı kaynaklara göre X, bazılarına göre Y' şeklinde belirt. "
        "Yakaladığın her hatayı numaralandırarak listele, ardından doğru bilgiyi gerekçesiyle ver. "
        "1. ajanın bir ifadesi olgusal olarak doğruysa, öznel veya nitelendirici olsa bile hata sayma; sahte düzeltme yapma. "
        "Eğer 1. ajanda gerçek bir hata bulamazsan, bunu açıkça 'Bu bilgi doğru görünmektedir' şeklinde belirt; "
        "hata uydurmak zorunda değilsin. "
        "Yanıtın 2-5 cümle uzunluğunda olsun. "
        "Mutlaka '2. ajan:' ile başla. "
        "KESİNLİKLE yeni iddia veya bilgi üretme; yalnızca 1. ajandaki mevcut içeriği düzelt."
    ),
    3: (
        "Sen 3. ajansın. Rolün: 2. ajanın düzeltmesini denetlemek ve yalnızca MEVCUT hataları tamamlamak. "
        "2. ajanın 'muhtemelen var değildir' demediği ama şüpheli olan kişi/kurum varsa bunu da işaretle. "
        "2. ajanın kaçırdığı yer adı, yön, tarih, rakam veya birim hatası varsa düzelt. "
        "Eğer bir konu gerçekten tartışmalıysa (farklı kaynaklarda farklı cevaplar varsa), "
        "bunu 'Bu konu tartışmalıdır; kesin bir sonuç yoktur' şeklinde belirt — tek taraflı cevap verme. "
        "KESİNLİKLE yeni bilgi, yeni iddia veya yeni kaynak üretme; "
        "metinde olmayan bir içerik eklemek hata sayılır. "
        "Yanıtın 2-5 cümle uzunluğunda olsun. "
        "Mutlaka '3. ajan:' ile başla."
    ),
    4: (
        "Sen 4. ajansın. Rolün: önceki 3 ajanın tartışmasını sentezleyerek kullanıcıya "
        "doğru, eksiksiz ve anlaşılır nihai cevabı vermek. "
        "KESİNLİKLE: önceki ajanlarca 'muhtemelen var değildir' veya 'doğrulanamaz' olarak "
        "işaretlenen kişi, kurum ve kavramları nihai cevaba dahil etme; adlarını bile anma. "
        "Eğer sorudaki kişi/kurum zaten var olmayan biriyse, bunu açıkça 'Bu kişi/kurum "
        "gerçekte mevcut değildir' şeklinde belirt. "
        "Eğer konu tartışmalıysa (farklı kaynaklarda farklı cevaplar varsa), kesin bir cevap verme; "
        "'Bazı kaynaklara göre X, bazılarına göre Y; bu konuda bilimsel bir uzlaşı henüz yoktur' şeklinde belirt. "
        "Önceki ajanların iç tartışma sürecini tekrar etme; yalnızca doğrulanmış bilgiyi sun. "
        "Yanıtın 2-4 cümle uzunluğunda olsun. "
        "Mutlaka '4. ajan ajanları analiz edip doğru sonucu aktarıyorum:' ile başla."
    ),
}


def build_user_prompt(agent_number: int, question: str, previous_response: str) -> str:
    q = (question or "").strip()
    prev = (previous_response or "").strip()

    if agent_number == 1:
        return (
            f"Soru: {q}\n"
            "Format zorunlu: 1. ajan: <cevap>\n"
            "Cevabın içine en az bir yanlış/şüpheli iddia koy (halüsinasyon simülasyonu). "
            "2-5 cümle ile yanıtla."
        )

    if agent_number == 2:
        return (
            f"Soru: {q}\n"
            f"1. ajan çıktısı: {prev}\n"
            "Görev: 1. ajandaki TÜM hatalı iddiaları tek tek belirt (yer adı, yön, tarih, rakam, kişi/kurum dahil). "
            "Bahsedilen kişi/kurum gerçekte yoksa 'muhtemelen var değildir' de. "
            "Her hatayı numaralandır, ardından doğrusunu gerekçesiyle ver. Yeni bilgi üretme.\n"
            "Format zorunlu: 2. ajan: <numaralı hata listesi + düzeltmeler, 2-5 cümle>"
        )

    if agent_number == 3:
        return (
            f"Soru: {q}\n"
            f"2. ajan çıktısı: {prev}\n"
            "Görev: 2. ajanın kaçırdığı hataları düzelt (yer adı, yön, tarih, rakam, kişi/kurum varlığı). "
            "2. ajanın 'muhtemelen var değildir' demediği şüpheli varlıkları işaretle. "
            "KESİNLİKLE yeni bilgi veya iddia ekleme — sadece mevcut hataları tamamla.\n"
            "Format zorunlu: 3. ajan: <değerlendirme + yalnızca eksik düzeltmeler, 2-5 cümle>"
        )

    if agent_number == 4:
        return (
            f"Soru: {q}\n"
            f"3. ajan çıktısı: {prev}\n"
            "Görev: Tüm tartışmayı sentezleyerek kullanıcıya doğru, eksiksiz ve net nihai cevabı ver.\n"
            "Format zorunlu: 4. ajan ajanları analiz edip doğru sonucu aktarıyorum: <nihai cevap, 2-4 cümle>"
        )

    return f"Kullanıcı sorusu:\n{q}"


def clamp_temp(t: float) -> float:
    return max(0.0, min(2.0, t))


def _gemini_model_config(agent_number: int, temperature: float) -> ModelConfig:
    """Dört ajan da aynı GEMINI_API_KEY ve OpenAI-uyumlu Gemini uç noktası ile çalışır."""
    txt = read_keys_from_txt(workspace_dir() / "KEYS.txt")
    key = resolve_key("GEMINI_API_KEY", txt)
    if not key:
        raise HTTPException(
            status_code=400,
            detail="GEMINI_API_KEY tanımlı değil (.env veya KEYS.txt).",
        )
    t = clamp_temp(temperature)
    return ModelConfig(
        name=f"Ajan {agent_number} (Gemini)",
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        fallback_models=["gemini-2.5-flash-lite", "gemini-2.0-flash"],
        base_url=os.environ.get(
            "GEMINI_OPENAI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        ),
        api_key=key,
        temperature=t,
    )


def model_config_for_agent(agent_number: int, temperature: float) -> ModelConfig:
    if agent_number not in (1, 2, 3, 4):
        raise HTTPException(status_code=400, detail=f"Geçersiz ajan: {agent_number}")
    return _gemini_model_config(agent_number, temperature)


# ---------------------------------------------------------------------------
# FastAPI — Vite /api → buraya proxy
# ---------------------------------------------------------------------------


class AgentRequest(BaseModel):
    agentNumber: int
    question: str
    previousResponse: str = ""
    temperature: float = 0.7
    # Ajan 1 yapılandırılmış çıktı + tarama uzun olabilir
    maxTokens: int = 2048
    topP: float = 0.9


class AgentResponse(BaseModel):
    text: str
    usage: Dict[str, Any]


app = FastAPI(title="Halüsinasyon pipeline API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/api/agent", response_model=AgentResponse)
def run_agent_step(body: AgentRequest) -> AgentResponse:
    if not body.question.strip():
        raise HTTPException(status_code=400, detail="question boş olamaz.")
    if body.agentNumber not in (1, 2, 3, 4):
        raise HTTPException(status_code=400, detail="agentNumber 1–4 olmalı.")

    cfg = model_config_for_agent(body.agentNumber, body.temperature)
    system = SYSTEM_PROMPTS[body.agentNumber]
    user = build_user_prompt(body.agentNumber, body.question, body.previousResponse)

    max_t = max(128, min(4096, body.maxTokens))
    top_p = max(0.1, min(1.0, body.topP))

    _name, text, usage = call_model(cfg, system, user, max_t, top_p, status_cb=None)
    return AgentResponse(text=text, usage=usage)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
