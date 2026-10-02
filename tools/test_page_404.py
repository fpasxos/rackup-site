"""The 404 page. Python 3.8+, no packages:
python -m unittest discover -s tools
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402

PAGE = b.ROOT / "404.html"


class NotFoundPageTest(unittest.TestCase):

    def test_not_found_page_helps(self):
        self.assertTrue(PAGE.is_file(), "404.html is missing")
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn('<meta name="robots" content="noindex">', text)
        hrefs = re.findall(r'\shref="([^"]*)"', text)
        for target in ("/", "/en/", "/mpiliardo/"):
            self.assertIn(target, hrefs, f"404.html does not link {target}")
        # GitHub Pages serves this file at any depth, so a relative path would break.
        for value in re.findall(r'\s(?:href|src)="([^"]*)"', text):
            if value.startswith(("mailto:", "https://", "#")):
                continue
            self.assertRegex(value, r"^/(?!/)", f"404.html uses {value!r}, not a root-relative path")
        self.assertTrue(any(h.startswith("https://apps.apple.com/") for h in hrefs), "no App Store link")
        self.assertTrue(any(h.startswith("https://play.google.com/") for h in hrefs), "no Google Play link")
        self.assertEqual(b.HAND_PAGES.get("404.html"), "404.html", "the build would not tag its store links")
        self.assertEqual(b.campaign_for("404.html"), "404")


if __name__ == "__main__":
    unittest.main()
