"""Country hubs: a hub country's own page, linked from its cities, from both homes and from the directory.
Python 3.8+, no packages: python -m unittest discover -s tools
"""
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402
from test_directory_seo import description, node, structured, title, visible_crumbs, visible_text  # noqa: E402

LANGS = (("el", b.EL_ROOT), ("en", b.EN_ROOT))
GREEK = re.compile("[Ͱ-Ͽἀ-῿]")


class CountryHubTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.files = b.render()
        cls.cities = b.group_by_city(b.load_venues())
        cls.mine = b.by_country(cls.cities)["CY"]

    def hub(self, lang):
        root = dict(LANGS)[lang]
        return self.files[b.ROOT / root / "kypros" / "index.html"]

    def test_cyprus_has_a_hub_in_both_languages_and_greece_none(self):
        self.assertEqual(b.hubs_of(self.cities), {"CY": "kypros"})
        for lang, root in LANGS:
            text = self.hub(lang)
            self.assertIn(f'<link rel="canonical" href="{b.url(f"{root}/kypros/")}">', text)
            for other, other_root in LANGS:
                self.assertIn(f'<link rel="alternate" hreflang="{other}" href="{b.url(f"{other_root}/kypros/")}">', text)
            self.assertIn(f'<html lang="{lang}">', text)
        hubs = [p for p in self.files if p.parent.name in b.HUBS.values()]
        self.assertEqual(len(hubs), 2, "one page per language, and none for a country outside HUBS")

    def test_the_hub_lists_its_countrys_cities_with_their_counts(self):
        n = sum(len(h) for h in self.mine.values())
        for lang, root in LANGS:
            text, order = self.hub(lang), b.city_order(self.mine, lang)
            grid = re.search(r'<ul class="city-grid">(.*?)</ul>', text, re.S).group(1)
            self.assertEqual(re.findall(r'href="\.\./([^/]+)/"', grid), [b.CITIES[c][0] for c in order], lang)
            listing = node(structured(text), "ItemList")
            self.assertEqual(listing["numberOfItems"], len(self.mine))
            self.assertEqual([i["url"] for i in listing["itemListElement"]],
                             [b.url(f"{root}/{b.CITIES[c][0]}/") for c in order])
            lead = re.search(r'<p class="lead">(.*?)</p>', text, re.S).group(1)
            self.assertIn(f"{n} αίθουσες σε {len(self.mine)} πόλεις" if lang == "el"
                          else f"{n} halls in {len(self.mine)} cities", lead)
            self.assertIn("τη διεύθυνση και το τηλέφωνο" if lang == "el" else "address and phone number", lead,
                          "every Cypriot hall has a phone")

    def test_the_hub_speaks_of_its_own_country_and_no_other(self):
        greek_cities = [c for c, h in self.cities.items() if b.country_of(h) != "CY"]
        for lang, _ in LANGS:
            text = self.hub(lang)
            # The page's own words: the shared header and footer carry «ΕΛ» and the Ioannina address.
            main = re.search(r'<main id="main">(.*)</main>', text, re.S).group(1)
            said = " ".join([title(text), description(text), visible_text(f"<body>{main}</body>")])
            self.assertIn("στην Κύπρο" if lang == "el" else "in Cyprus", said)
            for city in greek_cities:
                name = b.CITIES[city][1] if lang == "el" else city
                self.assertNotRegex(said, rf"\b{re.escape(name)}\b", f"{lang} names {city}")
            if lang == "en":
                self.assertNotRegex(said, GREEK)

    def test_the_hub_claims_no_carom_its_halls_lack(self):
        halls = [v for h in self.mine.values() for v in h]
        self.assertFalse(any(b.offers_carom(v) for v in halls), "a Cypriot hall has carom now: revisit the hub")
        for lang, _ in LANGS:
            text = self.hub(lang)
            main = re.search(r'<main id="main">(.*)</main>', text, re.S).group(1)
            # The download card is the one shared pitch, and it says «στις αίθουσες με τραπέζια γαλλικού».
            own = re.sub(r'<section class="cta-card".*?</section>', "", main, flags=re.S)
            said = " ".join([title(text), description(text), re.sub(r"<[^>]+>", " ", own)])
            self.assertNotRegex(said, r"(?i)γαλλικ|τρίσποντ|μονόσποντ|carom|cushion", lang)

    def test_snippets_fit_and_greek_keeps_its_floor(self):
        for lang, _ in LANGS:
            text = self.hub(lang)
            self.assertLessEqual(len(title(text)), b.TITLE_LIMIT, lang)
            self.assertLessEqual(len(description(text)), b.DESCRIPTION_LIMIT, lang)
            for city in self.mine:
                self.assertIn(b.CITIES[city][1] if lang == "el" else city, description(text), city)
        self.assertGreaterEqual(len(description(self.hub("el"))), 110)
        self.assertTrue(description(self.hub("el")).startswith("Μπιλιάρδα στην Κύπρο: "))

    def test_hub_cities_crumbs_pass_through_the_hub_and_no_other_city_does(self):
        for city, halls in self.cities.items():
            for lang, root in LANGS:
                crumbs = visible_crumbs(self.files[b.ROOT / root / b.CITIES[city][0] / "index.html"])
                if b.country_of(halls) == "CY":
                    country = "Κύπρος" if lang == "el" else "Cyprus"
                    self.assertEqual(crumbs[2], (country, b.url(f"{root}/kypros/")), f"{city} {lang}")
                else:
                    self.assertEqual(len(crumbs), 3, f"{city} {lang}")

    def test_both_homes_and_both_indexes_link_the_hub(self):
        n, c = sum(len(h) for h in self.mine.values()), len(self.mine)
        labels = {"el": f"Μπιλιάρδο στην Κύπρο: {n} αίθουσες σε {c} πόλεις", "en": f"Billiards in Cyprus: {n} halls in {c} cities"}
        for page, lang, href in (("index.html", "el", "mpiliardo/kypros/"), ("en/index.html", "en", "billiards/kypros/"),
                                 (f"{b.EL_ROOT}/index.html", "el", "kypros/"), (f"{b.EN_ROOT}/index.html", "en", "kypros/")):
            text = self.files[b.ROOT / page]
            self.assertEqual(text.count(f'<p class="more"><a href="{href}">{labels[lang]}</a></p>'), 1, page)

    def test_a_hub_slug_never_takes_a_citys(self):
        with mock.patch.dict(b.HUBS, {"CY": "lefkosia"}), self.assertRaises(SystemExit) as stop:
            b.hubs_of(self.cities)
        self.assertIn("is a city's too", str(stop.exception.code))


if __name__ == "__main__":
    unittest.main()
