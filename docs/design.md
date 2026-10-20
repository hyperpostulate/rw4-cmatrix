# UI/UX Tasarım Spesifikasyonu: rw4-cmatrix (Redmi Watch 4)

Bu belge, Redmi Watch 4 için geliştirilen **rw4-cmatrix** uygulamasının kesin tasarım kurallarını belirler. Uygulama, klasik cmatrix "matrix dijital yağmuru" efektini tek ekranda, gerçek siyah zeminde ve yalnızca yeşil tonlarıyla yeniden üretir. Saat, tarih, sensör veya ağ verisi yoktur; hiçbir izin istenmez.

## 1. Genel Görsel Dil

### Tema ve Renk Paleti
AMOLED enerji tasarrufu için arka plan tamamen siyahtır (`#000000`, true black). Görsel hiyerarşi renk çeşitliliğiyle değil, tek bir yeşil ailesinin **iki parlaklık kademesiyle** kurulur: kafadaki beyazımsı yeşil ve gövdenin canlı yeşili.

| Kullanım Alanı | RGB | Hex | Açıklama |
| :--- | :--- | :--- | :--- |
| **Arka Plan** | `(0, 0, 0)` | `#000000` | Saf siyah (True Black) |
| **Gölge 0 — Kafa** | `(208, 255, 224)` | `#D0FFE0` | Beyazımsı parlak yeşil; kolonun en üst karakteri |
| **Gölge 1 — Gövde** | `(0, 200, 83)` | `#00C853` | İz boyunca tek düze gövde yeşili |

### Kritik Cihaz Notu: Metin Görsel Olarak Çizilir
Redmi Watch 4'ün Vela çalışma zamanı `<text>`/`<span>`/`<input>` bileşenleri için **hiçbir okunabilir glif çizmez** (gerçek cihazda doğrulandı; paketlenen bir `@font-face` fontu da etkisizdir). `<image>` ise sorunsuz çizilir. Bu nedenle:

- Görünür her karakter önceden üretilmiş bir PNG'dir; uygulamada statik etiket/başlık görseli yoktur.
- Yağmur, **karakter × gölge** glif atlasından dizilir: her karakterin iki gölge için ayrı şeffaf PNG'si vardır (`src/common/txt/g_<kod noktası hex>_<gölge>.png`). Boş hücreler `blank.png` kullanır.
- Şablonda `for="{{ grid }}"` (kolonlar) + `for="{{ $item }}"` (hücreler) + `src="{{ $item }}"` ile hücre başına bir `<image>` çizilir. Veri **kolon-major**dur ve diziler kararlıdır: her tick yalnızca değişen kolonları, kolon başına **tek tam-aralık `splice`** ile yamalar (bkz. §5).
- Atlas dışı bir karakterin dosyası bulunmaz; karakter havuzuna eklenmeden çizilemez.

Tüm görseller `scripts/gen_assets.py` tarafından belirlenimci biçimde üretilir ve her dosya yazıldıktan sonra geri okunup doğrulanır.

---

## 2. Ekran: Sabit Izgara

Uygulama tek ekrandır ve ekran sabit bir hücre ızgarasıyla kaplanır. Yağmur bu ızgaranın içinde akar; ızgara boyutu çalışma zamanında değişmez.

| Öğe | Değer |
| :--- | :--- |
| **Ekran** | 390 × 450 px (designWidth 390) |
| **Kolon × Satır** | 16 × 17 = **272 hücre** |
| **Hücre** | 24 × 26 px |
| **Izgara alanı** | 384 × 442 px |
| **Sol kenar payı** | 5 px (`.app` padding-left) |
| **Üst kenar payı** | 4 px (`.app` padding-top) |

Yerleşim Vela'nın desteklediği `flex-direction` + `margin`/`padding` ile kurulur (`display` ve `gap` yoktur): `.app` yatay kolon dizisi, her `.col` dikey kolon, her `.cell` tek bir `<image>`.

```css
.app  { width: 390px; height: 450px; flex-direction: row; align-items: flex-start; background-color: #000000; padding-left: 5px; padding-top: 4px; }
.col  { flex-direction: column; }
.cell { width: 24px; height: 26px; }
```

---

## 3. Animasyon Modeli

Animasyon tek bir `setInterval` ile yürür. Varsayılan tick süresi **500 ms**'dir. Her kolon bağımsız durum taşır: kafa konumu, iz uzunluğu, hız, kesirli biriktirici, bekleme sayacı ve satır başına karakter kodu.

