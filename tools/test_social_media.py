"""Media under media/social/, which Instagram fetches by URL. Python 3.8+, no packages:
python -m unittest discover -s tools
"""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402

MEDIA = b.ROOT / "media" / "social"
# Instagram's limits: JPEG only, 8 MB, 320 to 1440 px wide; Story videos 100 MB.
JPEG_MAX = 8 * 1024 * 1024
VIDEO_MAX = 100 * 1024 * 1024
SIZES = {(1080, 1350), (1080, 1920)}


def jpeg_size(data):
    """(width, height) from the first SOF marker, or None."""
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            return None
        marker = data[i + 1]
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + length
    return None


def mp4_boxes(data):
    out, i = [], 0
    while i + 8 <= len(data):
        size, kind = struct.unpack(">I4s", data[i:i + 8])
        if size == 1:
            size = struct.unpack(">Q", data[i + 8:i + 16])[0]
        out.append(kind)
        if size < 8:
            break
        i += size
    return out


class SocialMediaTest(unittest.TestCase):

    def files(self):
        return sorted(p for p in MEDIA.rglob("*") if p.is_file()) if MEDIA.is_dir() else []

    def test_only_instagram_ready_files(self):
        for p in self.files():
            rel = p.relative_to(b.ROOT).as_posix()
            data = p.read_bytes()
            if p.suffix == ".jpg":
                self.assertLessEqual(len(data), JPEG_MAX, rel)
                self.assertIn(jpeg_size(data), SIZES, f"{rel} is not a 4:5 or 9:16 JPEG at 1080 px")
            elif p.suffix == ".mp4":
                self.assertLessEqual(len(data), VIDEO_MAX, rel)
                boxes = mp4_boxes(data)
                self.assertEqual(boxes[0], b"ftyp", rel)
                self.assertLess(boxes.index(b"moov"), boxes.index(b"mdat"),
                                f"{rel}: moov after mdat, Meta cannot stream it")
            else:
                self.fail(f"{rel}: only .jpg and .mp4 belong in media/social/")

    def test_nothing_links_to_them(self):
        # Unlisted on purpose: no page, script or the sitemap points here.
        for p in b.ROOT.rglob("*"):
            if p.suffix not in (".html", ".xml", ".js", ".css", ".txt") or not p.is_file():
                continue
            rel = p.relative_to(b.ROOT).as_posix()
            if rel.split("/")[0] in (".git", "tools", "docs", "data"):
                continue
            self.assertNotIn("media/social", p.read_text(encoding="utf-8", errors="replace"), rel)


if __name__ == "__main__":
    unittest.main()
