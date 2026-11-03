"""The carom pages and chips: every hall the data says has carom tables, and no other.
Python 3.8+, no packages: python -m unittest discover -s tools
"""
import html
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402
from test_build_directory import imported, published, site_path  # noqa: E402
from test_directory_seo import (description, node, strip_tags, structured, title, visible_crumbs,  # noqa: E402
                                visible_text)

PAGES = {"el": "galliko-mpiliardo/index.html", "en": "en/carom-billiards/index.html"}
URLS = {"el": "https://getrackup.com/galliko-mpiliardo/", "en": "https://getrackup.com/en/carom-billiards/"}
CHIP = re.compile(r'<p class="tags"><span class="chip"><span class="ball cr" aria-hidden="true"></span>([^<]*)</span></p>')
LINK = re.compile(r'<p class="tags"><a class="chip chip-link" href="([^"]*)">'
                  r'<span class="ball cr" aria-hidden="true"></span>([^<]*)</a></p>')


def hall(vid, city="Larissa", **carom):
    v = {"id": vid, "name": vid.title(), "city": city, "country": "GR", "address": "Odos 1", "sortOrder": 1}
    v.update(carom)
    return v


def absolute(rel, href):
    return urljoin(f"{b.BASE_URL}/{site_path(rel)}", href)


class CaromImportTest(unittest.TestCase):

    def test_import_keeps_carom_only_when_it_says_the_hall_has_it(self):
        backup = [hall("a", caromTables=4), hall("b", caromTables=0), hall("c", hasCarom=True),
                  hall("d", hasCarom=False), hall("e", caromTables=True), hall("f", caromTables="2"),
                  hall("g", caromTables=2, hasCarom=True), hall("h", caromTables=None)]
        records = {r["id"]: r for r in json.loads(imported(backup))}
        carom = {vid: {k: r[k] for k in b.CAROM_FIELDS if k in r} for vid, r in records.items()}
        self.assertEqual(carom, {"a": {"caromTables": 4}, "b": {}, "c": {"hasCarom": True}, "d": {}, "e": {},
                                 "f": {}, "g": {"caromTables": 2, "hasCarom": True}, "h": {}})

    def test_the_build_refuses_carom_values_that_say_nothing(self):
        for bad in ({"caromTables": 0}, {"caromTables": "2"}, {"caromTables": True}, {"hasCarom": False},
                    {"hasCarom": "yes"}):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as tmp:
                data = Path(tmp, "venues.json")
                data.write_text(json.dumps([hall("venue-x", **bad)]), encoding="utf-8")
                with mock.patch.object(b, "DATA", data), self.assertRaises(SystemExit):
                    b.load_venues()

    def test_a_directory_without_carom_is_refused(self):
        cities = {"Larissa": [hall("venue-lar-a")]}
        with self.assertRaises(SystemExit):
            b.index_page(cities, "el")


class CaromChipTest(unittest.TestCase):

    def test_the_chip_gives_the_count_only_when_it_is_known(self):
        cases = {"el": ("Γαλλικό: 4 τραπέζια", "Γαλλικό: 1 τραπέζι", "Γαλλικό", "Γαλλικό: 2 τραπέζια"),
                 "en": ("Carom: 4 tables", "Carom: 1 table", "Carom", "Carom: 2 tables")}
        halls = (hall("a", caromTables=4), hall("b", caromTables=1), hall("c", hasCarom=True),
                 hall("d", caromTables=2, hasCarom=True))
        for lang, expected in cases.items():
            for v, text in zip(halls, expected):
                self.assertEqual(CHIP.findall(b.carom_chip(v, lang)), [text], f"{v} {lang}")

    def test_a_hall_without_carom_has_no_chip(self):
        for lang in ("el", "en"):
            self.assertNotIn('class="chip"', b.hall_item(hall("a"), lang))
            self.assertIn('class="chip"', b.hall_item(hall("a", hasCarom=True), lang))


class CaromSiteTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.files = {p.relative_to(b.ROOT).as_posix(): t for p, t in b.render().items()}
        cls.cities = b.group_by_city(b.load_venues())
        cls.carom = {city: [v for v in halls if b.offers_carom(v)] for city, halls in cls.cities.items()}
        cls.carom = {city: halls for city, halls in cls.carom.items() if halls}
        cls.halls = sum(len(h) for h in cls.carom.values())

    def test_the_data_has_carom_halls_to_show(self):
        self.assertGreater(self.halls, 0)
        for v in b.load_venues():
            self.assertEqual(b.offers_carom(v), bool(v.get("caromTables") or v.get("hasCarom")), v["id"])

    def test_every_carom_hall_is_listed_once_linked_to_its_city_page_anchor(self):
        for lang, rel in PAGES.items():
            text = self.files[rel]
            links = re.findall(r'<h3(?: lang="el")?><a href="([^"]*)">', text)
            want = {v["id"]: v for halls in self.carom.values() for v in halls}
            self.assertEqual(len(links), len(want), f"{rel}: a hall is listed twice or missing")
            for href in links:
                target = urlsplit(absolute(rel, href))
                v = want.pop(target.fragment)
                root = b.EL_ROOT if lang == "el" else b.EN_ROOT
                self.assertEqual(target.path, f"/{root}/{b.CITIES[v['city']][0]}/", href)
                city_page = self.files[f"{target.path.strip('/')}/index.html"]
                self.assertIn(f'id="{v["id"]}"', city_page, f"{href} opens no hall")
            self.assertEqual(want, {}, f"{rel} leaves out {sorted(want)}")
            self.assertEqual(re.findall(r'\sid="(venue-[^"]*)"', text), [],
                             "a hall's anchor lives on its city page only, where its QR code points")

    def test_counts_on_the_carom_pages_come_from_the_data(self):
        n, c = self.halls, len(self.carom)
        lines = {"el": f"{n} αίθουσες σε {c} πόλεις", "en": f"{n} halls in {c} cities"}
        for lang, rel in PAGES.items():
            text = self.files[rel]
            self.assertIn(lines[lang], title(text), rel)
            self.assertIn(lines[lang], visible_text(text), rel)
            listing = node(structured(text), "ItemList")
            self.assertEqual(listing["numberOfItems"], n, rel)
            self.assertEqual(len(listing["itemListElement"]), n, rel)
            for city, halls in self.carom.items():
                slug = b.CITIES[city][0]
                section = re.search(rf'<section class="carom-city" id="{slug}">(.*?)</section>', text, re.S).group(1)
                self.assertEqual(len(re.findall(r'<li class="hall">', section)), len(halls), f"{rel} {city}")
                label = b.plural_el(len(halls)) if lang == "el" else b.plural_en(len(halls))
                self.assertIn(f'<a href="#{slug}"><span class="city">', text, f"{rel} {city}")
                self.assertRegex(text, rf'<a href="#{slug}"><span class="city">[^<]*</span> '
                                       rf'<span class="count">{label}</span></a>', f"{rel} {city}")
            self.assertEqual(len(re.findall(r'<section class="carom-city"', text)), c, rel)
            chips = CHIP.findall(text)
            self.assertEqual(len(chips), n, rel)
            counted = sum(1 for halls in self.carom.values() for v in halls if b.carom_tables(v))
            self.assertEqual(sum(1 for t in chips if re.search(r"\d", t)), counted, rel)

    def test_halls_are_the_same_places_as_on_the_city_pages(self):
        for lang, rel in PAGES.items():
            items = [li["item"] for li in node(structured(self.files[rel]), "ItemList")["itemListElement"]]
            ids = {v["id"]: v for halls in self.carom.values() for v in halls}
            for item in items:
                v = ids[item["@id"].rsplit("#", 1)[1]]
                self.assertEqual(item, b.business(v), rel)

    def test_city_pages_carry_carom_chips_exactly_where_the_data_has_carom(self):
        for city, halls in self.cities.items():
            slug = b.CITIES[city][0]
            mine = [v for v in halls if b.offers_carom(v)]
            for lang, root in (("el", b.EL_ROOT), ("en", b.EN_ROOT)):
                rel = f"{root}/{slug}/index.html"
                text = self.files[rel]
                with self.subTest(page=rel):
                    links = LINK.findall(text)
                    if not mine:
                        self.assertEqual(links, [])
                        self.assertEqual(CHIP.findall(text), [])
                        continue
                    ((href, label),) = links
                    self.assertEqual(absolute(rel, href), f"{URLS[lang]}#{slug}")
                    count = b.plural_el(len(mine)) if lang == "el" else b.plural_en(len(mine))
                    self.assertTrue(label.endswith(count), label)
                    for v in halls:
                        card = re.search(rf'<li class="hall" id="{v["id"]}">(.*?)</li>', text, re.S).group(1)
                        self.assertEqual(bool(CHIP.search(card)), b.offers_carom(v), v["id"])

    def test_directory_indexes_link_the_carom_page_with_its_counts(self):
        n, c = self.halls, len(self.carom)
        expected = {"el": f"Γαλλικό μπιλιάρδο: {n} αίθουσες σε {c} πόλεις",
                    "en": f"Carom billiards: {n} halls in {c} cities"}
        for lang, root in (("el", b.EL_ROOT), ("en", b.EN_ROOT)):
            rel = f"{root}/index.html"
            ((href, label),) = LINK.findall(self.files[rel])
            self.assertEqual(absolute(rel, href), URLS[lang], rel)
            self.assertEqual(label, expected[lang], rel)

    def test_homes_link_the_carom_page_from_the_games_tile(self):
        for home, lang in b.HOMES.items():
            tile = re.search(r"<h3>(?:Αμερικάνικο και γαλλικό|Pool and carom)</h3>\s*<p>(.*?)</p>",
                             self.files[home], re.S).group(1)
            hrefs = re.findall(r'<a href="([^"]*)">', tile)
            self.assertEqual([absolute(home, h) for h in hrefs], [URLS[lang]], home)

    def test_every_footer_links_the_carom_page_in_its_language(self):
        checked = 0
        for rel, text in published(".html"):
            lang = re.search(r'<html lang="(el|en)">', text).group(1)
            footer = re.search(r'<footer class="site-footer">.*?</footer>', text, re.S).group(0)
            # The 404 page is served at any depth, so it links from the root.
            base = f"{b.BASE_URL}/" if rel == "404.html" else f"{b.BASE_URL}/{site_path(rel)}"
            hrefs = {urljoin(base, h) for h in re.findall(r'<a href="([^"]*)"', footer)}
            self.assertIn(URLS[lang], hrefs, rel)
            checked += 1
        self.assertGreater(checked, 90, "too few pages read")

    def test_sitemap_lists_both_pages_and_they_are_an_hreflang_pair(self):
        sitemap = self.files["sitemap.xml"]
        for lang, rel in PAGES.items():
            self.assertEqual(sitemap.count(f"<loc>{URLS[lang]}</loc>"), 1, lang)
            text = self.files[rel]
            self.assertIn(f'<html lang="{lang}">', text)
            self.assertIn(f'<link rel="canonical" href="{URLS[lang]}">', text)
            self.assertIn(f'<link rel="alternate" hreflang="el" href="{URLS["el"]}">', text)
            self.assertIn(f'<link rel="alternate" hreflang="en" href="{URLS["en"]}">', text)
            self.assertIn(f'<link rel="alternate" hreflang="x-default" href="{URLS["el"]}">', text)
            self.assertIn(f'<meta property="og:url" content="{URLS[lang]}">', text)

    def test_titles_and_descriptions_fit_and_no_other_page_shares_them(self):
        others = {description(t) for rel, t in self.files.items()
                  if rel.endswith(".html") and rel not in PAGES.values() and '<meta name="description"' in t}
        for rel in PAGES.values():
            text = self.files[rel]
            self.assertLessEqual(len(title(text)), b.TITLE_LIMIT, title(text))
            self.assertTrue(title(text).endswith("| RackUp"), title(text))
            self.assertLessEqual(len(description(text)), b.DESCRIPTION_LIMIT, description(text))
            self.assertNotIn(description(text), others, rel)
        self.assertNotEqual(description(self.files[PAGES["el"]]), description(self.files[PAGES["en"]]))

    def test_breadcrumbs_in_json_ld_match_the_visible_ones(self):
        for lang, rel in PAGES.items():
            text = self.files[rel]
            trail = node(structured(text), "BreadcrumbList")["itemListElement"]
            self.assertEqual([(c["name"], c["item"]) for c in trail], visible_crumbs(text), rel)
            self.assertEqual(trail[0]["item"], f"{b.BASE_URL}/" if lang == "el" else f"{b.BASE_URL}/en/")
            self.assertEqual(trail[-1]["item"], URLS[lang])

    def test_copy_names_the_games_as_the_app_does(self):
        greek = visible_text(self.files[PAGES["el"]])
        for word in ("Γαλλικό μπιλιάρδο", "τρίσποντο", "μονόσποντο"):
            self.assertIn(word.lower(), greek.lower(), word)
        # 1-cushion is «μονόσποντο», never «σπόντα»; pool is «αμερικάνικο», never «πουλ».
        self.assertNotRegex(greek, r"(?i)\bσπόντα\b|\bπουλ\b")
        english = visible_text(self.files[PAGES["en"]])
        for word in ("Carom billiards", "3-cushion", "1-cushion"):
            self.assertIn(word, english)

    def test_no_published_file_cites_carom_gr(self):
        # A fan site's compiled list: a lead for research, never a source the site names.
        for rel, text in published(".html", ".xml", ".json", ".txt", ".js", ".css"):
            self.assertNotIn("carom.gr", text.lower(), rel)