| Parametre | Değer | Davranış |
| :--- | :--- | :--- |
| **Tick** | 500 ms | Tüm kolonlar aynı tick'te ilerler; cihazda kare ~0,8 sn'de bir işlenir (bkz. §5) |
| **Hız** | 0.2–0.4 hücre/tick | Kesirli biriktirici (`acc`) 1'i aştıkça kafa bir hücre ilerler |
| **İz (trail)** | 6–14 hücre | Kafanın arkasında görünen dolu hücre sayısı |
| **Bekleme** | 0–25 tick | Ekranı terk eden kolon yeniden başlamadan önce bu kadar boş bekler |
| **Mutasyon** | 0.05 / tick | Aktif kolonda görünür bir glifin rastgele yeniden atanması |
| **Karakter karışımı** | %70 katakana / %30 Latin | `KANA_WEIGHT = 0.7` |

### Gölge Eşlemesi
Kafa ile hücre arasındaki dikey uzaklık `d` olmak üzere:

| Koşul | Gölge | Görünüm |
| :--- | :--- | :--- |
| `d == 0` | 0 | Beyazımsı parlak kafa |
| `d > 0` (iz boyunca) | 1 | Gövde yeşili |

İz dışındaki, henüz ulaşılmamış veya beklemedeki hücreler `blank.png` (tam şeffaf 24×26) ile çizilir.

### Durum Matrisi

Tek durum vardır: **sürekli yağmur**. Alt durumlar yalnızca kolon bazındadır:

| Durum | Giriş | Çıkış |
| :--- | :--- | :--- |
| **Aktif** | Tick başlangıcı / bekleme bitişi | Kafa + iz ekranı terk edince |
| **Beklemede** | `head - trail >= ROWS` | `wait` sayacı 0 olunca yeniden aktif |

Timer yaşam döngüsü: `onShow`'da `setInterval` başlar; `onHide` ve `onDestroy`'da `clearInterval` ile durur (pil tasarrufu). İlk kare `onInit` içinde hemen kurulur, böylece uygulama boş ekranla açılmaz.

---

## 4. Varlık (Asset) Spesifikasyonları

### `logo.png` (App Icon)
- **Boyut:** **96×96 px** (bilinçli, tesadüf değil). Başlatıcı, ismin solunda ayırdığı alanın genişliğini simge PNG'sinin piksel boyutundan türetir; **192×192** (Vela dokümanlarının önerdiği boyut) ismi satırın ortasına itiyordu, **96×96** normal konumuna getirdi (cihazda doğrulandı).
- **İçerik:** Tam kanama siyah daire + üzerinde dikey **halfwidth katakana yağmuru izleri**; gövde yeşili (gölge 1) izler ve en üstte gölge 0 parlak kafa. Simge, uygulamanın kendi görsel dilinin minyatürüdür.
- Not: Başlatıcının koyu zemininde siyah daire pratikte görünmez; okunan şey yeşil yağmur izleridir.
- Simge konumu ve isim hizası başlatıcı tarafından belirlenir; manifestten değiştirilemez.

### `txt/g_<hex>_<shade>.png` (Glif Atlası)
- **Adlandırma:** `g_<küçük hex kod noktası>_<gölge>.png`, örn. `g_ff8a_0.png`, `g_41_1.png`.
- **Boyut:** 24 × 26 px (üretilen ve ekranda gösterilen aynı boyut); kullanılabilir mürekkep alanı 22 × 24 px.
- Şeffaf zemin; glif tam olarak ilgili gölge renginde, ölçülen mürekkep kutusu hücreye yatay/dikey ortalanarak yerleştirilir.
- **Dosya sayısı:** 99 karakter × 2 gölge = 198 dosya + `blank.png` = **199 PNG**.

#### Karakter Seti (99 karakter)
| Grup | Adet | İçerik |
| :--- | :--- | :--- |
| **LATIN** | 43 | `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$+-*=<>` |
| **KANA** | 56 | Halfwidth katakana, **U+FF66..U+FF9D** tam aralığı (küçük formlar dâhil): `ｦ`–`ﾝ` |

Runtime karakter seçimi: `%70` olasılıkla `U+FF66..U+FF9D` aralığından rastgele bir kod noktası, aksi hâlde `LATIN` havuzundan rastgele bir karakter. Atlas, seçilebilecek her kod noktasını kapsamak zorundadır.

### `blank.png`
- 24 × 26 px, tamamen şeffaf. Boş/ulaşılmamış/bekleyen hücreler için tek dosya.

