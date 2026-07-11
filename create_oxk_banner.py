"""
Generate a 2560x1440 YouTube banner with a centered "OXK" logo formed from many small "O/X/K" letters.
Saves to out/banner_2560x1440_oxk.png
"""
from pathlib import Path
import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

OUT_DIR = Path("out")
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "banner_2560x1440_oxk.png"
CANVAS_SIZE = (2560, 1440)
BIG_TEXT = "OXK"
SMALL_TEXT = "OXK"
# tuned for large banner
BIG_FONT_SIZE = 900
SMALL_FONT_BLOCK = 20  # pixel block for each small character
FG = (24, 242, 242)  # cyan
BG = (6, 8, 10)  # dark
GLOW_RADIUS = 28
DEPTH_OFFSET = 8
REFLECTION_OPACITY = 90
REFLECTION_GAP = 12

# YouTube safe area for text is centered 1546x423; we'll ensure text fits within that
SAFE_W = 1546
SAFE_H = 423


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


def create_silhouette(text, canvas_size, font, max_box=None):
    img = Image.new("L", canvas_size, 0)
    draw = ImageDraw.Draw(img)
    # compute text bbox
    try:
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except Exception:
        w, h = draw.textsize(text, font=font)
    # center, but if max_box provided, place inside center of that box
    if max_box:
        box_x, box_y, box_w, box_h = max_box
        x = box_x + (box_w - w) // 2
        y = box_y + (box_h - h) // 2
    else:
        x = (canvas_size[0] - w) // 2
        y = (canvas_size[1] - h) // 2
    draw.text((x, y), text, fill=255, font=font)
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
                # depth shadow
                draw.text((px + DEPTH_OFFSET, py + DEPTH_OFFSET), ch, fill=(6, 12, 14, 180), font=small_font)
                variance = random.randint(-8, 8)
                r = max(0, min(255, fg[0] + variance))
                g = max(0, min(255, fg[1] + variance))
                b = max(0, min(255, fg[2] + variance))
                draw.text((px, py), ch, fill=(r, g, b, 255), font=small_font)
                mask_draw.text((px, py), ch, fill=255, font=small_font)
    return out, mask


def apply_glow(base_img, mask, glow_color, radius):
    blur1 = mask.filter(ImageFilter.GaussianBlur(radius))
    blur2 = mask.filter(ImageFilter.GaussianBlur(int(radius * 2.2)))
    r, g, b = glow_color
    c1 = Image.new("RGBA", base_img.size, (r, g, b, 0))
    c1.putalpha(blur1)
    c2 = Image.new("RGBA", base_img.size, (r, g, b, 0))
    c2.putalpha(blur2)
    glow = Image.alpha_composite(c2, c1)
    out = Image.alpha_composite(glow, base_img)
    return out


def create_reflection(image, gap=REFLECTION_GAP, opacity=REFLECTION_OPACITY):
    w, h = image.size
    refl = image.copy().transpose(Image.FLIP_TOP_BOTTOM)
    # fade mask
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    for y in range(h):
        alpha = max(0, opacity - int((y / h) * opacity * 1.8))
        md.line((0, y, w, y), fill=alpha)
    refl.putalpha(mask)
    return refl


def main():
    w, h = CANVAS_SIZE
    big_font = load_font(size=BIG_FONT_SIZE)
    small_font = load_font(size=SMALL_FONT_BLOCK)

    # center safe box
    sx = (w - SAFE_W) // 2
    sy = (h - SAFE_H) // 2
    safe_box = (sx, sy, SAFE_W, SAFE_H)

    silhouette = create_silhouette(BIG_TEXT, CANVAS_SIZE, big_font, max_box=safe_box)

    # subtle grid background lines for tech aesthetic
    bg = Image.new("RGB", CANVAS_SIZE, BG)
    bg_draw = ImageDraw.Draw(bg)
    grid_spacing = 80
    for x in range(0, w, grid_spacing):
        c = (10, 12, 14) if x % (grid_spacing * 4) else (14, 20, 24)
        bg_draw.line((x, 0, x, h), fill=c, width=1)
    for y in range(0, h, grid_spacing):
        bg_draw.line((0, y, w, y), fill=(8, 10, 12), width=1)

    filled, mask = generate_filled_logo(silhouette, SMALL_TEXT, SMALL_FONT_BLOCK, small_font, FG, BG)

    # composite filled over bg
    filled_rgb = Image.alpha_composite(Image.new("RGBA", CANVAS_SIZE, BG + (255,)), filled)

    # add spotlight behind (subtle)
    spotlight = Image.new("L", CANVAS_SIZE, 0)
    sd = ImageDraw.Draw(spotlight)
    sd.ellipse((w*0.1, h*0.05, w*0.9, h*0.95), fill=220)
    spotlight = spotlight.filter(ImageFilter.GaussianBlur(180))
    sp_col = Image.new("RGBA", CANVAS_SIZE, (20, 40, 60, 0))
    sp_col.putalpha(spotlight)
    base = Image.alpha_composite(sp_col, filled_rgb)

    # apply glow
    result = apply_glow(base, mask, FG, GLOW_RADIUS)

    # reflection
    refl = create_reflection(result)
    final = Image.new("RGBA", (w, h + refl.size[1]//4), BG + (255,))
    final.paste(result, (0, 0), result)
    final.paste(refl, (0, h + REFLECTION_GAP), refl)
    final = final.crop((0, 0, w, h))

    # vignette
    vign = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vign)
    vd.ellipse((-w*0.2, -h*0.5, w*1.2, h*1.5), fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(240))
    vign_mask = ImageChops.invert(vign)
    darken = Image.new("RGBA", final.size, (0,0,0,100))
    final = Image.composite(final, Image.alpha_composite(darken, final), vign_mask.convert("L"))

    final.save(OUT_PATH)
    print(f"Saved banner to: {OUT_PATH}")

if __name__ == '__main__':
    main()
