"""Rebuilds assets/img from the iOS store screenshots in the sibling rackup repo. Dev only:
pip install Pillow && python tools/make_images.py [path/to/ios-screenshots]
After rendering tools/og-card.html to assets/og-card.png: python tools/make_images.py --og-card
Never add 1-venues.png: it shows a stale hall count.
"""
import math
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT.parent / "rackup" / "store-assets" / "ios-screenshots"
OUT = ROOT / "assets" / "img"
OG_CARD = ROOT / "assets" / "og-card.png"
LANGS = {"el": "el", "en": "en-GB"}
SCREENS = {"venue": "4-venue.png", "create": "2-create.png", "welcome": "5-welcome.png"}
WIDTHS = (360, 720)


def build(source):
    OUT.mkdir(parents=True, exist_ok=True)
    for lang, folder in LANGS.items():
        for screen, name in SCREENS.items():
            with Image.open(source / folder / name) as shot:
                shot = shot.convert("RGB")
                # 1x height rounded up so 2x is exactly double; srcset pairs stay true density pairs.
                one_x = math.ceil(WIDTHS[0] * shot.height / shot.width)
                for width in WIDTHS:
                    height = one_x * width // WIDTHS[0]
                    out = OUT / f"{lang}-{screen}-{width}.webp"
                    shot.resize((width, height), Image.LANCZOS).save(out, "WEBP", quality=80, method=6)
                    print(f"{out.relative_to(ROOT)}  {width}x{height}  {out.stat().st_size:,} bytes")


def optimise_og_card():
    # Lossless only: a 256-colour palette bands the glow and the 9 and 10 balls.
    with Image.open(OG_CARD) as card:
        card = card.convert("RGB")
    card.save(OG_CARD, "PNG", optimize=True)
    print(f"{OG_CARD.relative_to(ROOT)}  {card.width}x{card.height}  {OG_CARD.stat().st_size:,} bytes")


if __name__ == "__main__":
    if sys.argv[1:] == ["--og-card"]:
        optimise_og_card()
    else:
        build(Path(sys.argv[1]) if len(sys.argv) > 1 else SOURCE)
