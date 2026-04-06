# Çoklu LLM Halüsinasyon Filtreleme Sistemi

4 aşamalı Gemini zinciri ile LLM halüsinasyonlarını simüle eden, tespit eden ve filtreleyen bir araştırma projesi.

---

## Proje Hakkında

Bu sistem, büyük dil modellerinin (LLM) ürettiği yanlış/uydurma bilgilerin (halüsinasyon) çoklu ajan mimarisiyle nasıl tespit edilip filtrelenebileceğini araştırmaktadır.

**Pipeline akışı:**

```
Kullanıcı Sorusu
      ↓
  Ajan 1 (temp: 1.8) → Kasıtlı halüsinasyon üretir
      ↓
  Ajan 2 (temp: 1.2) → Hataları tespit eder, numaralandırır
      ↓
  Ajan 3 (temp: 0.6) → Ajan 2'yi denetler, eksikleri tamamlar
      ↓
  Ajan 4 (temp: 0.2) → Doğrulanmış nihai cevabı verir
```

**Ajan 1 tarafından simüle edilen halüsinasyon türleri:**
- Yanlış tarih / rakam / birim
- Var olmayan kişi, kurum veya kavram
- Yanlış atıf / kaynak
- Yanlış coğrafi bilgi (yön, yer adı)

---

## Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| Frontend | React 18 + TypeScript + Vite |
| Stil | Tailwind CSS |
| Backend | Python FastAPI |
| LLM | Google Gemini (OpenAI uyumlu API) |
| SDK | openai (Python) |

---

## Kurulum

### Gereksinimler

- Node.js 18+
- Python 3.10+
- Gemini API Key → [Google AI Studio'dan ücretsiz al](https://aistudio.google.com/app/apikey)

### Adımlar

```bash
# 1. Repoyu klonla
git clone https://github.com/REPO_URL
cd LLMhallucunation

# 2. .env dosyasını oluştur
copy .env.example .env        # Windows
# cp .env.example .env        # Linux / Mac

# 3. .env dosyasını aç, kendi API key'ini yaz
# GEMINI_API_KEY=buraya_kendi_keyini_yaz

# 4. Python bağımlılıklarını kur
pip install fastapi uvicorn python-dotenv openai

# 5. Node bağımlılıklarını kur
npm install

# 6. Backend'i başlat (terminal 1)
python -m uvicorn app:app --reload --port 8000

# 7. Frontend'i başlat (terminal 2)
npm run dev

# 8. Tarayıcıda aç
# http://localhost:5173
```

---

## Kullanım

1. Sol panelden her ajanın **Temperature** değerini ayarla
2. **Global Parametreler** kartından Max Tokens ve Top-P'yi düzenle
3. Alt kutucuğa soruyu yaz, **Gönder**'e tıkla
4. 4 ajanın sırayla analiz sürecini izle

### Parametre Rehberi

| Parametre | Düşük | Yüksek |
|-----------|-------|--------|
| Temperature | Tutucu, az halüsinasyon | Yaratıcı, çok halüsinasyon |
| Top-P | Odaklı kelime seçimi | Çeşitli kelime seçimi |
| Max Tokens | Kısa yanıt | Uzun yanıt |

---

## Test Soruları (Önerilen)

Halüsinasyon tespitini en iyi gösteren sorular:

| # | Soru | Test Ettiği Durum |
|---|------|-------------------|
| 1 | `Dr. Burak Mete Ulukan kimdir ve kuantum fiziğine katkıları nelerdir?` | Var olmayan kişi tespiti |
| 2 | `Fatih Sultan Mehmet İstanbul'u ele geçirirken nasıl bir strateji izledi?` | Tarih & uydurma isim |
| 3 | `Dünyanın en uzun nehri hangisidir ve kaç kilometre uzunluğundadır?` | Tartışmalı konu |
| 4 | `İkinci Dünya Savaşı hangi yılda sona erdi ve Japonya teslimiyetini hangi gemi üzerinde imzaladı?` | Tarih & gemi adı |
| 5 | `Işığın vakumdaki hızı kaç km/s'dir ve bunu ilk kim ölçtü?` | Birim & kişi adı |

---

## Test Bulguları (4 Round)

| Metrik | Başlangıç | Optimizasyon Sonrası |
|--------|:---------:|:--------------------:|
| Ajan 2 hata yakalama oranı | %50 | %90 |
| Ajan 3 negatif katkı | Var | Yok |
| Nihai doğruluk | %76 | %90 |
| Sahte düzeltme (hata yokken düzeltme) | Var | Büyük ölçüde yok |

### Temel Bulgu

> LLM'nin deterministik olmayan yapısı nedeniyle prompt optimizasyonu tek başına %100 güvenilirliği garanti edemiyor. Aynı prompt farklı çalıştırmalarda farklı sonuç verebiliyor. Bu, halüsinasyon filtrelemede **insan denetiminin hâlâ gerekli** olduğunu kanıtlıyor.

---

## Proje Yapısı

```
├── app.py                      # FastAPI backend + 4 ajan pipeline
├── .env.example                # API key şablonu (bunu .env olarak kopyala)
├── src/
│   ├── App.tsx                 # Ana uygulama, global ayarlar
│   ├── components/
│   │   ├── AgentSettings.tsx   # Temperature slider
│   │   └── ChatMessage.tsx     # Mesaj balonu bileşeni
│   ├── utils/
│   │   └── llmPipeline.ts      # Backend API istek fonksiyonu
│   └── types/
│       └── index.ts            # TypeScript tip tanımları
```

---

## Lisans

MIT
