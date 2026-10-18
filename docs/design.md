# UI/UX Tasarım Spesifikasyonu: rw4-cmatrix (Redmi Watch 4)

Bu belge, Redmi Watch 4 için geliştirilen **rw4-cmatrix** uygulamasının kesin tasarım kurallarını belirler. Uygulama, klasik cmatrix "matrix dijital yağmuru" efektini tek ekranda, gerçek siyah zeminde ve yalnızca yeşil tonlarıyla yeniden üretir. Saat, tarih, sensör veya ağ verisi yoktur; hiçbir izin istenmez.

## 1. Genel Görsel Dil

### Tema ve Renk Paleti
AMOLED enerji tasarrufu için arka plan tamamen siyahtır (`#000000`, true black). Görsel hiyerarşi renk çeşitliliğiyle değil, tek bir yeşil ailesinin **dört parlaklık kademesiyle** kurulur: kafadaki beyazımsı yeşilden kuyruktaki koyu yeşile.

| Kullanım Alanı | RGB | Hex | Açıklama |
| :--- | :--- | :--- | :--- |
| **Arka Plan** | `(0, 0, 0)` | `#000000` | Saf siyah (True Black) |
| **Gölge 0 — Kafa** | `(208, 255, 224)` | `#D0FFE0` | Beyazımsı parlak yeşil; kolonun en üst karakteri |
| **Gölge 1** | `(0, 230, 118)` | `#00E676` | Kafanın hemen altındaki canlı yeşil |
| **Gölge 2** | `(0, 200, 83)` | `#00C853` | Gövde yeşili |
| **Gölge 3 — Kuyruk** | `(0, 122, 51)` | `#007A33` | Soluk kuyruk yeşili |

### Kritik Cihaz Notu: Metin Görsel Olarak Çizilir
Redmi Watch 4'ün Vela çalışma zamanı `<text>`/`<span>`/`<input>` bileşenleri için **hiçbir okunabilir glif çizmez** (gerçek cihazda doğrulandı; paketlenen bir `@font-face` fontu da etkisizdir). `<image>` ise sorunsuz çizilir. Bu nedenle:

- Görünür her karakter önceden üretilmiş bir PNG'dir; uygulamada statik etiket/başlık görseli yoktur.
- Yağmur, **karakter × gölge** glif atlasından dizilir: her karakterin dört gölge için ayrı şeffaf PNG'si vardır (`src/common/txt/g_<kod noktası hex>_<gölge>.png`). Boş hücreler `blank.png` kullanır.
- Şablonda `for="{{ grid }}"` + `for="{{ $item }}"` + `src="{{ $item }}"` ile hücre başına bir `<image>` çizilir; her tick yalnızca `src` dizeleri değiştirilir.
- Atlas dışı bir karakterin dosyası bulunmaz; karakter havuzuna eklenmeden çizilemez.

Tüm görseller `scripts/gen_assets.py` tarafından belirlenimci biçimde üretilir ve her dosya yazıldıktan sonra geri okunup doğrulanır.

---

## 2. Ekran: Sabit Izgara

Uygulama tek ekrandır ve ekran sabit bir hücre ızgarasıyla kaplanır. Yağmur bu ızgaranın içinde akar; ızgara boyutu çalışma zamanında değişmez.

| Öğe | Değer |
| :--- | :--- |
| **Ekran** | 390 × 450 px (designWidth 390) |
| **Kolon × Satır** | 19 × 17 = **323 hücre** |
| **Hücre** | 20 × 26 px |
| **Izgara alanı** | 380 × 442 px |
| **Sol kenar payı** | 5 px (`.app` padding-left) |
| **Üst kenar payı** | 4 px (`.app` padding-top) |

Yerleşim Vela'nın desteklediği `flex-direction` + `margin`/`padding` ile kurulur (`display` ve `gap` yoktur): `.app` dikey kolon, her `.row` yatay satır, her `.cell` tek bir `<image>`.

```css
.app  { width: 390px; height: 450px; flex-direction: column; align-items: flex-start; background-color: #000000; padding-left: 5px; padding-top: 4px; }
.row  { flex-direction: row; }
.cell { width: 20px; height: 26px; }
```

---

## 3. Animasyon Modeli

Animasyon tek bir `setInterval` ile yürür. Varsayılan tick süresi **240 ms**'dir. Her kolon bağımsız durum taşır: kafa konumu, iz uzunluğu, hız, kesirli biriktirici, bekleme sayacı ve satır başına karakter kodu.

| Parametre | Değer | Davranış |
| :--- | :--- | :--- |
| **Tick** | 240 ms | Tüm kolonlar aynı tick'te ilerler |
| **Hız** | 0.6–1.6 hücre/tick | Kesirli biriktirici (`acc`) 1'i aştıkça kafa bir hücre ilerler |
| **İz (trail)** | 6–14 hücre | Kafanın arkasında görünen dolu hücre sayısı |
| **Bekleme** | 0–25 tick | Ekranı terk eden kolon yeniden başlamadan önce bu kadar boş bekler |
| **Mutasyon** | 0.2 / tick | Aktif kolonda görünür bir glifin rastgele yeniden atanması |
| **Karakter karışımı** | %70 katakana / %30 Latin | `KANA_WEIGHT = 0.7` |

