import sys
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    print("Pillow is not installed. Install it with: pip install pillow")
    sys.exit(1)

# Load your logo shape (black/white silhouette). If it's missing, create a placeholder.
logo_path = "your_logo.png"
if not os.path.exists(logo_path):
    print(f"Logo image '{logo_path}' not found — creating a placeholder image.")
    img = Image.new("L", (400, 200), 255)
    tmp_draw = ImageDraw.Draw(img)
    import sys
    import os
    import argparse
    from pathlib import Path

    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        print("Pillow is not installed. Install it with: pip install pillow")
        sys.exit(1)


    def load_logo_or_placeholder(path: Path, size=(400, 400)) -> Image.Image:
        if not path or not path.exists():
            print(f"Logo image '{path}' not found — creating a placeholder image.")
            img = Image.new("L", size, 255)
            tmp_draw = ImageDraw.Draw(img)
            tmp_draw.ellipse((size[0] // 8, size[1] // 8, size[0] * 7 // 8, size[1] * 7 // 8), fill=0)
            return img
        else:
            return Image.open(path).convert("L")


    def get_font(font_path: str, pixel_block: int):
        # Choose a font size close to the pixel block so characters fit inside each cell when scaled.
        try:
            size = max(1, int(pixel_block * 0.9))
            return ImageFont.truetype(font_path, size)
        except Exception:
            return ImageFont.load_default()


    def generate_pixel_text_art(silhouette: Image.Image, text: str, out_size: tuple, block: int, font_path: str, fg=(0, 255, 255), bg=(0, 0, 0)) -> Image.Image:
        """
        Create an image of size out_size composed of blocks of size `block` where each block that
        corresponds to dark silhouette pixels will contain a character from `text`.
        Algorithm:
          - Resize silhouette down to (out_w/block, out_h/block)
          - For each cell that is dark, draw the appropriate character at (x*block, y*block) using a font sized to ~block
          - This keeps a crisp pixel-art look when using integer block sizes and nearest-neighbor scaling.
        """
        out_w, out_h = out_size

        # Compute small grid size
        small_w = max(1, out_w // block)
        small_h = max(1, out_h // block)

        small_logo = silhouette.resize((small_w, small_h), resample=Image.LANCZOS).convert("L")

        # Create output image at final size
        out = Image.new("RGB", (out_w, out_h), bg)
        draw = ImageDraw.Draw(out)

        font = get_font(font_path, block)

        for y in range(small_h):
            for x in range(small_w):
                pixel = small_logo.getpixel((x, y))
                if pixel < 128:
                    ch = text[((x) + (y)) % len(text)]
                    # Position the character inside the block. We'll use a small offset to center roughly.
                    try:
                        bbox = font.getbbox(ch)
                        w = bbox[2] - bbox[0]
                        h = bbox[3] - bbox[1]
                    except Exception:
                        w, h = font.getsize(ch)

                    px = x * block + max(0, (block - w) // 2)
                    py = y * block + max(0, (block - h) // 2)
                    draw.text((px, py), ch, fill=fg, font=font)

        return out


    def make_assets(logo_path: Path, text: str, font_path: str, out_dir: Path):
        silhouette = load_logo_or_placeholder(logo_path, size=(800, 800))

        assets = {
            "avatar_512": ((512, 512), 16),
            "favicon_32": ((32, 32), 4),
            "profile_800": ((800, 800), 20),
            "banner_2560x1440": ((2560, 1440), 24),
        }

        out_dir.mkdir(parents=True, exist_ok=True)

        for name, (size, block) in assets.items():
            print(f"Generating {name} -> {size} with block {block}")
            img = generate_pixel_text_art(silhouette, text, size, block, font_path)
            path = out_dir / f"{name}.png"
            img.save(path)
            print(f"  saved: {path}")
            # For favicon, also create .ico
            if name == "favicon_32":
                ico_path = out_dir / "favicon.ico"
                img.save(ico_path, format="ICO")
                print(f"  saved: {ico_path}")


    def main(argv=None):
        parser = argparse.ArgumentParser(description="Generate pixel-text channel assets using repeating text (e.g. OXK)")
        parser.add_argument("--input", "-i", help="Input silhouette PNG path (black on white). If omitted a placeholder is used.")
        parser.add_argument("--text", "-t", default="OXK", help="Pattern text to repeat (default: OXK)")
        parser.add_argument("--font", "-f", default="Courier.ttf", help="TTF font path to use (falls back to default font if missing)")
        parser.add_argument("--out", "-o", default="out", help="Output directory")

        args = parser.parse_args(argv)

        logo_path = Path(args.input) if args.input else Path("your_logo.png")
        out_dir = Path(args.out)

        make_assets(logo_path, args.text, args.font, out_dir)


    if __name__ == "__main__":
        main()
