"""Generate a centered 1024x1024 OXK Pixel logo composed of tiny glowing characters."""
from pathlib import Path
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "out" / "brand"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_SIZE = 4096  # render high-res, then downscale
FINAL_SIZE = 1024
PATTERN = "OXK"
BACKGROUND = (2, 5, 10)
FOREGROUND = (0, 230, 255)
LETTER_SPACING = -0.08  # relative to font size
TARGET_FILL_RATIO = 0.72  # height coverage for main word
BLOCK_SIZE = 14  # mosaic grid size at BASE_SIZE resolution
INNER_GLOW_RADIUS = 22
OUTER_GLOW_RADIUS = 96
AURA_STRENGTH = 160
VIGNETTE_STRENGTH = 90
DEPTH_OFFSET = 3

FONT_CANDIDATES = [
    "C:/Windows/Fonts/seguisb.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/consola.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def measure_char(font: ImageFont.FreeTypeFont, ch: str) -> tuple[int, int]:
    try:
        bbox = font.getbbox(ch)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return w, h
    except Exception:
        dummy = Image.new("L", (1, 1))
        draw = ImageDraw.Draw(dummy)
        return draw.textsize(ch, font=font)


def layout_text(canvas_size: int, text: str) -> tuple[Image.Image, ImageFont.FreeTypeFont, list[tuple[str, int, int]], tuple[int, int]]:
    margin = int(canvas_size * (1 - TARGET_FILL_RATIO) / 2)
    lo, hi = 10, canvas_size
    best_font = load_font(lo)
    best_metrics: list[tuple[str, int, int]] = []
    best_w = best_h = 0

    while lo <= hi:
        mid = (lo + hi) // 2
        font = load_font(mid)
        metrics = []
        total_w = 0
        max_h = 0
        for ch in text:
            w, h = measure_char(font, ch)
            metrics.append((ch, w, h))
            total_w += w
            max_h = max(max_h, h)
        letter_spacing = int(mid * LETTER_SPACING)
        total_w += letter_spacing * (len(text) - 1)

        if max_h <= canvas_size - margin * 2 and total_w <= canvas_size - margin * 2:
            best_font = font
            best_metrics = metrics
            best_w = total_w
            best_h = max_h
            lo = mid + 1
        else:
            hi = mid - 1

    canvas = Image.new("L", (canvas_size, canvas_size), 0)
    draw = ImageDraw.Draw(canvas)
    letter_spacing = int(best_font.size * LETTER_SPACING)
    x = (canvas_size - best_w) // 2
    y = (canvas_size - best_h) // 2
    for idx, (ch, w, h) in enumerate(best_metrics):
        draw.text((x, y), ch, fill=255, font=best_font)
        x += w + letter_spacing
    return canvas, best_font, best_metrics, (best_w, best_h)


def build_mosaic(mask: Image.Image, font: ImageFont.FreeTypeFont) -> tuple[Image.Image, Image.Image]:
    w, h = mask.size
    mosaic = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    depth_color = (4, 12, 20, 180)
    draw = ImageDraw.Draw(mosaic)
    glow_mask = Image.new("L", (w, h), 0)
    glow_draw = ImageDraw.Draw(glow_mask)

    bbox = mask.getbbox()
    if not bbox:
        return mosaic, glow_mask
    x0, y0, x1, y1 = bbox

    start_x = x0 - (x0 % BLOCK_SIZE)
    start_y = y0 - (y0 % BLOCK_SIZE)
    end_x = x1 + (BLOCK_SIZE - (x1 - start_x) % BLOCK_SIZE) % BLOCK_SIZE
    end_y = y1 + (BLOCK_SIZE - (y1 - start_y) % BLOCK_SIZE) % BLOCK_SIZE

    pattern_index = 0
    for iy in range(start_y, end_y, BLOCK_SIZE):
        for ix in range(start_x, end_x, BLOCK_SIZE):
            cx = min(w - 1, ix + BLOCK_SIZE // 2)
            cy = min(h - 1, iy + BLOCK_SIZE // 2)
            if mask.getpixel((cx, cy)) > 128:
                ch = PATTERN[pattern_index % len(PATTERN)]
                pattern_index += 1
                cw, ch_h = measure_char(font, ch)
                px = ix + (BLOCK_SIZE - cw) // 2
                py = iy + (BLOCK_SIZE - ch_h) // 2
                if DEPTH_OFFSET:
                    draw.text((px + DEPTH_OFFSET, py + DEPTH_OFFSET), ch, fill=depth_color, font=font)
                draw.text((px, py), ch, fill=FOREGROUND + (255,), font=font)
                glow_draw.text((px, py), ch, fill=255, font=font)
    return mosaic, glow_mask


def apply_glow(base: Image.Image, mask: Image.Image) -> Image.Image:
    inner = mask.filter(ImageFilter.GaussianBlur(INNER_GLOW_RADIUS))
    outer = mask.filter(ImageFilter.GaussianBlur(OUTER_GLOW_RADIUS))
    inner_layer = Image.new("RGBA", base.size, FOREGROUND + (0,))
    outer_layer = Image.new("RGBA", base.size, FOREGROUND + (0,))
    inner_layer.putalpha(inner)
    outer_layer.putalpha(outer)
    merged = Image.alpha_composite(outer_layer, inner_layer)
    return Image.alpha_composite(merged, base)


def add_aura(image: Image.Image) -> Image.Image:
    w, h = image.size
    aura = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(aura)
    draw.ellipse((w * 0.18, h * 0.18, w * 0.82, h * 0.82), fill=AURA_STRENGTH)
    aura = aura.filter(ImageFilter.GaussianBlur(int(w * 0.12)))
    aura_layer = Image.new("RGBA", (w, h), FOREGROUND + (0,))
    aura_layer.putalpha(aura)
    return Image.alpha_composite(image, aura_layer)


def add_vignette(image: Image.Image) -> Image.Image:
    w, h = image.size
    vign = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(vign)
    draw.ellipse((-w * 0.25, -h * 0.25, w * 1.25, h * 1.25), fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(int(w * 0.18)))
    mask = ImageChops.invert(vign)
    dark = Image.new("RGBA", (w, h), (0, 0, 0, VIGNETTE_STRENGTH))
    return Image.composite(image, Image.alpha_composite(dark, image), mask.convert("L"))


def main() -> None:
    mask, mosaic_font, _metrics, _ = layout_text(BASE_SIZE, "OXK")
    char_font = load_font(max(12, int(BLOCK_SIZE * 1.1)))
    mosaic, glow_mask = build_mosaic(mask, char_font)
    glowing = apply_glow(mosaic, glow_mask)
    halo = add_aura(glowing)

    base = Image.new("RGBA", (BASE_SIZE, BASE_SIZE), BACKGROUND + (255,))
    composed = Image.alpha_composite(base, halo)
    final = add_vignette(composed)
    final = final.resize((FINAL_SIZE, FINAL_SIZE), Image.LANCZOS)
    out_path = OUT_DIR / "logo_1024_centered.png"
    final.save(out_path, dpi=(300, 300))
    print(f"Saved centered logo to: {out_path}")


if __name__ == "__main__":
    main()