### Fontlar (yalnızca üretim zamanı — pakete girmez)
| Font | Kaynak | Boyut | Kullanım |
| :--- | :--- | :--- | :--- |
| `scripts/assets/ui-subset.ttf` | mevcut subset | ~22–23 px (23'ten gerekirse 22'ye düşer; sığmazsa 18'e kadar küçülür) | 43 Latin karakter |
| `scripts/assets/katakana-subset.ttf` | Noto Sans Mono CJK JP'den fontTools ile subset — **SIL OFL** | 26 px (gerekirse 22'ye kadar küçülür) | 56 halfwidth katakana |

Halfwidth katakana dar glifler olduğu için eşit görsel ağırlık sağlamak üzere Latin'den daha büyük puntoda üretilir. Her iki font da yalnızca `gen_assets.py` çalışırken kullanılır.

---

## 5. Performans ve TUNING

272 `<image>` hücresi, cihazın bilinen "yüzlerce görsel ekranı yavaşlatır" sınırının içindedir ve render mimarisi, bu cihazda **ölçülmüş** maliyet modeline göre tasarlanmıştır:

- **Maliyet birimi listedir, hücre değil.** Vela çalışma zamanı, gözlenen bir dizideki her mutasyon için ilgili `for` listesini yeniden render eder (bu cihazda ~0,1 sn/liste). Değişen hücre sayısı ikincildir; diziye **taze bir referans atamak tüm listeyi** yeniden ayarlar.
- **Veri kolon-major ve kararlıdır:** `grid` onInit'te bir kez kurulur; kolon dizileri asla yeniden atanmaz. Her tick, yalnızca gerçekten değişen her kolona **tek tam-aralık `splice`** uygular (`splice.apply` kullanılır, spread yerine — Vela JS güvenliği). Böylece tick başına güncelleme olayı sayısı ≈ değişen kolon sayısıdır.
- **DOM sabittir:** düğüm oluşturulmaz veya yok edilmez; her tick yalnızca hücre `src` dizelerini değiştirir.
- **Vela JS güvenliği:** `Array.prototype.fill` kullanılmaz; diziler döngüyle doldurulur.

Ölçümlü render merdiveni (gerçek cihaz, kare başına süre):

| Yineleme | Render yaklaşımı | Kare süresi |
| :--- | :--- | :--- |
| 1.0.6 | Tüm `grid`'i taze dizilerle yeniden ata | ~7–8 sn |
| 1.0.7–1.0.8 | Değişen hücre başına ayrı `splice` | ~3–4 sn |
| 1.0.9 | Değişen satır başına tam-aralık `splice` | ~2 sn |
| 1.0.10 | Kolon-major: değişen kolon başına `splice` | ~1 sn |
| 1.0.12 | 16 kolon + hız 0.2–0.4 (güncel) | ~0,8 sn |

~0,8 sn, bu yoğunluktaki bir ızgara için pratik donanım tabanıdır. Daha hızlı gitmek ızgarayı küçültmeyi gerektirir ki bu, görünümü gözle görülür biçimde bozar — bilinçli olarak yapılmadı. Canvas alternatifi yoktur: JS API yüzeyi mevcut olmasına karşın hiçbir şey çizmez ve kullanılması çalışma zamanını saatin yeniden başlatacağı kadar sert çökertir (tam bulgu: rw4-poc `docs/findings.md`).

Ayarlanabilir sabitler (`TUNING` bloğu, `src/pages/index/index.ux` tepesinde — cihazda ayarlanmak içindir, tahmin için değil):

| Sabit | Varsayılan | Etki |
| :--- | :--- | :--- |
| `COLS` | 16 | Kolon sayısı (genişlik = `COLS × 24` px) |
| `ROWS` | 17 | Satır sayısı (yükseklik = `ROWS × 26` px) |
| `TICK_MS` | 500 | Tick süresi |
| `TRAIL_MIN` / `TRAIL_MAX` | 6 / 14 | İz uzunluğu aralığı |
| `SPEED_MIN` / `SPEED_MAX` | 0.2 / 0.4 | Hız aralığı (hücre/tick) |
| `WAIT_MAX` | 25 | Maksimum bekleme (tick) |
| `MUTATE_CHANCE` | 0.05 | Tick başına glif mutasyonu olasılığı |
| `KANA_WEIGHT` | 0.7 | Katakana payı |

Izgara boyutu değiştirilirse `.app`/`.col`/`.cell` CSS geometrisi **ve** `scripts/gen_assets.py` içindeki hücre boyutu birlikte değiştirilip atlas yeniden üretilmelidir (glifler ekranda gösterildikleri boyutta üretilir).
