#!/usr/bin/env python3
"""Reproducible PNG asset generator for the CMatrix quick app on Redmi Watch 4.

Why images? The Redmi Watch 4 Vela runtime does not draw text glyphs (verified
on device: <text>, <input type=button> and <input type=text> all paint nothing
or notdef boxes, and a bundled @font-face has no effect), while <image> renders
perfectly. Every visible character is therefore a pre-rendered PNG.

The app is a Matrix-style "digital rain" screen. Runtime code composes strings
from a per-character glyph atlas. Each glyph is generated once per brightness
shade, at exactly its on-screen display size (20x26 px cell):

    src/common/txt/g_<codepoint hex>_<shade>.png

where <codepoint hex> is lowercase (python "%x" % ord(ch)) and <shade> is 0..3
(0 = head white-ish, 3 = dim tail). index.ux maps a character + shade to
'/common/txt/g_' + code.toString(16) + '_' + shade + '.png'. Missing cells use
'/common/txt/blank.png', a fully transparent 20x26 PNG.

Character sets (fonts under scripts/assets/, never shipped):
  - LATIN = "ABC...Z0-9$+-*=<>"  (43 chars)  scripts/assets/ui-subset.ttf
  - KANA  = halfwidth katakana    (56 chars)  scripts/assets/katakana-subset.ttf
    The full range U+FF66..U+FF9D, small forms included (index.ux picks from
    this whole range, so the atlas must cover every codepoint in it). The
    katakana font was subset from Noto Sans Mono CJK JP and is distributed
    here under the SIL Open Font License (OFL).

43 latin + 56 kana = 99 characters = 396 glyph files, plus blank.png = 397
PNGs in src/common/txt/. Every glyph, including the kana cell, must fit the
18x24 ink box inside its 20x26 cell.

Glyph placement is bbox based, never baseline-guessed: the rendered ink is
measured with font.getbbox(), centred horizontally and vertically in the cell,
and re-centred after downsampling so the final on-disk bbox is pixel-symmetric.

Idempotent: src/common/txt/ is wiped before generation, every file is written,
re-opened and verified (size, non-blank ink, shade colour). logo.png is 96x96
and MUST stay 96x96 -- see make_logo().

Run from anywhere:

    python3 scripts/gen_assets.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "src", "common")
TXT_DIR = os.path.join(OUT_DIR, "txt")
LATIN_FONT_PATH = os.path.join(ROOT, "scripts", "assets", "ui-subset.ttf")
KANA_FONT_PATH = os.path.join(ROOT, "scripts", "assets", "katakana-subset.ttf")

# Wipe every generated PNG before writing, so stale assets (old clock glyphs,
# renamed characters) can never linger in the bundle.
if os.path.isdir(TXT_DIR):
    for name in os.listdir(TXT_DIR):
        if name.endswith(".png"):
            os.remove(os.path.join(TXT_DIR, name))
os.makedirs(TXT_DIR, exist_ok=True)

SS = 4  # supersampling factor while drawing; stored assets are 1x

# ---- geometry (assets are generated at their on-screen display size) ----
CELL_W, CELL_H = 20, 26
CELL_INK_W, CELL_INK_H = CELL_W - 2, CELL_H - 2  # 18x24 usable ink box

LATIN_FONT_SIZE = 19         # requested size; drops to 18 because 'W' at 19
LATIN_FONT_MIN = 15          # inks 19px wide and overflows the 18px box
KANA_FONT_SIZE = 26          # halfwidth kana are narrow -> larger size for
KANA_FONT_MIN = 22           # equal visual mass; shrinks if the ink overflows

# ---- palette / shades (0 = head, 3 = dim tail) ----
SHADES = [
    (208, 255, 224, 255),    # 0 bright head, white-ish green
    (0, 230, 118, 255),      # 1
    (0, 200, 83, 255),       # 2
    (0, 122, 51, 255),       # 3 dim tail
]
BLACK = (0, 0, 0, 255)

# ---- character sets ----
LATIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$+-*=<>"
# Full halfwidth katakana range U+FF66..U+FF9D, small forms included: index.ux
# picks chars from randInt(0xFF66, 0xFF9D), so every codepoint needs a glyph.
KANA = "".join(chr(cp) for cp in range(0xFF66, 0xFF9E))

# Launcher icon size in px. Deliberately 96x96, NOT the 192x192 the Vela docs
# recommend: on the Redmi Watch 4 the launcher reserves a slot to the left of
# the app name whose width follows the image's pixel size, so a 192x192 icon
# pushes the name to the middle of the row while 96x96 keeps it in place.
# Verified on device -- do not "fix" this size.
LOGO_SIZE = 96


def _font(path, size):
    return ImageFont.truetype(path, size)


def _glyph_font(path, size, ch, keep_ink=True):
    """Return (font, bbox) for ch at size, shrinking kana until it fits."""
    while True:
        font = _font(path, size)
        bbox = font.getbbox(ch)
        assert bbox is not None and bbox[2] > bbox[0] and bbox[3] > bbox[1], \
            "font has no ink for %r (U+%04X)" % (ch, ord(ch))
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if w <= CELL_INK_W and h <= CELL_INK_H:
            return font, bbox
        floor = KANA_FONT_MIN if path == KANA_FONT_PATH else LATIN_FONT_MIN
        if keep_ink and size > floor:
            size -= 1
            continue
        raise AssertionError(
            "%r (U+%04X) ink %dx%d exceeds %dx%d at font size %d"
            % (ch, ord(ch), w, h, CELL_INK_W, CELL_INK_H, size))


def _save_verified(name, img, size, allow_blank=False):
    assert img.size == size, (name, img.size, size)
    if not allow_blank:
        assert img.getbbox() is not None, "blank image: %s" % name
    path = os.path.join(TXT_DIR, name)
    img.save(path, optimize=True)
    chk = Image.open(path)
    chk.load()
    assert chk.size == size, (name, chk.size, size)
    if not allow_blank:
        assert chk.getbbox() is not None, "blank on disk: %s" % name


def make_glyph(ch, shade):
    """One cell: exact-size 20x26 PNG, ink centred by its measured bbox.

    The glyph is rendered as a coverage mask, downsampled, then coloured with
    the exact shade RGB. Colourising after the resize (instead of resizing an
    RGBA image) keeps every non-transparent pixel at exactly the shade colour;
    Pillow resizes RGBA channels independently and would otherwise fringe the
    glyph with mixed colours. The mask also drops sub-4/255 LANCZOS ringing so
    the ink never spills into the cell border."""
    font_path = KANA_FONT_PATH if ch in KANA else LATIN_FONT_PATH
    size = KANA_FONT_SIZE if font_path == KANA_FONT_PATH else LATIN_FONT_SIZE
    font, bbox = _glyph_font(font_path, size, ch)

    fill = SHADES[shade]
    canvas = (CELL_W * SS, CELL_H * SS)
    mask = Image.new("L", canvas, 0)
    d = ImageDraw.Draw(mask)

    # Supersampled font; position so the glyph's ink box is centred.
    big_font = _font(font_path, size * SS)
    b = big_font.getbbox(ch)
    bw, bh = b[2] - b[0], b[3] - b[1]
    dx = (canvas[0] - bw) / 2.0 - b[0]
    dy = (canvas[1] - bh) / 2.0 - b[1]
    d.text((dx, dy), ch, font=big_font, fill=255)

    mask = mask.resize((CELL_W, CELL_H), Image.LANCZOS)
    mask = mask.point(lambda a: 0 if a < 4 else a)

    # Re-centre at pixel resolution: crop to the actual ink, then paste into a
    # fresh transparent cell. This makes the stored bbox symmetric instead of
    # inheriting sub-pixel error from the downsample.
    ink = mask.getbbox()
    assert ink is not None, "empty glyph: %r shade %d" % (ch, shade)
    gw, gh = ink[2] - ink[0], ink[3] - ink[1]
    assert gw <= CELL_W and gh <= CELL_H, (ch, gw, gh)
    ink_mask = mask.crop(ink)
    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    coloured = Image.new("RGBA", ink_mask.size, fill)
    coloured.putalpha(ink_mask)
    cell.paste(coloured, ((CELL_W - gw) // 2, (CELL_H - gh) // 2))

    _save_verified("g_%x_%d.png" % (ord(ch), shade), cell, (CELL_W, CELL_H))


def make_blank():
    img = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    _save_verified("blank.png", img, (CELL_W, CELL_H), allow_blank=True)


def make_logo():
    """96x96 launcher icon: matrix "kana rain" on a full-bleed black disc.

    The disc is black on the launcher's dark background (effectively invisible)
    so the icon reads as vertical halfwidth-katakana rain trails, dim tail at
    the bottom (shade 3) up through shade 2/1 to a bright shade-0 head on top.
    Drawn with the katakana font. Size is fixed at 96x96 -- see LOGO_SIZE."""
    size = (LOGO_SIZE, LOGO_SIZE)
    n = LOGO_SIZE * SS
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, n - 1, n - 1], fill=BLACK)

    font_size = 20  # nominal px in the 96x96 icon
    font = _font(KANA_FONT_PATH, font_size * SS)

    # (x fraction, bottom y fraction, characters bottom -> top)
    columns = [
        (0.20, 0.80, "ﾊﾋｼﾂ"),
        (0.36, 0.92, "ﾑﾃﾖ"),
        (0.52, 0.74, "ｼﾂﾑﾊﾋ"),
        (0.68, 0.88, "ﾃﾖﾈﾜ"),
        (0.84, 0.70, "ﾊｷﾑﾂ"),
    ]
    step = font_size * 0.92 * SS  # vertical advance between characters

    for xf, yf, chars in columns:
        x = xf * n
        y = yf * n  # centre of the bottom-most glyph
        count = len(chars)
        for i, ch in enumerate(chars):
            # i == 0 is the bottom char; tail shades 3 -> 2 -> 1 up the trail
            # with the bright shade-0 head as the topmost character.
            trail = [3, 3, 2, 1] if count >= 5 else [3, 2, 1]
            shade = 0 if i == count - 1 else trail[i]
            b = font.getbbox(ch)
            bw, bh = b[2] - b[0], b[3] - b[1]
            cx = x + (0.5 if i % 2 else -0.5) * font_size * SS * 0.15
            cy = y - i * step
            d.text((cx - bw / 2.0 - b[0], cy - bh / 2.0 - b[1]), ch,
                   font=font, fill=SHADES[shade])

    img = img.resize(size, Image.LANCZOS)
    path = os.path.join(OUT_DIR, "logo.png")
    img.save(path, optimize=True)
    chk = Image.open(path)
    chk.load()
    assert chk.size == size, (chk.size, size)
    assert chk.getpixel((size[0] // 2, size[1] // 2))[3] == 255, \
        "logo centre must be opaque"


def main():
    make_logo()
    make_blank()
    for ch in LATIN:
        for shade in range(len(SHADES)):
            make_glyph(ch, shade)
    for ch in KANA:
        for shade in range(len(SHADES)):
            make_glyph(ch, shade)

    glyph_files = (len(LATIN) + len(KANA)) * len(SHADES)
    total_files = len(os.listdir(TXT_DIR))
    total_bytes = sum(
        os.path.getsize(os.path.join(TXT_DIR, f)) for f in os.listdir(TXT_DIR)
    )
    print("latin glyphs: %d chars (%d files) from %s"
          % (len(LATIN), len(LATIN) * len(SHADES),
             os.path.basename(LATIN_FONT_PATH)))
    print("kana  glyphs: %d chars (%d files) from %s"
          % (len(KANA), len(KANA) * len(SHADES),
             os.path.basename(KANA_FONT_PATH)))
    print("blank cells: 1 file (blank.png, fully transparent %dx%d)"
          % (CELL_W, CELL_H))
    print("total glyph files: %d (+1 blank = %d PNGs)" % (glyph_files, total_files))
    print("txt/ total size: %.1f KB" % (total_bytes / 1024.0))


if __name__ == "__main__":
    main()
