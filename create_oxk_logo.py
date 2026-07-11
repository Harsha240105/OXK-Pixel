"""
Create a glowing OXK logo made entirely from many small repeating "OXK" texts.
Produces out/oxk_logo_glow.png by default.
"""
from pathlib import Path
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

# Config
OUT_DIR = Path("out")
OUT_DIR.mkdir(exist_ok=True)
OUT_PATH = OUT_DIR / "oxk_logo_glow.png"
CANVAS_SIZE = (1600, 600)  # width, height (HD banner)
BIG_TEXT = "OXK"
SMALL_TEXT = "OXK"
BIG_FONT_SIZE = 420  # slightly larger for banner
SMALL_FONT_BLOCK = 14  # grid size for small characters (smaller for denser particles)
FG = (24, 242, 242)  # bright cyan/teal
BG = (6, 8, 10)  # very dark background
GLOW_RADIUS = 18
DEPTH_OFFSET = 6  # simulate 3D depth by drawing a darker offset layer
REFLECTION_OPACITY = 120  # 0-255
REFLECTION_GAP = 10  # gap pixels between logo and reflection


def load_font(preferred=None, size=20):
    # Try preferred, then common Windows fonts, then default PIL font.
    candidates = []
    if preferred:
        candidates.append(preferred)
    # Common Windows fonts
    candidates += [
        r"C:\Windows\Fonts\seguisb.ttf",  # Segoe UI Semibold
        r"C:\Windows\Fonts\arialbd.ttf",  # Arial Bold
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\consola.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def create_silhouette(text, canvas_size, font):
    img = Image.new("L", canvas_size, 0)
    draw = ImageDraw.Draw(img)
    # center text
    try:
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except Exception:
        w, h = draw.textsize(text, font=font)
    x = (canvas_size[0] - w) // 2
    y = (canvas_size[1] - h) // 2
    draw.text((x, y), text, fill=255, font=font)
    return img


def generate_filled_logo(silhouette, small_text, block, small_font, fg, bg):
    w, h = silhouette.size
    out = Image.new("RGBA", (w, h), bg + (255,))
    draw = ImageDraw.Draw(out)

    # For glow mask we'll draw the small texts in white on a mask image
    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)

    # iterate grid; we'll add slight random jitter and layered depth
    import random
    cols = w // block
    rows = h // block
    for iy in range(rows):
        for ix in range(cols):
            # sample silhouette at center of this block
            cx = min(w - 1, ix * block + block // 2)
            cy = min(h - 1, iy * block + block // 2)
            try:
                val = silhouette.getpixel((cx, cy))
            except Exception:
                val = 0
            if val > 128:
                ch = small_text[(ix + iy) % len(small_text)]
                # small random offset for slightly organic distribution
                jx = random.randint(-1, 1)
                jy = random.randint(-1, 1)
                # compute bbox of character
                try:
                    bb = small_font.getbbox(ch)
                    tw = bb[2] - bb[0]
                    th = bb[3] - bb[1]
                except Exception:
                    tw, th = small_font.getsize(ch)
                px = ix * block + (block - tw) // 2 + jx
                py = iy * block + (block - th) // 2 + jy
                # depth layer (darker offset behind)
                draw.text((px + DEPTH_OFFSET, py + DEPTH_OFFSET), ch, fill=(8, 16, 20, 180), font=small_font)
                # main bright character with slight color variation
                variance = random.randint(-10, 10)
                r = max(0, min(255, fg[0] + variance))
                g = max(0, min(255, fg[1] + variance))
                b = max(0, min(255, fg[2] + variance))
                draw.text((px, py), ch, fill=(r, g, b, 255), font=small_font)
                mask_draw.text((px, py), ch, fill=255, font=small_font)

    return out, mask


def apply_glow(base_img, mask, glow_color, radius):
    # Create colored glow by blurring the mask, coloring it and compositing under base_img
    blur = mask.filter(ImageFilter.GaussianBlur(radius))
    # create multiple blurred layers for stronger bloom
    blur2 = mask.filter(ImageFilter.GaussianBlur(int(radius * 1.8)))
    r, g, b = glow_color
    color_layer = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    c1 = Image.new("RGBA", base_img.size, (r, g, b, 0))
    c1.putalpha(blur)
    c2 = Image.new("RGBA", base_img.size, (r, g, b, 0))
    c2.putalpha(blur2)
    # composite glow layers and then place base_img over them
    glow = Image.alpha_composite(c2, c1)
    out = Image.alpha_composite(glow, base_img)
    return out


def main():
    # Load fonts
    big_font = load_font(size=BIG_FONT_SIZE)
    small_font = load_font(size=SMALL_FONT_BLOCK)

    silhouette = create_silhouette(BIG_TEXT, CANVAS_SIZE, big_font)

    # Add a subtle radial spotlight behind the text for cinematic lighting
    w, h = CANVAS_SIZE
    spotlight = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = Image.new("L", (w, h), 0)
    sd_draw = ImageDraw.Draw(sd)
    # large soft ellipse centered
    sd_draw.ellipse((w*0.15, h*0.05, w*0.85, h*0.95), fill=200)
    spotlight_blur = sd.filter(ImageFilter.GaussianBlur(150))
    spotlight_col = Image.new("RGBA", (w, h), (30, 60, 80, 0))
    spotlight_col.putalpha(spotlight_blur)

    filled, mask = generate_filled_logo(silhouette, SMALL_TEXT, SMALL_FONT_BLOCK, small_font, FG, BG)

    # place spotlight under the filled text
    composed = Image.alpha_composite(spotlight_col, filled)

    # apply glow
    result = apply_glow(composed, mask, FG, GLOW_RADIUS)

    # create reflection
    refl = result.copy().transpose(Image.FLIP_TOP_BOTTOM)
    # crop reflection to lower half area and fade
    rw, rh = refl.size
    mask_ref = Image.new("L", (rw, rh), 0)
    mr_draw = ImageDraw.Draw(mask_ref)
    # gradient alpha for reflection
    for y in range(rh):
        alpha = max(0, REFLECTION_OPACITY - int((y / rh) * REFLECTION_OPACITY * 1.5))
        mr_draw.line((0, y, rw, y), fill=alpha)
    refl = Image.composite(Image.new("RGBA", refl.size, (0,0,0,0)), refl, mask_ref)
    # place reflection below with small gap
    final = Image.new("RGBA", (w, h + rh//3), (BG[0], BG[1], BG[2], 255))
    # center result at top portion
    top_y = 0
    final.paste(result, (0, top_y), result)
    refl_y = top_y + h + REFLECTION_GAP
    # paste partial reflection (shifted up so only visible area shows) scaled down in opacity
    final.paste(refl, (0, h + REFLECTION_GAP), refl)

    # crop back to banner size (1600x600), keeping reflection subtle below
    final = final.crop((0, 0, w, h))

    # small vignette to darken edges
    vign = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vign)
    vd.ellipse((-w*0.2, -h*0.5, w*1.2, h*1.5), fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(200))
    vign_mask = ImageChops.invert(vign)
    final.putalpha(255)
    # composite vignette over final by darkening edges slightly
    darken = Image.new("RGBA", final.size, (0,0,0,120))
    final = Image.composite(final, Image.alpha_composite(darken, final), vign_mask.convert("L"))

    final.save(OUT_PATH)
    print(f"Saved logo to: {OUT_PATH}")


if __name__ == '__main__':
    main()
