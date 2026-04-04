# LLM Hallucination — Gemini Multi-Temperature

Ayni soruyu Gemini API'ye farkli sicaklik (temperature) degerleriyle gonderip cevaplari karsilastirir.
Her istegin suresi (ms) ve token tuketimi gosterilir.

## Kurulum

Python 3.10+ gerekli.

```bash
pip install -r requirements.txt
```

## API Key

`.env` dosyasi olustur ve Gemini anahtarini ekle:

```
GEMINI_API_KEY=senin_anahtarin
```

Alternatif olarak `KEYS.txt` icinde `GEMINI_API_KEY=...` satirini da okur.

## Calistirma

```bash
python -m streamlit run app.py
```

Tarayicida `http://localhost:8501` adresinde acilir.

## Ozellikler

- Tek Gemini anahtari, 3 farkli temperature ile sirali istek
- Her cevap icin API suresi (ms), prompt/completion/total token bilgisi
- 429 hiz limiti icin otomatik retry (max 3 deneme)
- Model bulunamazsa (404) yedek modele gecis
- Canli durum paneli — hangi istek yapiliyor, bekleniyor mu gorunur
- max_tokens, top_p, model id, base URL arayuzden ayarlanabilir
