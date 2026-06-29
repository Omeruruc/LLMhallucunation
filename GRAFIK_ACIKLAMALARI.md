# Grafik ve Tablo Bilgilendirmeleri

Bu belge, oluşturulan tüm grafiklerin ve tabloların ne anlama geldiğini, nasıl yorumlanması gerektiğini ve makalede nasıl bir argüman sunmak için kullanılabileceğini açıklar.

**Genel Not:** Tüm analizler, 18 farklı konu alanından toplam 500 sorunun, 4 aşamalı bir yapay zeka ajan sisteminden geçirilmesiyle elde edilen **2000 adet cevabın** incelenmesiyle oluşturulmuştur.

---

### **1. `performans_ozeti.md` (Özet Performans Tablosu)**

-   **Bu Tablo Neyi Anlatıyor?** Dört ajanın sayısal performansının kuş bakışı özetidir. Hız, tutarlılık (medyan süre) ve cevap uzunluğu gibi temel metrikleri bir arada sunar.
-   **Temel Bulgular ve Yorumlar:**
    -   **Hız:** En hızlı ajanın **Ajan 3 (GPT)**, en yavaşların ise **Ajan 4 (Deepseek)** ve **Ajan 1 (Gemini)** olduğu görülmektedir.
    -   **Cevap Uzunluğu:** **Ajan 2 (Claude)**, diğer ajanlardan **iki katından daha uzun** cevaplar üretmektedir. Bu, onun düzeltme görevini çok daha detaylı bir şekilde yerine getirdiğini göstermektedir.
    -   **Tutarlılık:** Ortalama ve medyan süreler arasındaki fark, performans tutarlılığı hakkında bir ipucu verir. Örneğin Ajan 4'ün ortalama ve medyan süreleri arasındaki fark, bazı cevaplarda çok uzun süreler beklediğini, yani daha az tutarlı olduğunu düşündürmektedir.
-   **Makalede Nasıl Kullanılabilir?** "Bulgular" bölümünün başında bu tabloya yer vererek, ajanların genel performans profilleri okuyucuya tanıtılabilir. Hız (GPT) ve detay (Claude) arasında bir ödünleşim (trade-off) olduğu vurgulanabilir.

---

### **Sayısal Analiz Grafikleri**

**Grafik 1: `1_ortalama_cevap_suresi.png`**
-   **Bu Grafik Neyi Anlatıyor?** "Hangi ajan en hızlı?" sorusunu cevaplar. Her bir ajanın 500 soruya verdiği cevapların ortalama süresini (milisaniye cinsinden) karşılaştırır.
-   **Yorum:** GPT'nin hız avantajı ve Deepseek'in yavaşlığı bu grafikte net bir şekilde görülmektedir.

**Grafik 2: `2_ortalama_token_kullanimi.png`**
-   **Bu Grafik Neyi Anlatıyor?** "Hangi ajan en uzun/kısa cevapları veriyor?" sorusunu cevaplar. Ajanların cevap üretirken kullandığı ortalama "token" sayısını karşılaştırır.
-   **Yorum:** Claude'un (Ajan 2) diğer ajanlara kıyasla ne kadar baskın bir şekilde daha uzun ve detaylı cevaplar ürettiği bu grafiğin en çarpıcı bulgusudur. Bu, onun "düzeltici" rolünü ne kadar ciddiye aldığının bir göstergesidir.

**Grafik 3: `3_konu_bazli_cevap_suresi.png`**
-   **Bu Grafik Neyi Anlatıyor?** "Ajanların hızı konuya göre değişiyor mu?" sorusunu cevaplar. Her bir ajanın 18 farklı konu başlığındaki ortalama cevap verme hızını ayrı ayrı gösterir.
-   **Yorum:** Ajanlar arasındaki hız sıralamasının (GPT > Claude > Gemini > Deepseek) çoğu konu alanında büyük ölçüde korunduğu görülecektir. Bu, performans farklarının konuya özel değil, genel bir karakteristik olduğunu gösterir.

