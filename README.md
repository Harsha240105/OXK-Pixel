# OXK Pixel

My YouTube channel branding — logos, banners, and pixel-art assets.

## Logo

![OXK Logo](assets/OXK_logo_art.png)

![OXK Centered Logo](assets/logo_1024_centered.png)

## Channel Banner

![OXK Banner](assets/OXK_Pixel_Banner.png)

![YouTube Banner 2560x1440](assets/banner_2560x1440.png)

## Hi-Res Banner (5120x2880)

![Hi-Res Banner](assets/banner_5120x2880.png)

## Avatar & Profile

![Avatar](assets/avatar_512.png)

![Profile](assets/profile_800.png)

## Thumbnail

![Thumbnail](assets/thumbnail_1280x720.png)

## Scripts

| Script | What it does |
|--------|-------------|
| `Logo.py` | Pixel-art assets from a silhouette (avatar, banner, thumbnail, favicon) |
| `create_oxk_logo.py` | 1600x600 glowing OXK intro banner |
| `create_oxk_square.py` | 800x800 cyan mosaic avatar |
| `create_oxk_avatar.py` | 1024x1024 avatar with grid alignment |
| `create_oxk_banner.py` | 2560x1440 YouTube banner |
| `create_oxk_brand.py` | Full brand set (2048 logo + 5120x2880 banner) |
| `create_oxk_logo_centered.py` | Centered logo variant |

## Generate

```powershell
pip install -r requirements.txt
python Logo.py --text "OXK" --out out
```

## License

MIT
