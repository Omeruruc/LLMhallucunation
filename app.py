import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

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
# Anahtar okuma
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

# ---------------------------------------------------------------------------
# Tek model çağrısı — basit, 429 için max 3 retry, 60 sn timeout
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
    status_cb varsa her adımda çağırarak kullanıcıya durum gösterir.
    """
    client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url, timeout=60.0)
    models_to_try = [cfg.model] + [m for m in cfg.fallback_models if m != cfg.model]

    for model_name in models_to_try:
        for attempt in range(4):  # 0,1,2,3 → ilk deneme + 3 retry
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
                    "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                    "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
                    "used_model": model_name,
                    "latency_ms": elapsed_ms,
                }

            except Exception as exc:
                msg = str(exc)

                if _is_model_not_found(msg):
                    if status_cb:
                        status_cb(f"{model_name} bulunamadi (404), siradaki modele geciliyor...")
                    break  # bu modeli bırak, sıradakine geç

                if "429" in msg:
                    wait = _parse_retry_seconds(msg) or 10.0
                    wait = min(wait, 30.0)
                    if attempt < 3:
                        if status_cb:
                            status_cb(f"{cfg.name}: 429 hiz limiti - {wait:.0f}s bekleniyor (deneme {attempt+1}/3)...")
                        time.sleep(wait)
                        continue
                    return cfg.name, (
                        f"HATA: Hız limiti (429) — 3 retry sonra hâlâ aşılamadı. "
                        f"Birkaç dakika bekleyip tekrar dene veya Google AI Studio kotanı kontrol et."
                    ), _empty_usage()

                return cfg.name, f"HATA: {exc}", _empty_usage()

    return cfg.name, f"HATA: Hiçbir model çalışmadı. Deneneler: {', '.join(models_to_try)}", _empty_usage()

# ---------------------------------------------------------------------------
# Streamlit arayüzü
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Gemini — çoklu sıcaklık", layout="wide")
    st.title("Gemini — aynı soru, farklı temperature")
    st.caption("Tek API anahtarı · sıralı istek · her çağrının ms süresi gösterilir")

    workspace = Path(__file__).resolve().parent
    txt_keys = read_keys_from_txt(workspace / "KEYS.txt")
    gemini_key = resolve_key("GEMINI_API_KEY", txt_keys)

    col_left, col_right = st.columns([2, 1])

    with col_left:
        system_prompt = st.text_area(
            "System prompt",
            value="Sen gerçekçi ve temkinli bir asistansın. Bilmediğin yerde 'emin değilim' de. Maksimum 5 kısa cümle kullan.",
            height=120,
        )
        user_prompt = st.text_area("Soru", placeholder="Soruyu buraya yaz...", height=160)

    with col_right:
        max_tokens = st.slider("max_tokens", 128, 4096, 1024, 64,
                               help="gemini-2.5-flash düşünme tokenları da buna dahil; 1024+ önerilir.")
        top_p = st.slider("top_p", 0.1, 1.0, 0.9, 0.05)
        model_id = st.text_input("Gemini model id", value="gemini-2.5-flash")
        base_url = st.text_input("Base URL", value="https://generativelanguage.googleapis.com/v1beta/openai/")

    key_override = st.text_input("API key (boşsa .env / KEYS.txt)", value="", type="password").strip()
    effective_key = key_override or gemini_key

    st.subheader("Sıcaklık ayarları")
    runs: List[Tuple[bool, float]] = []
    rcols = st.columns(3)
    for i, default_t in enumerate([0.2, 0.6, 1.0]):
        with rcols[i]:
            on = st.checkbox(f"Run {i+1}", value=True, key=f"run_on_{i}")
            t = st.slider(f"Temp {i+1}", 0.0, 1.2, default_t, 0.1, key=f"run_temp_{i}")
            runs.append((on, t))

    gap_s = st.slider("İstekler arası bekleme (sn)", 0.0, 15.0, 4.0, 0.5,
                       help="429 alıyorsan bunu artır.")

    if not st.button("Başlat", type="primary", use_container_width=True):
        return
    if not user_prompt.strip():
        st.warning("Önce soru gir.")
        return
    if not effective_key:
        st.error("GEMINI_API_KEY tanımlı değil.")
        return

    active: List[ModelConfig] = []
    for i, (on, temp) in enumerate(runs):
        if on:
            active.append(ModelConfig(
                name=f"Run {i+1} (T={temp})",
                model=model_id.strip(),
                fallback_models=["gemini-2.5-flash-lite", "gemini-2.0-flash"],
                base_url=base_url.strip(),
                api_key=effective_key,
                temperature=temp,
            ))
    if not active:
        st.error("En az bir çalıştırma seç.")
        return

    results: Dict[str, str] = {}
    usages: Dict[str, Dict[str, Any]] = {}

    status = st.status(f"0/{len(active)} tamamlandı", expanded=True)
    for i, cfg in enumerate(active):
        if i > 0 and gap_s > 0:
            status.update(label=f"{i}/{len(active)} tamamlandı — {gap_s:.0f}s bekleniyor...")
            time.sleep(gap_s)

        def _cb(msg: str, _st=status):
            _st.write(msg)

        name, text, usage = call_model(cfg, system_prompt, user_prompt, max_tokens, top_p, status_cb=_cb)
        results[name] = text
        usages[name] = usage
        lat = usage.get("latency_ms")
        lat_str = f"{lat} ms" if lat is not None else "—"
        status.write(f"{name} tamamlandi ({lat_str})")

    status.update(label=f"{len(active)}/{len(active)} tamamlandı", state="complete", expanded=False)

    st.subheader("Sonuçlar")
    for cfg in active:
        name = cfg.name
        st.markdown(f"### {name}")
        st.write(results.get(name, "—"))
        u = usages.get(name, {})
        lat = u.get("latency_ms")
        lat_str = f"{lat} ms" if lat is not None else "—"
        st.caption(
            f"Süre: **{lat_str}** · "
            f"prompt: {u.get('prompt_tokens')} · completion: {u.get('completion_tokens')} · "
            f"total: {u.get('total_tokens')} · model: {u.get('used_model')}"
        )


if __name__ == "__main__":
    main()