WHERE = {"el": "Πού παίζω γαλλικό μπιλιάρδο;", "en": "Where can I play carom?"}


def faq_of(text):
    """The visible questions and answers, as text."""
    return [(html.unescape(q), html.unescape(a))
            for q, a in re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", text)]


def own_copy(text):
    """The explainer and the FAQ: the page's new words, without its hall listings or the shared card."""
    return re.search(r'<section class="carom-about".*?<section class="carom-faq".*?</section>', text, re.S).group(0)


class CaromExplainerTest(unittest.TestCase):
    """Audit fix 4: how carom is played and a FAQ, on both carom pages."""

    @classmethod
    def setUpClass(cls):
        cls.files = {p.relative_to(b.ROOT).as_posix(): t for p, t in b.render().items()}
        cls.cities = b.group_by_city(b.load_venues())
        cls.carom = b.carom_by_city(cls.cities)

    def test_the_faq_and_its_structured_data_say_the_same(self):
        for rel in PAGES.values():
            text = self.files[rel]
            faq = node(structured(text), "FAQPage")["mainEntity"]
            self.assertEqual([(q["name"], q["acceptedAnswer"]["text"]) for q in faq], faq_of(text), rel)
            self.assertEqual(len(faq), 4, rel)

    def test_the_explainer_says_plainly_how_both_games_are_played(self):
        expected = {"el": ("χωρίς τρύπες", "τρεις μπάλες", "τουλάχιστον τρεις φορές", "τουλάχιστον μία φορά"),
                    "en": ("without pockets", "three balls", "at least three times", "at least once")}
        for lang, rel in PAGES.items():
            text = self.files[rel]
            self.assertIn('<section class="carom-about" id="how-to-play">', text, "the explainer is never folded")
            said = strip_tags(own_copy(text))
            for phrase in expected[lang]:
                self.assertIn(phrase, said, rel)

    def test_karambola_once_as_a_synonym_and_no_other_spelling(self):
        greek = self.files[PAGES["el"]]  # head, body and structured data alike
        self.assertEqual(len(re.findall(r"(?i)καραμπόλα", greek)), 1)
        self.assertIn("Το γαλλικό μπιλιάρδο, ή καραμπόλα,", greek)
        self.assertNotRegex(greek, r"(?i)καρομπόλα")
        # Never «σπόντα» in any form, as 1-cushion is «μονόσποντο». Hall addresses are data, not copy
        # (Ελλησπόντου 26-28), so this reads the page's own words.
        lead = re.search(r'<p class="lead">(.*?)</p>', greek, re.S).group(1)
        words = " ".join([title(greek), description(greek), lead, strip_tags(own_copy(greek))])
        self.assertNotRegex(words, r"(?i)σπόντ|\bπουλ\b")
        self.assertNotRegex(self.files[PAGES["en"]], r"(?i)carambol|καρ[αο]μπόλα")

    def test_where_to_play_counts_from_the_data_and_names_only_carom_countries(self):
        n, c = sum(len(h) for h in self.carom.values()), len(self.carom)
        counted = [b.carom_tables(v) for halls in self.carom.values() for v in halls if b.carom_tables(v)]
        self.assertEqual(list(b.by_country(self.carom)), ["GR"], "another country has carom now: revisit the copy")
        el = dict(faq_of(self.files[PAGES["el"]]))[WHERE["el"]]
        self.assertIn(f"{n} τέτοιες αίθουσες σε {c} πόλεις, προς το παρόν όλες στην Ελλάδα.", el)
        self.assertIn(f"Μετράμε {sum(counted)} τραπέζια γαλλικού σε {len(counted)} αίθουσες όπου ξέρουμε", el)
        en = dict(faq_of(self.files[PAGES["en"]]))[WHERE["en"]]
        self.assertIn(f"{n} such halls in {c} cities, for now all of them in Greece.", en)
        self.assertIn(f"We count {sum(counted)} carom tables at the {len(counted)} halls where we know", en)
        for rel in PAGES.values():
            self.assertNotRegex(self.files[rel], r"Κύπρ|Cyprus", f"{rel} must not imply carom tables in Cyprus")

    def test_the_country_and_table_lines_follow_the_data(self):
        greek, cyprus = hall("venue-lar-a", caromTables=1), dict(hall("venue-cy-nic-a", city="Nicosia"), country="CY")

        def where(venues, lang):
            cities = b.group_by_city(venues)
            return dict(b.carom_faq(b.carom_by_city(cities), cities, lang))[WHERE[lang]]

        self.assertIn("προς το παρόν όλες στην Ελλάδα.", where([greek, cyprus], "el"))
        self.assertNotIn("προς το παρόν", where([greek], "el"), "one country: nothing to tell apart")
        both = [greek, dict(cyprus, hasCarom=True)]
        self.assertNotIn("προς το παρόν", where(both, "el"))
        self.assertNotIn("for now", where(both, "en"))
        self.assertIn("Μετράμε 1 τραπέζι γαλλικού σε 1 αίθουσα όπου ξέρουμε πόσα έχει.", where([greek], "el"))
        self.assertIn("We count 1 carom table at the 1 hall where we know how many.", where([greek], "en"))
        unknown = [hall("venue-lar-b", hasCarom=True)]
        self.assertNotIn("Μετράμε", where(unknown, "el"), "no count is known, so none is said")
        self.assertNotIn("We count", where(unknown, "en"))

    def test_the_new_copy_names_no_hall_and_claims_no_authority_ranking_or_health(self):
        names = [v["name"] for v in b.load_venues()]
        for rel in PAGES.values():
            said = own_copy(self.files[rel])
            for name in names:
                self.assertNotIn(name, said, rel)
            self.assertNotRegex(said, r"(?i)\bUMB\b|ομοσπονδ|federation|επίσημ|official|κανονισμ|\brules\b|"
                                      r"κορυφαί|καλύτερ|\bbest\b|υγεί|health", rel)


if __name__ == "__main__":
    unittest.main()
