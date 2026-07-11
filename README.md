# OXK Pixel Asset Generator

This workspace now ships with multiple generators for the "OXK Pixel" brand.

## Scripts

- `Logo.py` – generates pixel-art style channel assets (avatar, banner, thumbnail, favicon) from a black/white silhouette using repeated text (default `OXK`).
- `create_oxk_logo.py` – produces a 1600×600 glowing "OXK" intro/banner.
- `create_oxk_square.py` – outputs an 800×800 cyan mosaic avatar.
- `create_oxk_avatar.py` – renders a deterministic 1024×1024 avatar with perfect grid alignment.
- `create_oxk_banner.py` – creates a 2560×1440 YouTube banner with safe-area layout.
- `create_oxk_brand.py` – builds the high-resolution identity set (2048×2048 logo, 5120×2880 banner PNG + JPG).

## Logo.py quick start

This script generates pixel-art style channel assets (avatar, banner, thumbnail, favicon) from a black/white silhouette image using repeated text (default: `OXK`).

Files created
- `out/avatar_512.png` — square avatar (512×512)
- `out/favicon_32.png` — favicon-sized image (32×32)
- `out/favicon.ico` — Windows/Mac favicon
- `out/profile_800.png` — larger profile image (800×800)
- `out/banner_2560x1440.png` — YouTube banner (2560×1440)

Quick start

1. (Optional) Put a black-on-white silhouette image named `your_logo.png` next to `Logo.py`.
2. Install dependencies:

```powershell
C:\Python314\python.exe -m pip install -r requirements.txt
```

3. Run the generator:

```powershell
C:\Python314\python.exe "c:\Users\hshar\OneDrive\Desktop\Logo\Logo.py" --text "OXK" --out out
```

Customize
- `--input / -i` to specify a different silhouette file.
- `--text / -t` to change the repeating characters.
- `--font / -f` to point to a .ttf font file for the characters used.
- `--out / -o` to change output directory.

Notes
- The script will create a placeholder silhouette if no input file is found.
- The generated assets use a block/grid approach so they keep a pixel-art look.
- If you want different sizes or block sizes, edit the `assets` dict inside `Logo.py`.

## High-resolution brand set

Run the dedicated generator to export the 2048×2048 logo and 5120×2880 banner (PNG + JPG):

```powershell
C:\Python314\python.exe "c:\Users\hshar\OneDrive\Desktop\Logo\create_oxk_brand.py"
```

Outputs are stored in `out/brand/`:
- `logo_1024.png`
- `logo_2048.png`
- `banner_2560x1440.png`
- `banner_2560x1440.jpg`
- `banner_5120x2880.png`
- `banner_5120x2880.jpg`

All assets use deterministic mosaic alignment, neon glow, spotlight lighting, and subtle tech-grid backgrounds for a cohesive OXK Pixel identity.