**Grafik 4: `4_cevap_suresi_dagilimi.png` (Kutu Grafiği)**
-   **Bu Grafik Neyi Anlatıyor?** "Ajanların hızı ne kadar tutarlı?" sorusunu cevaplar. Her bir ajanın cevap sürelerinin dağılımını (en yavaş, en hızlı, medyan) gösterir. Kısa bir kutu, tutarlı performansı ifade eder.
-   **Yorum:** GPT ve Claude'un kutularının daha kompakt olması, performanslarının daha öngörülebilir olduğunu gösterir. Gemini ve Deepseek'in daha değişken olduğu anlaşılır.

**Grafik 5: `5_korelasyon_isi_haritasi.png`**
-   **Bu Grafik Neyi Anlatıyor?** "Hız ve cevap uzunluğu gibi metrikler arasında bir ilişki var mı?" sorusunu cevaplar.
-   **Yorum:** `GecikmeMS` (hız) ve `CompletionTokens` (cevap uzunluğu) arasındaki pozitif korelasyon, genel olarak daha uzun cevapların daha fazla zaman aldığını matematiksel olarak kanıtlar.

---

### **Niteliksel Analiz Grafikleri (Sistemin Başarısı)**

**Grafik 6: `6_ajan2_duzeltme_basarisi.png`**
-   **Bu Grafik Neyi Anlatıyor?** Ajan 2'nin (Claude), Ajan 1 bir hata ürettiğinde bunu **tespit etme ve düzeltmeye çalışma** görevini yüzde kaç başarıyla yerine getirdiğini gösterir.
-   **Yorum:** %100'lük oran, Ajan 2'nin bir hata olduğunu "fark etme" görevinde hiç fire vermediğini gösterir. Bu grafiğin, yapılan düzeltmenin doğruluğunu ölçmediği, sadece bir "düzeltme girişimi" olduğunu ölçtüğü makalede belirtilmelidir.

**Grafik 8 & 10: `8_ajan3_katki_orani.png` ve `10_ajan2_duzeltme_dogrulugu.png` (Birlikte Yorumlanmalı)**
-   **Bu Grafikler Neyi Anlatıyor?** Bu ikili, sistemin en önemli bulgularından birini ortaya koyar. Grafik 8, denetçi olan Ajan 3'ün (GPT) vakaların **%81.8'inde sürece anlamlı bir katkı yaptığını** gösterir. Grafik 10 ise bu durumu Ajan 2'nin perspektifinden anlatır: Ajan 2'nin yaptığı düzeltmelerin sadece **%18.2'si tek başına yeterli bulunmuş**, geri kalan %81.8'i Ajan 3 tarafından ek bir iyileştirmeye ihtiyaç duymuştur.
-   **Yorum:** Bu bulgu, "halüsinasyonu düzeltmek için tek bir düzeltici ajan yeterli değildir" argümanını çok güçlü bir şekilde destekler. Ajan 3'ün varlığı, sistemin doğruluğunu önemli ölçüde artıran kritik bir adımdır.

**Grafik 7: `7_ajan4_nihai_dogruluk.png`**
-   **Bu Grafik Neyi Anlatıyor?** Tüm sürecin sonunda ortaya çıkan nihai cevabın kalitesini ölçer.
-   **Yorum:** Nihai cevapların hiçbirinin "tamamen yanlış" olmaması, sistemin temel görevini (yanlış bilgiyi engelleme) başardığını gösterir. Cevapların **%43.4'ünün tam doğru**, **%56.6'sının ise kısmen doğru** olması, sistemin çok başarılı olduğunu ancak mükemmel olmadığını kanıtlar.

**Grafik 9: `9_konu_bazli_halusinasyon.png`**
-   **Bu Grafik Neyi Anlatıyor?** Halüsinasyon üreten Ajan 1'in (Gemini), hangi konularda yanlış bilgi üretmeye daha yatkın olduğunu gösterir.
-   **Yorum:** Grafikte belirli konulardaki (örneğin, daha niş veya teknik konular) halüsinasyon oranlarının diğerlerinden daha yüksek çıkması, modelin bilgi tabanındaki zayıf noktaları işaret edebilir. Bu, LLM'lerin bilgi derinliğinin homojen olmadığına dair bir kanıt olarak sunulabilir.
