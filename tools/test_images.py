"""Guards the screenshots and the social card. Python 3.8+, no packages:
python -m unittest discover -s tools
"""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "assets" / "img"
WEBPS = [IMG / f"{lang}-{screen}-{width}.webp"
         for lang in ("el", "en") for screen in ("venue", "create", "welcome") for width in (360, 720)]
WEBP_MAX = 60 * 1024
OG_MAX = 300 * 1024
# Old cards that link previews cached before the switch still fetch by URL. No page names them
# (tools/test_site.py). Delete them, and this, after about 12 December 2026.
RETIRED_CARDS = ("og-card.png", "og-card-en.png")


def webp_size(data):
    """(width, height) from a RIFF/WEBP header with a VP8, VP8L or VP8X first chunk."""
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("not a WebP file")
    chunk = data[12:16]
    if chunk == b"VP8 ":
        if data[23:26] != b"\x9d\x01\x2a":
            raise ValueError("VP8 frame without its start code")
        w, h = struct.unpack("<HH", data[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if chunk == b"VP8L":
        if data[20] != 0x2F:
            raise ValueError("VP8L without its signature")
        bits = struct.unpack("<I", data[21:25])[0]
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8X":
        w = int.from_bytes(data[24:27], "little") + 1
        h = int.from_bytes(data[27:30], "little") + 1
        return w, h
    raise ValueError(f"unknown WebP chunk {chunk!r}")


def png_size(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("not a PNG file")
    return struct.unpack(">II", data[16:24])


class ImagesTest(unittest.TestCase):

    def test_images_are_light_and_sized(self):
        for path in WEBPS:
            with self.subTest(image=path.name):
                self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")
                data = path.read_bytes()
                self.assertLess(len(data), WEBP_MAX, f"{path.name} is {len(data)} bytes")
                width, _ = webp_size(data)
                self.assertIn(width, (360, 720), path.name)
                self.assertEqual(width, int(path.stem.rsplit("-", 1)[1]), "width disagrees with the name")
        for card in (ROOT / name for name in b.OG_CARD.values()):
            self.assertTrue(card.is_file(), f"missing assets/{card.name}")
            data = card.read_bytes()
            self.assertEqual(png_size(data), (1200, 630), card.name)
            self.assertLess(len(data), OG_MAX, f"{card.name} is {len(data)} bytes")

    def test_only_the_current_and_retired_cards_are_kept(self):
        """Pages name only a current card; a retired one stays a real card for cached previews."""
        self.assertEqual({card.name for card in (ROOT / "assets").glob("og-card*.png")},
                         {Path(name).name for name in b.OG_CARD.values()} | set(RETIRED_CARDS))
        for name in RETIRED_CARDS:
            self.assertEqual(png_size((ROOT / "assets" / name).read_bytes()), (1200, 630), name)


if __name__ == "__main__":
    unittest.main()
