"""
Generate a 1024x1024 square avatar for 'OXK Pixel'.
Saves to out/avatar_1024_oxk.png
"""
from pathlib import Path
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

OUT_DIR = Path("out")
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "avatar_1024_oxk.png"
CANVAS_SIZE = (1024, 1024)
BIG_TEXT = "OXK"
SMALL_TEXT = "OXK"
BIG_FONT_SIZE = 480
SMALL_FONT_BLOCK = 8  # dense small characters (tighter mosaic)
FG = (20, 245, 235)  # neon cyan/turquoise
BG = (0, 0, 0)  # pure black background
GLOW_RADIUS = 14
OUTER_GLOW_RADIUS = 32
DEPTH_OFFSET = 2
MARGIN = 56
LETTER_SPACING = -6
GRID_OPACITY = 12  # subtle digital grid


def load_font(preferred=None, size=20):
    candidates = []
    if preferred:
        candidates.append(preferred)
    candidates += [
        r"C:\Windows\Fonts\seguisb.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\consola.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def find_max_font_size(text, canvas_size, margin, preferred=BIG_FONT_SIZE, min_size=10):
    w, h = canvas_size
    max_w = w - 2 * margin
    max_h = h - 2 * margin
    lo = min_size
    hi = preferred * 2
    best = min_size
    while lo <= hi:
        mid = (lo + hi) // 2
        f = load_font(size=mid)
        try:
            bb = f.getbbox(text)
            tw = bb[2] - bb[0]
            th = bb[3] - bb[1]
        except Exception:
            tw, th = ImageDraw.Draw(Image.new("L", (1, 1))).textsize(text, font=f)
        if tw <= max_w and th <= max_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def create_silhouette(text, canvas_size, preferred_font_size=None, margin=0, letter_spacing=0):
    img = Image.new("L", canvas_size, 0)
    draw = ImageDraw.Draw(img)
    chosen_size = find_max_font_size(text, canvas_size, margin, preferred=preferred_font_size or BIG_FONT_SIZE)
    font = load_font(size=chosen_size)
    char_boxes = []
    total_w = 0
    max_h = 0
    for ch in text:
        try:
            bb = font.getbbox(ch)
            cw = bb[2] - bb[0]
            ch_h = bb[3] - bb[1]
        except Exception:
            cw, ch_h = draw.textsize(ch, font=font)
        char_boxes.append((ch, cw, ch_h))
        total_w += cw
    total_w += letter_spacing * (len(text) - 1)
    max_h = max([bh for (_c, _w, bh) in char_boxes])
    x_start = (canvas_size[0] - total_w) // 2
    y = (canvas_size[1] - max_h) // 2
    x = x_start
    for idx, (ch, cw, ch_h) in enumerate(char_boxes):
        draw.text((x, y), ch, fill=255, font=font)
        x += cw + letter_spacing
    return img


def generate_filled_logo(silhouette, small_text, block, small_font, fg, bg):
    """
    Deterministic placement of small characters inside the silhouette bounding box.
    No randomness — characters are tightly packed in a grid aligned to the silhouette bbox so
    the big letters are clean, centered, and symmetrical. This prevents stray characters before
    the top of the 'O' and ensures consistent visual output.
    """
    w, h = silhouette.size
    out = Image.new("RGBA", (w, h), bg + (255,))
    draw = ImageDraw.Draw(out)
    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)

    # Determine bounding box of silhouette to avoid drawing outside the big letters.
    bbox = silhouette.getbbox()
    if not bbox:
        return out, mask
    x0, y0, x1, y1 = bbox

    # Align grid to the bounding box to ensure top row starts exactly at top of 'O' area
    start_x = x0 - (x0 % block)
    start_y = y0 - (y0 % block)
    end_x = x1
    end_y = y1

    cols = max(1, (end_x - start_x) // block)
    rows = max(1, (end_y - start_y) // block)

    for row in range(rows):
        for col in range(cols):
            ix = start_x + col * block
            iy = start_y + row * block
            # sample center of cell
            cx = min(w - 1, ix + block // 2)
            cy = min(h - 1, iy + block // 2)
            val = silhouette.getpixel((cx, cy))
            if val > 128:
                ch = small_text[(col + row) % len(small_text)]
                try:
                    bb = small_font.getbbox(ch)
                    tw = bb[2] - bb[0]
                    th = bb[3] - bb[1]
                except Exception:
                    tw, th = small_font.getsize(ch)
                px = ix + (block - tw) // 2
                py = iy + (block - th) // 2
                # subtle depth shadow behind each char for slight 3D
                draw.text((px + DEPTH_OFFSET, py + DEPTH_OFFSET), ch, fill=(6, 10, 12, 160), font=small_font)
                # main character (no color variance for crispness)
                draw.text((px, py), ch, fill=fg + (255,), font=small_font)
                mask_draw.text((px, py), ch, fill=255, font=small_font)
    return out, mask


def apply_glow(base_img, mask, glow_color, radius):
    blur1 = mask.filter(ImageFilter.GaussianBlur(radius))
    blur2 = mask.filter(ImageFilter.GaussianBlur(int(radius * 1.8)))
    r, g, b = glow_color
    c1 = Image.new("RGBA", base_img.size, (r, g, b, 0))
    c1.putalpha(blur1)
    c2 = Image.new("RGBA", base_img.size, (r, g, b, 0))
    c2.putalpha(blur2)
    glow = Image.alpha_composite(c2, c1)
    out = Image.alpha_composite(glow, base_img)
    return out


def add_subtle_grid(image, spacing=64, opacity=GRID_OPACITY):
    w, h = image.size
    overlay = Image.new("RGBA", (w, h), (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    line_col = (8, 12, 14, opacity)
    for x in range(0, w, spacing):
        d.line((x, 0, x, h), fill=line_col)
    for y in range(0, h, spacing):
        d.line((0, y, w, y), fill=line_col)
    return Image.alpha_composite(image, overlay)


def add_outer_glow_layer(mask, color, radius):
    blur = mask.filter(ImageFilter.GaussianBlur(radius))
    layer = Image.new("RGBA", mask.size, (color[0], color[1], color[2], 0))
    layer.putalpha(blur)
    return layer


def main():
    w, h = CANVAS_SIZE
    # choose a dense small font to render tiny letters
    small_font = load_font(size=SMALL_FONT_BLOCK)
    # silhouette with slightly tighter spacing and margin
    silhouette = create_silhouette(BIG_TEXT, CANVAS_SIZE, preferred_font_size=BIG_FONT_SIZE, margin=MARGIN, letter_spacing=LETTER_SPACING)
    filled, mask = generate_filled_logo(silhouette, SMALL_TEXT, SMALL_FONT_BLOCK, small_font, FG, BG)
    # inner glow
    result = apply_glow(filled, mask, FG, GLOW_RADIUS)
    # outer glow/bloom underneath
    outer = add_outer_glow_layer(mask, FG, OUTER_GLOW_RADIUS)
    composed = Image.alpha_composite(outer, result)
    # subtle grid
    composed = add_subtle_grid(composed, spacing=56)
    # final vignette to keep focus center
    vign = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vign)
    vd.ellipse((-w*0.1, -h*0.1, w*1.1, h*1.1), fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(140))
    vign_mask = ImageChops.invert(vign)
    darken = Image.new("RGBA", (w, h), (0,0,0,120))
    final = Image.composite(composed, Image.alpha_composite(darken, composed), vign_mask.convert("L"))
    final.save(OUT_PATH)
    print(f"Saved avatar to: {OUT_PATH}")

if __name__ == '__main__':
    main()
