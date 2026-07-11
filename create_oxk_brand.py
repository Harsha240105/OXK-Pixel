"""
Generate an ultra-HD brand identity set for "OXK Pixel".
Outputs:
 - 1024x1024 avatar (PNG)
 - 2048x2048 master logo (PNG)
 - 2560x1440 YouTube banner (PNG + JPG)
 - 5120x2880 4K YouTube banner (PNG + JPG)
Files are written to out/brand/
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "out" / "brand"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PATTERN = "OXK"
BACKGROUND = (4, 6, 8)
FOREGROUND = (24, 238, 238)


@dataclass
class AssetSpec:
    name: str
    size: tuple[int, int]
    text: str
    margin: int
    letter_spacing: int
    block: int
    inner_glow_radius: int
    outer_glow_radius: int
    grid_spacing: int
    grid_alpha: int
    spotlight_blur: int
    reflection_intensity: int
    depth_offset: int
    gradient_top: tuple[int, int, int] | None = None
    gradient_bottom: tuple[int, int, int] | None = None
    add_reflection: bool = False
    safe_box_dimensions: tuple[int, int] | None = None  # (w, h)
    ring_alpha: int = 0
    ring_width: int = 0
    ring_blur: int = 0
    ring_padding: float = 0.0
    formats: tuple[str, ...] = ("png",)
    vertical_offset_ratio: float = 0.0


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


def measure_text(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    try:
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return w, h
    except Exception:
        dummy = Image.new("L", (1, 1))
        draw = ImageDraw.Draw(dummy)
        return draw.textsize(text, font=font)


def find_font_for_box(text: str, box_w: int, box_h: int, letter_spacing: int, min_size: int = 10, max_size: int = 2000) -> tuple[ImageFont.FreeTypeFont, list[tuple[str, int, int]]]:
    lo, hi = min_size, max_size
    best_font = load_font(min_size)
    best_metrics: list[tuple[str, int, int]] = []

    while lo <= hi:
        mid = (lo + hi) // 2
        font = load_font(mid)
        metrics = []
        total_w = 0
        max_h = 0
        for ch in text:
            w, h = measure_text(font, ch)
            metrics.append((ch, w, h))
            total_w += w
            max_h = max(max_h, h)
        total_w += letter_spacing * (len(text) - 1)

        if total_w <= box_w and max_h <= box_h:
            best_font = font
            best_metrics = metrics
            lo = mid + 1
        else:
            hi = mid - 1

    return best_font, best_metrics


def create_silhouette(spec: AssetSpec) -> tuple[Image.Image, ImageFont.FreeTypeFont, list[tuple[str, int, int]], tuple[int, int]]:
    width, height = spec.size
    canvas = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(canvas)

    if spec.safe_box_dimensions:
        box_w, box_h = spec.safe_box_dimensions
        box_x = (width - box_w) // 2
        box_y = (height - box_h) // 2
    else:
        box_x = spec.margin
        box_y = spec.margin
        box_w = width - spec.margin * 2
        box_h = height - spec.margin * 2

    font, metrics = find_font_for_box(spec.text, box_w, box_h, spec.letter_spacing)
    total_w = sum(w for _, w, _ in metrics) + spec.letter_spacing * (len(metrics) - 1)
    max_h = max(h for _, _, h in metrics)

    x = box_x + (box_w - total_w) // 2
    y = box_y + (box_h - max_h) // 2

    if spec.vertical_offset_ratio:
        offset = int(spec.size[1] * spec.vertical_offset_ratio)
        y = max(box_y, min(box_y + box_h - max_h, y - offset))

    for idx, (ch, w, h) in enumerate(metrics):
        draw.text((x, y), ch, fill=255, font=font)
        x += w + spec.letter_spacing

    return canvas, font, metrics, (total_w, max_h)


def build_mosaic(silhouette: Image.Image, pattern: str, block: int, char_font: ImageFont.FreeTypeFont, fg: tuple[int, int, int], depth_offset: int) -> tuple[Image.Image, Image.Image]:
    w, h = silhouette.size
    mosaic = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow_color = (6, 12, 18, 180)
    draw = ImageDraw.Draw(mosaic)

    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)

    bbox = silhouette.getbbox()
    if not bbox:
        return mosaic, mask
    x0, y0, x1, y1 = bbox

    start_x = x0 - (x0 % block)
    start_y = y0 - (y0 % block)
    end_x = x1 + (block - (x1 - start_x) % block) % block
    end_y = y1 + (block - (y1 - start_y) % block) % block

    cols = max(1, (end_x - start_x) // block)
    rows = max(1, (end_y - start_y) // block)

    index = 0
    for row in range(rows):
        for col in range(cols):
            ix = start_x + col * block
            iy = start_y + row * block
            cx = min(w - 1, ix + block // 2)
            cy = min(h - 1, iy + block // 2)
            if silhouette.getpixel((cx, cy)) > 128:
                ch = pattern[index % len(pattern)]
                index += 1
                cw, ch_h = measure_text(char_font, ch)
                px = ix + (block - cw) // 2
                py = iy + (block - ch_h) // 2

                if depth_offset:
                    draw.text((px + depth_offset, py + depth_offset), ch, fill=shadow_color, font=char_font)
                draw.text((px, py), ch, fill=fg + (255,), font=char_font)
                mask_draw.text((px, py), ch, fill=255, font=char_font)

    return mosaic, mask


def apply_glow(base: Image.Image, mask: Image.Image, inner_radius: int, outer_radius: int, color: tuple[int, int, int]) -> Image.Image:
    inner = mask.filter(ImageFilter.GaussianBlur(inner_radius))
    outer = mask.filter(ImageFilter.GaussianBlur(outer_radius))

    inner_layer = Image.new("RGBA", base.size, color + (0,))
    outer_layer = Image.new("RGBA", base.size, color + (0,))
    inner_layer.putalpha(inner)
    outer_layer.putalpha(outer)

    merged = Image.alpha_composite(outer_layer, inner_layer)
    return Image.alpha_composite(merged, base)


def add_background_layers(image: Image.Image, spec: AssetSpec) -> Image.Image:
    w, h = image.size
    base = Image.new("RGBA", (w, h), BACKGROUND + (255,))

    # Vertical gradient (top darker, bottom lighter)
    if spec.gradient_top and spec.gradient_bottom:
        grad = Image.new("RGB", (1, h))
        top = spec.gradient_top
        bottom = spec.gradient_bottom
        for y in range(h):
            t = y / (h - 1)
            r = int(top[0] * (1 - t) + bottom[0] * t)
            g = int(top[1] * (1 - t) + bottom[1] * t)
            b = int(top[2] * (1 - t) + bottom[2] * t)
            grad.putpixel((0, y), (r, g, b))
        grad = grad.resize((w, h))
        grad_layer = Image.new("RGBA", (w, h))
        grad_layer.paste(grad)
        base = Image.alpha_composite(base, grad_layer)

    # Soft radial spotlight behind center
    spotlight = Image.new("L", (w, h), 0)
    sd = ImageDraw.Draw(spotlight)
    sd.ellipse((w * 0.08, h * 0.08, w * 0.92, h * 0.92), fill=235)
    spotlight = spotlight.filter(ImageFilter.GaussianBlur(spec.spotlight_blur))
    spot_layer = Image.new("RGBA", (w, h), (40, 80, 110, 0))
    spot_layer.putalpha(spotlight)
    base = Image.alpha_composite(base, spot_layer)

    # Subtle grid
    if spec.grid_spacing > 0 and spec.grid_alpha > 0:
        grid = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grid)
        color = (16, 26, 32, spec.grid_alpha)
        for x in range(0, w, spec.grid_spacing):
            gd.line((x, 0, x, h), fill=color, width=1)
        for y in range(0, h, spec.grid_spacing):
            gd.line((0, y, w, y), fill=color, width=1)
        base = Image.alpha_composite(base, grid)

    return Image.alpha_composite(base, image)


def add_ring(image: Image.Image, spec: AssetSpec) -> Image.Image:
    if spec.ring_alpha <= 0 or spec.ring_width <= 0:
        return image
    w, h = image.size
    ring_mask = Image.new("L", (w, h), 0)
    rd = ImageDraw.Draw(ring_mask)
    pad = int(min(w, h) * spec.ring_padding)
    max_offset = spec.ring_width
    for offset in range(max_offset):
        alpha = max(0, spec.ring_alpha - int(spec.ring_alpha * (offset / max(1, max_offset))))
        rd.ellipse((pad + offset, pad + offset, w - pad - offset, h - pad - offset), outline=alpha)
    ring_mask = ring_mask.filter(ImageFilter.GaussianBlur(spec.ring_blur))
    ring_layer = Image.new("RGBA", (w, h), FOREGROUND + (0,))
    ring_layer.putalpha(ring_mask)
    return Image.alpha_composite(image, ring_layer)


def add_reflection(image: Image.Image, intensity: int) -> Image.Image:
    if intensity <= 0:
        return image
    w, h = image.size
    reflection = image.transpose(Image.FLIP_TOP_BOTTOM)
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    for y in range(h):
        alpha = max(0, intensity - int(intensity * (y / h) * 2.2))
        md.line((0, y, w, y), fill=alpha)
    reflection.putalpha(mask)
    canvas = Image.new("RGBA", (w, h + h // 3), BACKGROUND + (255,))
    canvas.paste(image, (0, 0), image)
    canvas.paste(reflection, (0, h // 10), reflection)
    return canvas.crop((0, 0, w, h))


def add_vignette(image: Image.Image, strength: int = 120) -> Image.Image:
    w, h = image.size
    vign = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vign)
    vd.ellipse((-w * 0.3, -h * 0.5, w * 1.3, h * 1.5), fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(int(max(w, h) * 0.15)))
    mask = ImageChops.invert(vign)
    dark = Image.new("RGBA", (w, h), (0, 0, 0, strength))
    return Image.composite(image, Image.alpha_composite(dark, image), mask.convert("L"))


def render_asset(spec: AssetSpec) -> Image.Image:
    silhouette, _, _, _ = create_silhouette(spec)
    char_font = load_font(spec.block)
    mosaic, mask = build_mosaic(silhouette, PATTERN, spec.block, char_font, FOREGROUND, spec.depth_offset)
    glowing = apply_glow(mosaic, mask, spec.inner_glow_radius, spec.outer_glow_radius, FOREGROUND)
    layered = add_background_layers(glowing, spec)
    layered = add_ring(layered, spec)
    if spec.add_reflection:
        layered = add_reflection(layered, spec.reflection_intensity)
    final = add_vignette(layered, 90)
    return final


def save_outputs():
    specs = [
        AssetSpec(
            name="logo_1024",
            size=(1024, 1024),
            text="OXK",
            margin=96,
            letter_spacing=-14,
            block=6,
            inner_glow_radius=16,
            outer_glow_radius=44,
            grid_spacing=0,
            grid_alpha=0,
            spotlight_blur=180,
            reflection_intensity=0,
            depth_offset=2,
            gradient_top=(2, 4, 6),
            gradient_bottom=(12, 28, 36),
            ring_alpha=110,
            ring_width=18,
            ring_blur=28,
            ring_padding=0.12,
            formats=("png",),
            vertical_offset_ratio=0.08,
        ),
        AssetSpec(
            name="logo_2048",
            size=(2048, 2048),
            text="OXK",
            margin=180,
            letter_spacing=-18,
            block=10,
            inner_glow_radius=22,
            outer_glow_radius=54,
            grid_spacing=140,
            grid_alpha=22,
            spotlight_blur=260,
            reflection_intensity=0,
            depth_offset=3,
            gradient_top=(2, 4, 6),
            gradient_bottom=(16, 32, 40),
            ring_alpha=120,
            ring_width=22,
            ring_blur=36,
            ring_padding=0.1,
            formats=("png",),
        ),
        AssetSpec(
            name="banner_2560x1440",
            size=(2560, 1440),
            text="OXK Pixel",
            margin=180,
            letter_spacing=-10,
            block=12,
            inner_glow_radius=22,
            outer_glow_radius=60,
            grid_spacing=140,
            grid_alpha=18,
            spotlight_blur=280,
            reflection_intensity=90,
            depth_offset=3,
            gradient_top=(2, 6, 10),
            gradient_bottom=(18, 36, 48),
            add_reflection=True,
            safe_box_dimensions=(1546, 423),
            formats=("png", "jpg"),
        ),
        AssetSpec(
            name="banner_5120x2880",
            size=(5120, 2880),
            text="OXK Pixel",
            margin=320,
            letter_spacing=-12,
            block=14,
            inner_glow_radius=28,
            outer_glow_radius=78,
            grid_spacing=200,
            grid_alpha=24,
            spotlight_blur=400,
            reflection_intensity=120,
            depth_offset=4,
            gradient_top=(2, 6, 10),
            gradient_bottom=(20, 38, 52),
            add_reflection=True,
            safe_box_dimensions=(1546 * 2, 423 * 2),
            formats=("png", "jpg"),
        ),
    ]

    outputs = []
    for spec in specs:
        image = render_asset(spec)
        for fmt in spec.formats:
            out_path = OUT_DIR / f"{spec.name}.{fmt}"
            if fmt.lower() == "png":
                image.save(out_path)
            elif fmt.lower() in {"jpg", "jpeg"}:
                image.convert("RGB").save(out_path, quality=95, subsampling=0)
            else:
                raise ValueError(f"Unsupported format: {fmt}")
            outputs.append(out_path)

    return outputs


if __name__ == "__main__":
    files = save_outputs()
    for file in files:
        print(f"Saved: {file}")