### Gölge Eşlemesi
Kafa ile hücre arasındaki dikey uzaklık `d` olmak üzere:

| Koşul | Gölge | Görünüm |
| :--- | :--- | :--- |
| `d == 0` | 0 | Beyazımsı parlak kafa |
| `d <= 2` | 1 | Canlı yeşil |
| `d <= 5` | 2 | Gövde yeşili |
| `d > 5` (iz sonuna kadar) | 3 | Soluk kuyruk |

İz dışındaki, henüz ulaşılmamış veya beklemedeki hücreler `blank.png` (tam şeffaf 20×26) ile çizilir.

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
- **İçerik:** Tam kanama siyah daire + üzerinde dikey **halfwidth katakana yağmuru izleri**; altta gölge 3 kuyruk, yukarı doğru gölge 2/1 ve en üstte gölge 0 parlak kafa. Simge, uygulamanın kendi görsel dilinin minyatürüdür.
- Not: Başlatıcının koyu zemininde siyah daire pratikte görünmez; okunan şey yeşil yağmur izleridir.
- Simge konumu ve isim hizası başlatıcı tarafından belirlenir; manifestten değiştirilemez.

### `txt/g_<hex>_<shade>.png` (Glif Atlası)
- **Adlandırma:** `g_<küçük hex kod noktası>_<gölge>.png`, örn. `g_ff8a_0.png`, `g_41_3.png`.
- **Boyut:** 20 × 26 px (üretilen ve ekranda gösterilen aynı boyut); kullanılabilir mürekkep alanı 18 × 24 px.
- Şeffaf zemin; glif tam olarak ilgili gölge renginde, ölçülen mürekkep kutusu hücreye yatay/dikey ortalanarak yerleştirilir.
- **Dosya sayısı:** 99 karakter × 4 gölge = 396 dosya + `blank.png` = **397 PNG**.

#### Karakter Seti (99 karakter)
| Grup | Adet | İçerik |
| :--- | :--- | :--- |
| **LATIN** | 43 | `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$+-*=<>` |
| **KANA** | 56 | Halfwidth katakana, **U+FF66..U+FF9D** tam aralığı (küçük formlar dâhil): `ｦ`–`ﾝ` |

Runtime karakter seçimi: `%70` olasılıkla `U+FF66..U+FF9D` aralığından rastgele bir kod noktası, aksi hâlde `LATIN` havuzundan rastgele bir karakter. Atlas, seçilebilecek her kod noktasını kapsamak zorundadır.

### `blank.png`
- 20 × 26 px, tamamen şeffaf. Boş/ulaşılmamış/bekleyen hücreler için tek dosya.

### Fontlar (yalnızca üretim zamanı — pakete girmez)
| Font | Kaynak | Boyut | Kullanım |
| :--- | :--- | :--- | :--- |
| `scripts/assets/ui-subset.ttf` | mevcut subset | ~18–19 px (19'dan gerekirse 18'e düşer; sığmazsa 15'e kadar küçülür) | 43 Latin karakter |
| `scripts/assets/katakana-subset.ttf` | Noto Sans Mono CJK JP'den fontTools ile subset — **SIL OFL** | 26 px (gerekirse 22'ye kadar küçülür) | 56 halfwidth katakana |

Halfwidth katakana dar glifler olduğu için eşit görsel ağırlık sağlamak üzere Latin'den daha büyük puntoda üretilir. Her iki font da yalnızca `gen_assets.py` çalışırken kullanılır.

---

## 5. Performans ve TUNING

323 `<image>` hücresi, cihazın bilinen "yüzlerce görsel ekranı yavaşlatır" sınırının bilinçli olarak üst ucundadır. Bu yüzden:

- **DOM sabittir:** Izgara bir kez kurulur; her tick'te yalnızca `src` dizeleri değiştirilir, düğüm oluşturulmaz veya yok edilmez.
- **Vela JS güvenliği:** `Array.prototype.fill` kullanılmaz; diziler döngüyle doldurulur.
- **Ayarlanabilir sabitler:** `src/pages/index/index.ux` tepesindeki `TUNING` bloğu cihazda ayarlanmak içindir, tahmin için değil:

| Sabit | Varsayılan | Etki |
| :--- | :--- | :--- |
| `COLS` | 19 | Kolon sayısı (genişlik = `COLS × 20` px) |
| `ROWS` | 17 | Satır sayısı (yükseklik = `ROWS × 26` px) |
| `TICK_MS` | 240 | Tick süresi; artırmak yavaşlatır ve yükü azaltır |
| `TRAIL_MIN` / `TRAIL_MAX` | 6 / 14 | İz uzunluğu aralığı |
| `SPEED_MIN` / `SPEED_MAX` | 0.6 / 1.6 | Hız aralığı (hücre/tick) |
| `WAIT_MAX` | 25 | Maksimum bekleme (tick) |
| `MUTATE_CHANCE` | 0.2 | Tick başına glif mutasyonu olasılığı |
| `KANA_WEIGHT` | 0.7 | Katakana payı |

Cihazda akıcı değilse önce `COLS`/`ROWS` düşürülür veya `TICK_MS` artırılır; ardından yeniden derlenir. Izgara boyutu ile `.app`/`.cell` CSS geometrisi birlikte değiştirilmelidir.
