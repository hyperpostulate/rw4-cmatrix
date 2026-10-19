# rw4-cmatrix — Redmi Watch 4 CMatrix

![Platform](https://img.shields.io/badge/platform-Xiaomi%20Vela-blue)
![Device](https://img.shields.io/badge/device-Redmi%20Watch%204-orange)
![Version](https://img.shields.io/badge/version-1.0.4-green)
![License](https://img.shields.io/badge/license-GPLv3-blue)

A minimal Xiaomi Vela JS quick app (`.rpk`) for the Redmi Watch 4: a faithful **CMatrix** clone — the classic "matrix digital rain" — running on the watch's true-black AMOLED screen. One screen, green glyphs falling in columns, no clock, no date, no permissions.

Built on the **[rw4-poc](https://github.com/hyperpostulate/rw4-poc)** boilerplate — the platform PoC that mapped what a third-party Vela quick app can and cannot do on this device.

Inspired by **cmatrix** by Chris Allegretta (current upstream: [github.com/abishekvashok/cmatrix](https://github.com/abishekvashok/cmatrix)).

* * *

## Table of Contents

- [What this is](#what-this-is)
- [What it shows](#what-it-shows)
- [Install on the Watch](#install-on-the-watch)
- [Build & Run](#build--run)
- [Project Structure](#project-structure)
- [On-device findings](#on-device-findings)
- [Limitations](#limitations)
- [License](#license)
- [Developer](#developer)
- [Contributing](#contributing)

* * *

## What this is

A deliberately tiny app that does one thing well: it recreates cmatrix's falling-character rain on the Redmi Watch 4. It is a pure visual toy — there is no clock face, no sensor input, no network, and no permission request. Under the hood it is also a working demonstration of what a third-party Vela quick app can do on this device.

To build your own app on top of the boilerplate, see the upstream guide: **[rw4-poc → docs/developing.md](https://github.com/hyperpostulate/rw4-poc/blob/main/docs/developing.md)**.

## What it shows

One screen — true black, two shades of green — covered by a fixed grid of **15 columns × 14 rows = 210 cells** (26×32 px each), rendered by a single `<canvas>` (or by 210 `<image>` nodes in fallback mode). Each column is an independent trail of glyphs:

| Property | Behaviour |
| :-- | :-- |
| **Speed** | 1.0–2.2 cells per tick, with a fractional accumulator per column |
| **Trail** | 5–11 cells long: bright head on a uniform green body |
| **Respawn** | A column that leaves the screen idles 0–25 ticks, then starts again |
| **Mutation** | On each tick an active column has a 20% chance to re-roll one visible glyph (cmatrix's flickering-character effect) |
| **Glyphs** | 70% halfwidth katakana / 30% Latin letters, digits and symbols |

Two brightness shades are used: a white-ish green head `(208,255,224)` and the body green `(0,200,83)`. The animation ticks every 240 ms.

No permission is requested: the app only uses a JS timer.

* * *

## Install on the Watch

The `.rpk` is installed over Bluetooth from an Android phone using the **[Notify for Xiaomi](https://play.google.com/store/apps/details?id=com.mc.xiaomi1)** app (Google Play listing "Notify for Xiaomi/Mi Band 8-10", package `com.mc.xiaomi1`, by OneZeroBit). The Redmi Watch 4 is on the app's official compatibility list, and the app's official site documents installing custom VelaJS (`.rpk`) apps this way.

> **Verification status:** verified on a real Redmi Watch 4 — the app installs and runs correctly with this method.

### Prerequisites

- An **Android phone** (iOS cannot install `.rpk` files).
- **Notify for Xiaomi** installed from Google Play.
- The watch paired with Notify: the in-app setup wizard fetches the pairing (auth) key through your Xiaomi account, so Mi Fitness does not need to stay installed.
- Only one app can hold the watch's Bluetooth connection at a time. If Mi Fitness is installed, force-stop it, deny its "Nearby devices" permission, or uninstall it — but **do not un-pair the watch from Mi Fitness before uninstalling**.

### Steps

1. Build the package: `npm run build` → `dist/com.hyperpostulate.rw4cmatrix.debug.<version>.rpk`.
2. Open **Notify for Xiaomi**.
3. Go to **Device**.
4. Select **Third party app**.
5. Select the `.rpk` file (`dist/com.hyperpostulate.rw4cmatrix.debug.<version>.rpk`).
6. Keep the watch near the phone and follow the guided steps.
7. When the installation finishes, **RW4 - CMatrix** appears in the watch's app list.

### Notes

- The debug-signed `.rpk` produced by `npm run build` is fine for this app: Vela only checks the certificate for watch↔phone Interconnect communication, which this app does not use.
- Redmi Watch 4 limits: at most ~20 quick apps installed, and ~87 MB of free space is required for quick-app installs.
- To update, build a new `.rpk` and install it over the same package name (`com.hyperpostulate.rw4cmatrix`). Changing the `package` value installs a **separate** app instead of updating.
- Unverified details: the app version that introduced `.rpk` installs, and whether the feature requires the (about €3, one-time) PRO purchase, are not officially documented. The menu labels above are the English ones; the app itself is localized, but the Turkish labels were not verified.

Sources: [Notify for Xiaomi VelaJS install guide](https://mibandnotify.com/xiaomi-mi-band/notify-xms-app-instructions.php) · [Google Play listing](https://play.google.com/store/apps/details?id=com.mc.xiaomi1)

* * *

## Build & Run

Requirements:

| Requirement | Version / Notes |
| :-- | :-- |
| Node.js | 18+ (tested on v24.12.0) |
| npm | 9+ (tested on 11.6.2) |
| Python 3 + Pillow | Only needed to regenerate the PNG assets (`scripts/gen_assets.py`) |
| Android phone | Only needed to install the `.rpk` onto the watch via **Notify for Xiaomi** (see [Install on the Watch](#install-on-the-watch)) |
| `aiot-toolkit` | Pulled in automatically as a dev dependency (`npm install`) |

```
git clone https://github.com/hyperpostulate/rw4-cmatrix.git
cd rw4-cmatrix
npm install                          # Install the aiot-toolkit toolchain
npm run build                        # Build a debug .rpk into dist/
npm run release                      # Build a release .rpk (requires signing keys)
npm run start                        # aiot start --watch (live development)
python3 scripts/gen_assets.py        # Regenerate the PNG assets from code
```

The toolchain is `aiot-toolkit`. Every glyph asset is generated at exactly the size it is displayed at, which keeps the bundle small (the toolkit's `--enable-image-png8` flag actually makes the bundle *larger* at this asset size, so it is not used). The build produces `dist/com.hyperpostulate.rw4cmatrix.debug.<version>.rpk` — about **145 KB**, of which the 199 PNGs in `src/common/txt/` account for roughly 70 KB. The debug `.rpk` needs no signing; a release package needs `sign/private.pem` and `sign/certificate.pem` (generate with OpenSSL).

### Canvas probe (1.0.4)

Version **1.0.4** replaces the 210 `<image>` cells with a single `<canvas>` node painted via `drawImage` from the same glyph atlas. A probe in `onShow` checks for the canvas node, `getContext('2d')`, `fillRect`/`drawImage` and the global `Image` constructor; if any of them is missing the app automatically falls back to the original image grid, so it still runs on a runtime without canvas support.

**On-device diagnosis:** for the first ~1.5 s (5 ticks) a green strip is drawn across the bottom of the screen. A visible strip means the canvas pipeline works. A permanently black screen — no rain *and* no strip — means the canvas API exists but renders nothing: report it and the fallback will be made permanent.

On-device verification checklist:

1. At launch, does a green strip appear across the bottom for ~1.5 s? (canvas pipeline works)
2. Is the rain drawn as glyph trails (not empty or solid blocks)?
3. Do columns fall at different speeds, pause, and restart?
4. Are both shades visible (bright head and green body)?
5. Does an occasional glyph mutation show up?
6. Is the app smooth? If not, tune the `TUNING` constants at the top of `index.ux` (lower `COLS`/`ROWS` or raise `TICK_MS`) and rebuild.
7. In the launcher, are the icon and the app name in their normal positions?
8. Is the screen permanently black with no strip? Then the canvas API exists but renders nothing — report it; the image-grid fallback can be forced instead.

* * *

## Project Structure

```
rw4-cmatrix/
├── src/
│   ├── manifest.json          # package com.hyperpostulate.rw4cmatrix, name "RW4 - CMatrix", designWidth 390
│   ├── app.ux                 # app entry (onCreate/onDestroy)
│   ├── common/
│   │   ├── logo.png           # launcher icon: matrix rain motif, 96x96 (see On-device findings: icon size moves the app name)
│   │   └── txt/               # generated glyph atlas: g_<hex>_<shade>.png (99 chars x 2 shades) + blank.png
│   └── pages/
│       └── index/
│           └── index.ux       # the whole app: dual renderer (canvas probe + image-grid fallback) + rain logic + TUNING constants
├── scripts/
│   ├── gen_assets.py          # reproducible Pillow generator for every PNG asset
│   └── assets/
│       ├── ui-subset.ttf      # Latin glyph font, generation time only (not shipped)
│       └── katakana-subset.ttf # katakana glyph font, generation time only (OFL; not shipped)
├── docs/
│   └── design.md              # UI/UX design specification (Turkish)
├── dist/                      # build output (.rpk) - gitignored
├── build/                     # intermediate build output - gitignored
├── package.json
├── LICENSE                   # GPLv3 full text
└── README.md
```

### Core Files

| File | Purpose |
| :-- | :-- |
| `src/manifest.json` | Vela app manifest: `package` = `com.hyperpostulate.rw4cmatrix`, `name` = `RW4 - CMatrix`, `deviceTypeList: ["watch"]`, `designWidth: 390`, `features: ["system.router"]` (the app uses no other system API) |
| `src/pages/index/index.ux` | The whole app: dual renderer (single `<canvas>` probe with an image-grid fallback of 210 `<image>` cells), rain simulation (speeds, trails, respawn, mutation, shade mapping) and styles, plus the `TUNING` constants |
| `scripts/gen_assets.py` | Generates the two-shade glyph atlas (198 files), `blank.png` and the launcher icon (a 96x96 matrix-rain motif) deterministically; re-reads every file it writes and asserts dimensions (and non-blank ink for glyphs) |
| `docs/design.md` | The authoritative UI/UX spec (palette, geometry, animation model, asset spec) |

* * *

## On-device findings

Verified on a **real Redmi Watch 4**. Full detail — including the complete system-API table — is in the boilerplate repo: **[rw4-poc → docs/findings.md](https://github.com/hyperpostulate/rw4-poc/blob/main/docs/findings.md)**.

- **Text does not render.** `<text>`/`<span>`/`<input>` paint no readable glyphs and a bundled `@font-face` has no effect, so every visible character is a pre-rendered PNG. This app composes the rain from a per-character glyph atlas: 99 characters × 2 shades = 198 files plus `blank.png`.
- **Which system APIs work.** `@system.device`, `@system.storage`, `@system.brightness`, `@system.app`, `vibrator.vibrate()` and the JS clock work; geolocation (GPS, error `203`), sensor, battery, network, bluetooth, record, fetch and crypto do not.
- **No GNSS or health API** is exposed to quick apps, so a GPS/location quick app is impossible on this device. This app needs neither.
- **`203`** is Vela's *"function not supported"* code (a permission problem would be `400`/`402`); it is not recoverable by the app.
- **Launcher icon size moves the app name.** The launcher reserves a slot whose width follows the icon PNG's pixel size, so the icon also sets where the label starts — and no manifest field controls label position. The **96x96** `logo.png` is deliberate: `192x192` pushed the app name to the middle of the row, while `96x96` kept it in its normal position.

* * *

## Limitations

- **Text must be images.** Adding new characters means extending the character pools in `scripts/gen_assets.py` (`LATIN` / the katakana range) and regenerating the atlas. Characters outside the atlas would not have a matching `g_<hex>_<shade>.png`.
- **Many glyph images slow the app down.** Canvas mode draws the whole grid with one node; the fallback still uses 210 `<image>` elements, inside the known "hundreds of images are slow" warning zone. If either mode feels sluggish on-device, lower `COLS`/`ROWS` or raise `TICK_MS` in the `TUNING` block at the top of `index.ux`, then rebuild.
- **The grid is fixed at runtime.** Canvas mode never touches `this.grid` after `onInit`; the fallback swaps only the `src` strings of a constant set of image nodes. No nodes are created or destroyed. Resizing the grid means editing both the `TUNING` constants and the CSS geometry.
- **`npm audit` reports vulnerabilities in transitive dev dependencies** of `aiot-toolkit`. They are build-time only and do not ship inside the `.rpk`.

* * *

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)** — see the [LICENSE](LICENSE) file for the full license text.

* * *

## Developer

**Mesut ORMANLI**

- Email: [mesutormanli@gmail.com](mailto:mesutormanli@gmail.com)
- GitHub: [@hyperpostulate](https://github.com/hyperpostulate)

* * *

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

* * *

# rw4-cmatrix — Redmi Watch 4 CMatrix

![Platform](https://img.shields.io/badge/platform-Xiaomi%20Vela-blue)
![Device](https://img.shields.io/badge/device-Redmi%20Watch%204-orange)
![Version](https://img.shields.io/badge/version-1.0.4-green)
![License](https://img.shields.io/badge/license-GPLv3-blue)

Redmi Watch 4 için minimal bir Xiaomi Vela JS hızlı uygulaması (`.rpk`): klasik **CMatrix** ("matrix dijital yağmuru") klonu — saatin gerçek siyah AMOLED ekranında yeşil glifler kolonlar hâlinde düşer. Tek ekran, saat/tarih yok, izin yok.

Bu uygulama, bu cihazda bir üçüncü taraf Vela hızlı uygulamasının neler yapayıp yapamayacağını haritalayan platform PoC'si olan **[rw4-poc](https://github.com/hyperpostulate/rw4-poc)** şablonu üzerine inşa edilmiştir.

İlham: Chris Allegretta'nın **cmatrix**'i (güncel kaynak: [github.com/abishekvashok/cmatrix](https://github.com/abishekvashok/cmatrix)).

* * *

## İçindekiler

- [Bu nedir](#bu-nedir)
- [Ne gösterir](#ne-gösterir)
- [Saate Kurulum](#saate-kurulum)
- [Derleme ve Çalıştırma](#derleme-ve-çalıştırma)
- [Proje Yapısı](#proje-yapısı)
- [Cihaz üstü bulgular](#cihaz-üstü-bulgular)
- [Sınırlamalar](#sınırlamalar)
- [Lisans](#lisans)
- [Geliştirici](#geliştirici)
- [Katkıda Bulunma](#katkıda-bulunma)

* * *

## Bu nedir

Tek bir işi iyi yapan, bilinçli olarak çok küçük bir uygulama: cmatrix'in düşen karakter yağmurunu Redmi Watch 4'te yeniden yaratır. Saf görsel bir oyuncaktır — saat kadranı, sensör girdisi, ağ veya izin isteği yoktur. Arka planda aynı zamanda bir üçüncü taraf Vela hızlı uygulamasının bu cihazda neler yapabildiğinin çalışan bir gösterimidir.

Şablonun üzerinde kendi uygulamanızı geliştirmek için kaynak projedeki kılavuza bkz.: **[rw4-poc → docs/developing.md](https://github.com/hyperpostulate/rw4-poc/blob/main/docs/developing.md)**.

## Ne gösterir

Tek ekran — gerçek siyah, iki yeşil tonu — sabit bir ızgarayla kaplanır: **15 kolon × 14 satır = 210 hücre** (her biri 26×32 px); bu ızgara tek bir `<canvas>` ile (yedek modda 210 `<image>` düğümüyle) çizilir. Her kolon bağımsız bir glif izidir:

| Özellik | Davranış |
| :-- | :-- |
| **Hız** | Tick başına 1.0–2.2 hücre; her kolonda kesirli biriktirici |
| **İz (trail)** | 5–11 hücre; parlak kafa, düz yeşil gövde |
| **Yeniden başlama** | Ekrandan çıkan kolon 0–25 tick bekler, sonra yeniden başlar |
| **Mutasyon** | Her tick'te aktif kolonun görünür bir glifini %20 olasılıkla değiştirir (cmatrix'in karakter değiştirme efekti) |
| **Glifler** | %70 halfwidth katakana / %30 Latin harfleri, rakamlar ve semboller |

İki parlaklık tonu kullanılır: beyazımsı yeşil kafa `(208,255,224)` ve gövde yeşili `(0,200,83)`. Animasyon 240 ms'de bir tick'ler.

Hiçbir izin istenmez: uygulama yalnızca bir JS zamanlayıcısı kullanır.

* * *

## Saate Kurulum

`.rpk` dosyası, Android telefonda yüklü **[Notify for Xiaomi](https://play.google.com/store/apps/details?id=com.mc.xiaomi1)** uygulaması (Google Play adı "Notify for Xiaomi/Mi Band 8-10", paket `com.mc.xiaomi1`, geliştirici OneZeroBit) ile Bluetooth üzerinden saate kurulur. Redmi Watch 4, uygulamanın resmî uyumluluk listesinde yer alır; uygulamanın resmî sitesi özel VelaJS (`.rpk`) uygulamalarının bu yolla kurulmasını belgeler.

> **Doğrulama durumu:** gerçek bir Redmi Watch 4 üzerinde doğrulandı — uygulama bu yöntemle sorunsuz kurulup çalışıyor.

### Ön koşullar

- **Android telefon** (iOS ile `.rpk` kurulamaz).
- Google Play'den kurulmuş **Notify for Xiaomi**.
- Saatin Notify ile eşlenmiş olması: uygulamadaki kurulum sihirbazı eşleme (auth) anahtarını Xiaomi hesabınız üzerinden alır; Mi Fitness'in kurulu kalması zorunlu değildir.
- Saatin Bluetooth bağlantısını aynı anda tek uygulama tutabilir. Mi Fitness kuruluysa durdurun, "Yakındaki cihazlar" iznini kaldırın ya da uygulamayı kaldırın — ama **kaldırmadan önce saati Mi Fitness eşleşmesinden ayırmayın**.

### Adımlar

1. Paketi derleyin: `npm run build` → `dist/com.hyperpostulate.rw4cmatrix.debug.<version>.rpk`.
2. **Notify for Xiaomi**'i açın.
3. **Device** bölümüne gidin.
4. **Third party app** seçeneğini seçin.
5. `.rpk` dosyasını (`dist/com.hyperpostulate.rw4cmatrix.debug.<version>.rpk`) seçin.
6. Saati telefonun yakınında tutun ve yönlendirmeli adımları izleyin.
7. Kurulum bitince **RW4 - CMatrix** saatin uygulama listesinde görünür.

### Notlar

- `npm run build` ile üretilen debug imzalı `.rpk` bu uygulama için yeterlidir: Vela sertifikayı yalnızca saat↔telefon Interconnect iletişiminde denetler; bu uygulama Interconnect kullanmaz.
- Redmi Watch 4 sınırları: en fazla ~20 hızlı uygulama kurulabilir ve kurulum için ~87 MB boş alan gerekir.
- Güncelleme için yeni bir `.rpk` derleyip aynı paket adının (`com.hyperpostulate.rw4cmatrix`) üzerine kurun. `package` değerini değiştirmek güncelleme yerine **ayrı** bir uygulama kurar.
- Doğrulanmayan ayrıntılar: `.rpk` kurulumunu ekleyen uygulama sürümü ve özelliğin (yaklaşık 3 €, tek seferlik) PRO satın alımı gerektirip gerektirmediği resmî olarak belgelenmemiştir. Yukarıdaki menü etiketleri İngilizcedir; uygulama Türkçeleştirilmiştir ama Türkçe etiketler doğrulanamamıştır.

Kaynaklar: [Notify for Xiaomi VelaJS kurulum kılavuzu](https://mibandnotify.com/xiaomi-mi-band/notify-xms-app-instructions.php) · [Google Play sayfası](https://play.google.com/store/apps/details?id=com.mc.xiaomi1)

* * *

## Derleme ve Çalıştırma

Gereksinimler:

| Gereksinim | Sürüm / Not |
| :-- | :-- |
| Node.js | 18+ (v24.12.0 ile test edildi) |
| npm | 9+ (11.6.2 ile test edildi) |
| Python 3 + Pillow | Yalnızca PNG varlıklarını yeniden üretmek için gerekir (`scripts/gen_assets.py`) |
| Android telefon | Yalnızca `.rpk` dosyasını **Notify for Xiaomi** ile saate kurmak için gerekir (bkz. [Saate Kurulum](#saate-kurulum)) |
| `aiot-toolkit` | `npm install` ile geliştirme bağımlılığı olarak otomatik gelir |

```
git clone https://github.com/hyperpostulate/rw4-cmatrix.git
cd rw4-cmatrix
npm install                          # aiot-toolkit araç zincirini kur
npm run build                        # dist/ içine debug .rpk derle
npm run release                      # release .rpk derle (imza anahtarları gerekir)
npm run start                        # aiot start --watch (canlı geliştirme)
python3 scripts/gen_assets.py        # PNG varlıklarını koddan yeniden üret
```

Araç zinciri `aiot-toolkit`'tir. Her glif varlığı ekranda gösterildiği boyutta üretilir; bu paketi küçük tutar (araç zincirinin `--enable-image-png8` bayrağı bu varlık boyutunda paketi daha da *büyütür*, bu yüzden kullanılmaz). Derleme `dist/com.hyperpostulate.rw4cmatrix.debug.<version>.rpk` dosyasını üretir — yaklaşık **145 KB**; bunun kabaca 70 KB'ı `src/common/txt/` içindeki 199 PNG'dir. Debug `.rpk` imza gerektirmez; release paketi için `sign/private.pem` ve `sign/certificate.pem` gerekir (OpenSSL ile üretilir).

### Canvas denemesi (1.0.4)

**1.0.4** sürümü 210 `<image>` hücresinin yerine, aynı glif atlasından `drawImage` ile boyanan tek bir `<canvas>` düğümü kullanır. `onShow` içindeki deneme; canvas düğümünü, `getContext('2d')`'yi, `fillRect`/`drawImage`'i ve global `Image` yapıcısını denetler; bunlardan biri yoksa uygulama otomatik olarak özgün görsel ızgarasına döner, böylece canvas desteği olmayan bir çalışma zamanında da çalışır.

**Cihaz üstü teşhis:** ilk ~1,5 saniye (5 tick) boyunca ekranın altında yeşil bir şerit çizilir. Şerit görünüyorsa canvas hattı çalışıyor demektir. Ekran kalıcı olarak siyahsa — ne yağmur ne şerit — canvas API'si var ama hiçbir şey çizmiyor demektir: bildirin, yedek mod kalıcı hâle getirilsin.

Cihaz üstü kontrol listesi:

1. Açılışta ekranın altında ~1,5 saniye yeşil bir şerit görünüyor mu? (canvas hattı çalışıyor)
2. Yağmur glif izleriyle çiziliyor mu (boş veya düz bloklar değil)?
3. Kolonlar farklı hızlarda düşüp duraklamadan sonra yeniden başlıyor mu?
4. İki gölge de görünüyor mu (parlak kafa ve yeşil gövde)?
5. Ara sıra bir glif mutasyonu görünüyor mu?
6. Uygulama akıcı mı? Değilse `index.ux` tepesindeki `TUNING` sabitleriyle ayarlayın (`COLS`/`ROWS` düşürün veya `TICK_MS` artırın) ve yeniden derleyin.
7. Başlatıcıda simge ve uygulama ismi normal konumunda mı?
8. Ekran kalıcı olarak siyah ve şerit yok mu? O zaman canvas API'si var ama hiçbir şey çizmiyor — bildirin; görsel ızgara yedeği kalıcı olarak zorlanabilir.

* * *

## Proje Yapısı

```
rw4-cmatrix/
├── src/
│   ├── manifest.json          # paket com.hyperpostulate.rw4cmatrix, ad "RW4 - CMatrix", designWidth 390
│   ├── app.ux                 # uygulama girişi (onCreate/onDestroy)
│   ├── common/
│   │   ├── logo.png           # başlatıcı simgesi: matrix yağmuru motifi, 96x96 (bkz. Cihaz üstü bulgular: simge boyutu ismi kaydırır)
│   │   └── txt/               # üretilen glif atlası: g_<hex>_<shade>.png (99 karakter x 2 gölge) + blank.png
│   └── pages/
│       └── index/
│           └── index.ux       # uygulamanın tamamı: çift işleyici (canvas denemesi + görsel ızgara yedeği) + yağmur mantığı + TUNING sabitleri
├── scripts/
│   ├── gen_assets.py          # her PNG varlığı için tekrarlanabilir Pillow üreteci
│   └── assets/
│       ├── ui-subset.ttf      # Latin glif fontu, yalnızca üretim zamanı (pakete girmez)
│       └── katakana-subset.ttf # katakana glif fontu, yalnızca üretim zamanı (OFL; pakete girmez)
├── docs/
│   └── design.md              # UI/UX tasarım spesifikasyonu
├── dist/                      # derleme çıktısı (.rpk) - gitignore'da
├── build/                     # ara derleme çıktısı - gitignore'da
├── package.json
├── LICENSE                   # GPLv3 tam metni
└── README.md
```

### Temel Dosyalar

| Dosya | Amaç |
| :-- | :-- |
| `src/manifest.json` | Vela uygulama manifesti: `package` = `com.hyperpostulate.rw4cmatrix`, `name` = `RW4 - CMatrix`, `deviceTypeList: ["watch"]`, `designWidth: 390`, `features: ["system.router"]` (uygulama başka sistem API'si kullanmaz) |
| `src/pages/index/index.ux` | Uygulamanın tamamı: çift işleyici (tek `<canvas>` denemesi ve 210 `<image>` hücreli görsel ızgara yedeği), yağmur benzetimi (hızlar, izler, yeniden başlama, mutasyon, gölge eşlemesi) ve stiller; ayrıca `TUNING` sabitleri |
| `scripts/gen_assets.py` | İki gölgeli glif atlasını (198 dosya), `blank.png`'yi ve başlatıcı simgesini (96x96 matrix yağmuru motifi) belirlenimci biçimde üretir; yazdığı her dosyayı geri okuyup boyutunu (gliflerde ayrıca boş olmadığını) doğrular |
| `docs/design.md` | Yetkili UI/UX spesifikasyonu (palet, geometri, animasyon modeli, varlık spec'i) |

* * *

## Cihaz üstü bulgular

**Gerçek bir Redmi Watch 4** üzerinde doğrulandı. Sistem API tablosunun tamamı dâhil ayrıntılar kaynak projede: **[rw4-poc → docs/findings.md](https://github.com/hyperpostulate/rw4-poc/blob/main/docs/findings.md)**.

- **Metin çizilmiyor.** `<text>`/`<span>`/`<input>` okunabilir glif çizmiyor ve paketlenen `@font-face` etkisiz; bu yüzden her görünür karakter önceden üretilmiş PNG'dir. Bu uygulama yağmuru karakter×gölge glif atlasından dizer: 99 karakter × 2 gölge = 198 dosya artı `blank.png`.
- **Hangi sistem API'leri çalışıyor.** `@system.device`, `@system.storage`, `@system.brightness`, `@system.app`, `vibrator.vibrate()` ve JS saati çalışıyor; geolocation (GPS, hata `203`), sensor, battery, network, bluetooth, record, fetch ve crypto çalışmıyor.
- **GNSS veya sağlık API'si** hızlı uygulamalara açık değildir; bu cihazda bir GPS/konum hızlı uygulaması imkânsızdır. Bu uygulamanın ikisine de ihtiyacı yok.
- **`203`**, Vela'nın *"bu işlev desteklenmiyor"* kodu (izin sorunu olsaydı `400`/`402` olurdu); uygulama tarafından giderilemez.
- **Başlatıcı simge boyutu uygulama ismini kaydırır.** Başlatıcı, genişliği simge PNG'sinin piksel boyutunu izleyen bir alan ayırır; böylece simge ismin nereden başlayacağını da belirler ve ismi konumlandıran bir manifest alanı yoktur. **96x96** `logo.png` bilinçlidir: `192x192` ismi satırın ortasına iterken `96x96` normal konumunda tuttu.

* * *

## Sınırlamalar

- **Metin görsel olmak zorundadır.** Yeni karakter eklemek, `scripts/gen_assets.py` içindeki karakter havuzlarını (`LATIN` / katakana aralığı) genişletmeyi ve atlası yeniden üretmeyi gerektirir. Atlas dışındaki karakterler için eşleşen `g_<hex>_<shade>.png` bulunmaz.
- **Çok sayıda glif görseli uygulamayı yavaşlatır.** Canvas modu tüm ızgarayı tek düğümle çizer; yedek mod ise bilinen "yüzlerce görsel yavaşlatır" uyarı bölgesinde duran 210 `<image>` kullanır. Hangi modda ağır hissedilirse `index.ux` tepesindeki `TUNING` bloğunda `COLS`/`ROWS` düşürün veya `TICK_MS` artırın, sonra yeniden derleyin.
- **Izgara çalışma zamanında sabittir.** Canvas modu `onInit`'ten sonra `this.grid`'e hiç dokunmaz; yedek mod yalnızca sabit sayıda görsel düğümün `src` dizelerini değiştirir. Düğüm oluşturulmaz veya yok edilmez. Izgarayı yeniden boyutlandırmak hem `TUNING` sabitlerini hem de CSS geometrisini düzenlemeyi gerektirir.
- **`npm audit`**, `aiot-toolkit`'in geçişli geliştirme bağımlılıklarında güvenlik açıkları bildirir. Bunlar yalnızca derleme zamanıyla ilgilidir ve `.rpk` paketine dâhil olmaz.

* * *

## Lisans

Bu proje **GNU Genel Kamu Lisansı v3.0 (GPL-3.0)** ile lisanslanmıştır — lisansın tam metni için [LICENSE](LICENSE) dosyasına bakın.

* * *

## Geliştirici

**Mesut ORMANLI**

- E-posta: [mesutormanli@gmail.com](mailto:mesutormanli@gmail.com)
- GitHub: [@hyperpostulate](https://github.com/hyperpostulate)

* * *

## Katkıda Bulunma

1. Depoyu fork edin
2. Bir özellik dalı oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik ekle'`)
4. Dalı push edin (`git push origin feature/yeni-ozellik`)
5. Bir Pull Request oluşturun
