"""RackUp's Instagram and Facebook: linked from every page's footer, named in the home's structured data.
Python 3.8+, no packages: python -m unittest discover -s tools
"""
import json
import re
import sys
import unittest
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402
from test_build_directory import published, rendered_pages  # noqa: E402

# Literals, so a typo in the generator's constants fails here too.
PROFILES = {"Instagram": "https://www.instagram.com/rackupbilliard/",
            "Facebook": "https://www.facebook.com/rackupbilliard"}
LABEL = {"el": "RackUp στο {}", "en": "RackUp on {}"}
HAND = {"index.html", "en/index.html", "404.html", "support.html", "privacy.html", "m/index.html", "go/index.html"}


def footer(rel, text):
    found = re.findall(r'<footer class="site-footer">(.*?)</footer>', text, re.S)
    if len(found) != 1:
        raise AssertionError(f"{rel}: expected one site footer, found {len(found)}")
    return found[0]


class SocialLinksTest(unittest.TestCase):

    def test_generator_links_the_real_profiles(self):
        self.assertEqual(b.INSTAGRAM, PROFILES["Instagram"])
        self.assertEqual(b.FACEBOOK, PROFILES["Facebook"])

    def test_every_page_links_both_profiles_from_its_footer(self):
        checked = set()
        for rel, text in published(".html"):
            lang = re.search(r'<html lang="(el|en)">', text).group(1)
            foot = footer(rel, text)
            for name, link in PROFILES.items():
                with self.subTest(page=rel, profile=name):
                    tags = re.findall(rf'<a href="{re.escape(link)}"[^>]*>{name}</a>', foot)
                    self.assertEqual(len(tags), 1, f"{rel}: the footer should link {link} once")
                    self.assertIn('rel="noopener"', tags[0])
                    self.assertIn(f'aria-label="{LABEL[lang].format(name)}"', tags[0], "label in the page's language")
            checked.add(rel)
        missing = (HAND | rendered_pages()) - checked
        self.assertEqual(missing, set(), "pages the walk never reached")

    def test_home_organization_names_both_profiles(self):
        text = (b.ROOT / "index.html").read_text(encoding="utf-8")
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)
        self.assertEqual(len(blocks), 1, "one JSON-LD block on the home")
        nodes = json.loads(blocks[0])["@graph"]
        (org,) = [n for n in nodes if n["@type"] == "Organization"]
        self.assertEqual((org["name"], org["url"]), ("RackUp", "https://getrackup.com/"))
        for link in PROFILES.values():
            self.assertIn(link, org["sameAs"])
        self.assertEqual(len(org["sameAs"]), len(set(org["sameAs"])), "a profile is listed twice")
        self.assertNotIn("facebook.com/profile.php", text, "the numeric Facebook URL is replaced by the name")
        logo = urlsplit(org["logo"]["url"]).path.lstrip("/")
        self.assertTrue((b.ROOT / logo).is_file(), f"logo {logo} is not on the site")
        (app,) = [n for n in nodes if n["@type"] == "MobileApplication"]
        self.assertEqual(app["publisher"], {"@id": org["@id"]})


if __name__ == "__main__":
    unittest.main()
