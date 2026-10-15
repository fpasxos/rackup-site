"""The RackUp logo on every page: the favicon set in the head, the 10-ball rack mark in the wordmark.
Python 3.8+, no packages: python -m unittest discover -s tools
"""
import re
import struct
import sys
import unittest
from pathlib import Path
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402
from test_build_directory import published, rendered_pages  # noqa: E402
from test_social_links import HAND  # noqa: E402

ICONS = (('rel="icon"', "favicon.ico", 'sizes="32x32"'),
         ('rel="icon"', "assets/favicon.svg", 'type="image/svg+xml"'),
         ('rel="apple-touch-icon"', "assets/apple-touch-icon.png", None))


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    assert head[:8] == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"
    return struct.unpack(">II", head[16:24])


class LogoTest(unittest.TestCase):

    def test_every_page_links_the_favicon_set_and_each_file_exists(self):
        checked = set()
        for rel, text in published(".html"):
            links = re.findall(r'<link rel="(?:icon|apple-touch-icon)"[^>]*>', text)
            with self.subTest(page=rel):
                self.assertEqual(len(links), len(ICONS), f"{rel}: {links}")
                for (kind, target, extra), tag in zip(ICONS, links):
                    self.assertIn(kind, tag)
                    if extra:
                        self.assertIn(extra, tag)
                    href = re.search(r'href="([^"]+)"', tag).group(1)
                    resolved = urljoin("https://getrackup.com/" + rel, href)
                    self.assertEqual(resolved, "https://getrackup.com/" + target, f"{rel}: {href}")
            checked.add(rel)
        self.assertEqual((HAND | rendered_pages()) - checked, set(), "pages the walk never reached")

    def test_the_icon_files_are_the_sizes_their_tags_promise(self):
        self.assertEqual(png_size(b.ROOT / "assets" / "apple-touch-icon.png"), (180, 180))
        self.assertEqual(png_size(b.ROOT / "assets" / "icon-512.png"), (512, 512), "the structured data says 512")
        ico = (b.ROOT / "favicon.ico").read_bytes()
        self.assertEqual(ico[:4], b"\x00\x00\x01\x00", "favicon.ico is not an icon file")
        count = struct.unpack("<H", ico[4:6])[0]
        sizes = {ico[6 + 16 * i] or 256 for i in range(count)}
        self.assertIn(32, sizes, "the head promises a 32 px favicon")
        svg = (b.ROOT / "assets" / "favicon.svg").read_text(encoding="utf-8")
        self.assertIn("<svg", svg)

    def test_every_wordmark_draws_the_rack_and_no_8_ball(self):
        for rel, text in published(".html"):
            marks = re.findall(r'<(?:a|span) class="wordmark"[^>]*>(.*?)<span class="wm">', text, re.S)
            with self.subTest(page=rel):
                self.assertTrue(marks, f"{rel}: no wordmark")
                for mark in marks:
                    self.assertEqual(mark, b.MARK, f"{rel}: the wordmark's mark is not the logo's")

    def test_the_mark_is_a_ten_ball_rack_with_the_10_in_lime(self):
        circles = re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="7.2"( fill="#C6F24E")?/>', b.MARK)
        self.assertEqual(len(circles), 10, "a real 10-ball rack has ten balls")
        lime = [(x, y) for x, y, accent in circles if accent]
        self.assertEqual(lime, [("40.2", "44.006")], "only the 10, in the middle of the third row, is lime")


if __name__ == "__main__":
    unittest.main()
