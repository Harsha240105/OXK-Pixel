"""
Generate an 800x800 square pixel-art OXK logo made from many small 'O', 'X', 'K' letters.
Saves to out/square_800_oxk.png
"""
from pathlib import Path
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

OUT_DIR = Path("out")
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "square_800_oxk.png"
CANVAS_SIZE = (800, 800)
BIG_TEXT = "OXK"
SMALL_TEXT = "OXK"
BIG_FONT_SIZE = 360
SMALL_FONT_BLOCK = 12  # size of grid cell for each small character
FG = (24, 242, 242)  # cyan
BG = (10, 12, 14)  # dark charcoal
GLOW_RADIUS = 14
OUTER_GLOW_RADIUS = 30
DEPTH_OFFSET = 4
MARGIN = 40  # ensure big text doesn't touch edges (reduced for larger logo)
LETTER_SPACING = -14  # negative to tighten gaps between letters


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
    # Binary search for the largest font size that fits within canvas_size minus margins
    w, h = canvas_size
    max_w = w - 2 * margin
    max_h = h - 2 * margin
    lo = min_size
    hi = preferred * 3
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
    # choose font size to maximize filling within margin
    chosen_size = find_max_font_size(text, canvas_size, margin, preferred=preferred_font_size or BIG_FONT_SIZE)
    font = load_font(size=chosen_size)

    # compute per-character widths and total width with custom letter spacing
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
    w, h = silhouette.size
    out = Image.new("RGBA", (w, h), bg + (255,))
    draw = ImageDraw.Draw(out)
    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)
    cols = w // block
    rows = h // block
    for iy in range(rows):
        for ix in range(cols):
            cx = min(w - 1, ix * block + block // 2)
            cy = min(h - 1, iy * block + block // 2)
            val = silhouette.getpixel((cx, cy)) if 0 <= cx < w and 0 <= cy < h else 0
            if val > 128:
                ch = small_text[(ix + iy) % len(small_text)]
                jx = random.randint(-1, 1)
                jy = random.randint(-1, 1)
                try:
                    bb = small_font.getbbox(ch)
                    tw = bb[2] - bb[0]
                    th = bb[3] - bb[1]
                except Exception:
                    tw, th = small_font.getsize(ch)
                px = ix * block + (block - tw) // 2 + jx
                py = iy * block + (block - th) // 2 + jy
                # small depth shadow for subtle 3D
                draw.text((px + DEPTH_OFFSET, py + DEPTH_OFFSET), ch, fill=(6, 10, 12, 180), font=small_font)
                variance = random.randint(-6, 6)
                r = max(0, min(255, fg[0] + variance))
                g = max(0, min(255, fg[1] + variance))
                b = max(0, min(255, fg[2] + variance))
                draw.text((px, py), ch, fill=(r, g, b, 255), font=small_font)
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


def add_vignette(image, strength=120):
    w, h = image.size
    vign = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vign)
    vd.ellipse((-w*0.2, -h*0.2, w*1.2, h*1.2), fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(180))
    mask = ImageChops.invert(vign)
    dark = Image.new("RGBA", image.size, (0,0,0,strength))
    return Image.composite(image, Image.alpha_composite(dark, image), mask.convert("L"))


def main():
    w, h = CANVAS_SIZE
    big_font = load_font(size=BIG_FONT_SIZE)
    small_font = load_font(size=SMALL_FONT_BLOCK)

    # create silhouette with tighter letter spacing and a dynamically chosen font size
    silhouette = create_silhouette(BIG_TEXT, CANVAS_SIZE, preferred_font_size=BIG_FONT_SIZE, margin=MARGIN, letter_spacing=LETTER_SPACING)

    filled, mask = generate_filled_logo(silhouette, SMALL_TEXT, SMALL_FONT_BLOCK, small_font, FG, BG)

    result = apply_glow(filled, mask, FG, GLOW_RADIUS)

    # stronger outer glow layer for contrast/pop
    outer_blur = mask.filter(ImageFilter.GaussianBlur(OUTER_GLOW_RADIUS))
    outer = Image.new("RGBA", CANVAS_SIZE, (FG[0], FG[1], FG[2], 0))
    outer.putalpha(outer_blur)
    # composite outer glow underneath result
    base_with_outer = Image.alpha_composite(outer, result)

    # subtle drop shadow under main composition
    shadow = Image.new("RGBA", CANVAS_SIZE, (0,0,0,0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle((0, h*0.7, w, h), fill=(0,0,0,40))
    final = Image.alpha_composite(Image.alpha_composite(Image.new("RGBA", CANVAS_SIZE, BG+(255,)), shadow), result)

    final = add_vignette(final, strength=100)

    # composite outer glow again subtly on final for a soft neon bloom
    final = Image.alpha_composite(outer, final)

    # Save
    final.save(OUT_PATH)
    print(f"Saved square logo to: {OUT_PATH}")

if __name__ == '__main__':
    main()
