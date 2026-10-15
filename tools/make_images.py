"""Rebuilds assets/img from the iPhone captures in the sibling rackup repo. Dev only:
pip install Pillow && python tools/make_images.py [path/to/store-shots/raw/ios]
After rendering tools/og-card.html to assets/og-card.png: python tools/make_images.py --og-card
1-venues.png is left out: its hall count is a snapshot that goes stale as halls are added.
A screen with no capture there (4-venue.png since 2.3.3) keeps the webp it has.
"""
import math
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
# The unframed captures; from 2.3.3 the listing set itself carries captions.
SOURCE = ROOT.parent / "rackup" / "store-assets" / "store-shots" / "raw" / "ios"
OUT = ROOT / "assets" / "img"
OG_CARD = ROOT / "assets" / "og-card.png"
LANGS = {"el": "el", "en": "en-GB"}
SCREENS = {"venue": "4-venue.png", "create": "2-create.png", "welcome": "5-welcome.png"}
WIDTHS = (360, 720)


def build(source):
    OUT.mkdir(parents=True, exist_ok=True)
    for lang, folder in LANGS.items():
        for screen, name in SCREENS.items():
            if not (source / folder / name).is_file():
                print(f"kept assets/img/{lang}-{screen}-*.webp: no {folder}/{name} in {source}")
                continue
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
    for path in (OG_CARD, OG_CARD.with_name("og-card-en.png")):
        with Image.open(path) as card:
            card = card.convert("RGB")
        card.save(path, "PNG", optimize=True)
        print(f"{path.relative_to(ROOT)}  {card.width}x{card.height}  {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    if sys.argv[1:] == ["--og-card"]:
        optimise_og_card()
    else:
        build(Path(sys.argv[1]) if len(sys.argv) > 1 else SOURCE)
