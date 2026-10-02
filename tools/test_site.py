"""Site-wide guards for the Felt and Neon design. Python 3.8+, no packages:
python -m unittest discover -s tools
"""
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402
from test_build_directory import published  # noqa: E402

CSS = b.ROOT / "assets" / "site.css"
PALETTE = ("#0E1512", "#18221C", "#131C17", "#1E2A23", "#EAF2ED", "#B4C3BA", "#8A9C90", "#5E7268",
           "#28312C", "#C6F24E", "#3FD597", "#101010", "#F4C81E", "#2F6BE0", "#C8453A", "#F4F4EE")
OLD_PALETTE = ("#0C3B2A", "#FFC66E")
GREEK_RANGES = ("U+0370-03FF", "U+1F00-1FFF")
HEADER_HEIGHT_PX = 64


def css():
    return CSS.read_text(encoding="utf-8")


def font_faces(text):
    return re.findall(r"@font-face\s*{([^}]*)}", text)


class StylesheetTest(unittest.TestCase):

    def test_greek_and_latin_faces_cover_their_scripts(self):
        faces = font_faces(css())
        self.assertEqual(len(faces), 4, "two families, each with a Latin and a Greek face")
        for family in ("RackUp Display", "RackUp Text"):
            mine = [f for f in faces if f'"{family}"' in f]
            self.assertEqual(len(mine), 2, family)
            greek = [f for f in mine if "commissioner-greek.woff2" in f]
            self.assertEqual(len(greek), 1, f"{family} has no Commissioner face")
            for span in GREEK_RANGES:
                self.assertIn(span, greek[0].replace(" ", ""), f"{family} Greek face misses {span}")
            latin = [f for f in mine if f not in greek][0]
            weight = lambda face: re.search(r"font-weight\s*:\s*([^;}]+)", face).group(1).strip()
            # Chrome only merges faces with identical descriptors, so a different weight hides Greek.
            self.assertEqual(weight(greek[0]), weight(latin), f"{family}: Greek and Latin faces differ in font-weight")
            self.assertRegex(latin, r"(space-grotesk|hanken-grotesk)-latin\.woff2", family)
            self.assertIn("font-display:swap", latin.replace(" ", ""))
        for ref in re.findall(r"url\(\s*['\"]?([^'\")]+)", css()):
            self.assertTrue((CSS.parent / ref).is_file(), f"site.css points at missing {ref}")

    def test_anchors_clear_the_sticky_header(self):
        rules = re.findall(r"([^{}]+){([^}]*scroll-margin-top\s*:\s*(\d+)px[^}]*)}", css())
        selectors = " ".join(sel for sel, _, px in rules if int(px) >= HEADER_HEIGHT_PX)
        self.assertRegex(selectors, r"\[id\]", "hall QR anchors would land under the sticky header")

    def test_motion_stops_under_reduced_motion(self):
        block = re.search(r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*{(.*?)}\s*}", css(), re.S)
        self.assertIsNotNone(block, "no reduced-motion block")
        self.assertRegex(block.group(1), r"animation\s*:\s*none")

    def test_stylesheet_carries_the_app_palette(self):
        text = css().upper()
        for colour in PALETTE:
            self.assertIn(colour, text, colour)
        for colour in OLD_PALETTE:
            self.assertNotIn(colour, text, colour)
        self.assertLess(CSS.stat().st_size, 25 * 1024)



def head_links(text):
    return dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)">', text))


class PagesTest(unittest.TestCase):

    def test_homes_are_an_hreflang_pair(self):
        pair = {"index.html": ("el", "https://getrackup.com/"), "en/index.html": ("en", "https://getrackup.com/en/")}
        for page, (lang, canonical) in pair.items():
            text = (b.ROOT / page).read_text(encoding="utf-8")
            self.assertIn(f'<html lang="{lang}">', text, page)
            self.assertIn(f'<link rel="canonical" href="{canonical}">', text, page)
            self.assertEqual(head_links(text), {"el": "https://getrackup.com/", "en": "https://getrackup.com/en/",
                                                "x-default": "https://getrackup.com/"}, page)

    def test_every_image_has_alt_and_size(self):
        for rel, text in published(".html"):
            for tag in re.findall(r"<img\b[^>]*>", text):
                for attr in ("alt", "width", "height"):
                    self.assertRegex(tag, rf'\s{attr}="[^"]+"', f"{rel}: {tag}")

    def test_faq_jsonld_matches_visible_faq(self):
        for page in ("index.html", "en/index.html"):
            text = (b.ROOT / page).read_text(encoding="utf-8")
            data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.S).group(1))
            faq = [n for n in data["@graph"] if n["@type"] == "FAQPage"][0]["mainEntity"]
            seen = re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", text)
            self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq], seen, page)

if __name__ == "__main__":
    unittest.main()
