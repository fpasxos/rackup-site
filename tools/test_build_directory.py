"""Tests for tools/build_directory.py. Python 3.8+, no packages:
python -m unittest discover -s tools
"""
import contextlib
import html
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402

# Pages that tag Play with their own source: match shares (m/), QR codes and ads (go/).
OWN_SOURCE = {"m/index.html", "go/index.html"}
# _config.yml keeps these off the site.
UNPUBLISHED = {".git", "tools", "data", "docs", ".superpowers", "README.md", ".gitignore"}
# Not a scheme and not protocol relative, so the browser stays on this site.
LOCAL = r"(?![a-zA-Z][a-zA-Z0-9+.-]*:|//)"
# Every App Store URL on the site starts like this: the host, then the Greek storefront.
GREEK_APP_STORE = "https://apps.apple.com/gr/app/"
# The one exception: go.js picks a storefront per hall slug in this one expression, and
# go_page.test.js pins which slug opens which store.
GO_STORE_BASE = '"https://apps.apple.com/" + storefrontOf(hall) + "/app/"'


def hall(vid, address, city="Larissa", country="GR"):
    return {"id": vid, "name": vid.title(), "city": city, "country": country, "address": address, "sortOrder": 1}


# The app repo's data/countries.json, cut to what --import reads.
COUNTRIES = [{"code": "GR", "fallback": True, "open": True}, {"code": "CY", "open": True},
             {"code": "DE", "open": False}]
# A made-up hall of a closed country, in a city CITIES does not have.
BERLIN = {"id": "venue-de-ber-test", "name": "Test Hall", "city": "Berlin", "country": "DE",
          "address": "Teststrasse 1", "sortOrder": 900}


def app_data(folder, backup, countries=COUNTRIES):
    """The app repo's data/ in small: the backup with countries.json beside it. Returns the backup."""
    Path(folder).mkdir(parents=True, exist_ok=True)
    Path(folder, "countries.json").write_text(json.dumps(countries), encoding="utf-8")
    source = Path(folder, "venues-backup.json")
    source.write_text(json.dumps(backup), encoding="utf-8")
    return source


def imported(backup, countries=COUNTRIES):
    """The data/venues.json text that --import makes of this backup."""
    with tempfile.TemporaryDirectory() as tmp:
        return b.import_backup(app_data(tmp, backup, countries))


def generate(*args):
    """The generator's command line with these arguments: its exit code and what it printed."""
    out = io.StringIO()
    with mock.patch.object(sys, "argv", ["build_directory.py", *args]), contextlib.redirect_stdout(out):
        try:
            b.main()
        except SystemExit as stop:
            return stop.code, out.getvalue()
    return 0, out.getvalue()


def published_files():
    """Every file GitHub Pages serves, as (repo path, file)."""
    for folder, dirs, names in os.walk(b.ROOT):
        if Path(folder) == b.ROOT:
            dirs[:] = [d for d in dirs if d not in UNPUBLISHED]
            names = [n for n in names if n not in UNPUBLISHED]
        for name in sorted(names):
            f = Path(folder, name)
            yield f.relative_to(b.ROOT).as_posix(), f


def published(*suffixes):
    """Every file GitHub Pages serves with one of these suffixes, as (repo path, text)."""
    for rel, f in published_files():
        if f.suffix in suffixes:
            yield rel, f.read_text(encoding="utf-8")


def app_store_urls(text):
    """App Store URLs however they are written: any case, any or no scheme, JSON's \\/ for /."""
    return re.findall(r"""(?i)(?:https?:)?(?://)?(?:apps|itunes)\.apple\.com[^\s"'<>]*""",
                      text.replace("\\/", "/"))


def site_path(rel):
    """index.html is "", mpiliardo/athens/index.html is mpiliardo/athens/, as campaign_for takes them."""
    return re.sub(r"(^|/)index\.html$", r"\1", rel)


def store_hrefs(text, host):
    return [html.unescape(h) for h in re.findall(rf'href="(https://{re.escape(host)}/[^"]*)"', text)]


def rendered_pages():
    return {p.relative_to(b.ROOT).as_posix() for p in b.render() if p.suffix == ".html"}


class BuildDirectoryTest(unittest.TestCase):

    def test_committed_pages_match_the_generator(self):
        for path, text in b.render().items():
            self.assertEqual(path.read_text(encoding="utf-8"), text, f"{path} is stale; run the generator")

    def test_import_keeps_only_public_fields_and_strips_dashes(self):
        backup = [{"id": "v1", "name": "Club — One", "city": "Volos", "address": "Odos 1",
                   "sortOrder": 3, "latitude": 39.3, "longitude": 22.9, "hours": "10-2",
                   "pricePerHourEuros": 6, "amenities": ["bar"], "tables": 8, "phone": ""}]
        (record,) = json.loads(imported(backup))
        # A hall that names no country is in the fallback country, as the app reads it.
        self.assertEqual(record, {"id": "v1", "name": "Club - One", "city": "Volos", "country": "GR",
                                  "address": "Odos 1", "sortOrder": 3})

    def test_import_keeps_each_halls_own_country(self):
        backup = [dict(hall("venue-cy-nic-a", "Odos 1", "Nicosia", "CY"), sortOrder=2), hall("venue-b", "Odos 2")]
        self.assertEqual([(r["id"], r["country"]) for r in json.loads(imported(backup))],
                         [("venue-b", "GR"), ("venue-cy-nic-a", "CY")])

    def test_one_district_among_several_halls_is_not_listed(self):
        halls = [hall("a", "Odos 1"), hall("b", "Odos 2"), hall("c", "Papagou 1A, Giannouli")]
        text = b.city_page("Larissa", halls, {"Larissa": halls}, "el")
        self.assertNotIn("Περιοχ", text)
        self.assertIn('<p class="lead">Λάρισα: 3 αίθουσες μπιλιάρδου στον κατάλογο του RackUp. '
                      'Παρακάτω θα βρεις τα μπιλιάρδα με τις διευθύνσεις τους.</p>', text)

    def test_two_or_more_districts_are_listed(self):
        halls = [hall("a", "Odos 1, Kalamaria"), hall("b", "Odos 2, Pylaia")]
        text = b.city_page("Larissa", halls, {"Larissa": halls}, "el")
        self.assertIn('<p class="lead">Λάρισα: 2 αίθουσες μπιλιάρδου στον κατάλογο του RackUp, σε Kalamaria και '
                      'Pylaia. Παρακάτω θα βρεις τα μπιλιάρδα με τις διευθύνσεις τους.</p>', text)

    def test_no_page_carries_a_map_or_a_coordinate(self):
        for path, text in b.render().items():
            for banned in ("maps.google", "google.com/maps", "latitude", "longitude", '"geo"'):
                self.assertNotIn(banned, text, f"{path} contains {banned}")

    def test_every_play_link_on_the_site_carries_its_page_campaign(self):
        tagged = set()
        for rel, text in published(".html"):
            links = store_hrefs(text, "play.google.com")
            # Structured data names the listing (sameAs) but is never a link anyone taps.
            visible = re.sub(r'<script type="application/ld\+json">.*?</script>', "", text, flags=re.S)
            bare = re.findall(r"https?://play\.google\.com/", visible)
            self.assertEqual(len(bare), len(links), f"{rel} has a Play URL outside an https href")
            for link in links:
                query = parse_qs(urlsplit(link).query)
                self.assertEqual(query.get("id"), ["com.rackup.app"], f"{rel}: {link}")
                self.assertEqual(len(query.get("referrer", [])), 1, f"{rel}: untagged Play link {link}")
                if rel in OWN_SOURCE:
                    continue
                campaign = b.campaign_for(site_path(rel))
                self.assertEqual(query["referrer"][0],
                                 f"utm_source=website&utm_medium=organic&utm_campaign={campaign}", rel)
                tagged.add(rel)
        self.assertEqual(tagged, rendered_pages(), "store links on a page the build does not tag; see HAND_PAGES")

    def test_campaigns_come_from_the_path_and_are_unique_and_valid(self):
        expected = {"": "home", "support.html": "support", "mpiliardo/": "el-directory",
                    "en/billiards/": "en-directory", "mpiliardo/athens/": "el-athens",
                    "en/billiards/athens/": "en-athens", "mpiliardo/agios-nikolaos/": "el-agios-nikolaos",
                    "galliko-mpiliardo/": "el-carom", "en/carom-billiards/": "en-carom"}
        for path, campaign in expected.items():
            self.assertEqual(b.campaign_for(path), campaign, path)
        campaigns = [b.campaign_for(site_path(rel)) for rel in sorted(rendered_pages())]
        self.assertEqual(len(campaigns),
                         2 * len(b.group_by_city(b.load_venues())) + 2 + len(b.CAROM) + len(b.HAND_PAGES))
        self.assertEqual(len(set(campaigns)), len(campaigns), "two pages share a campaign")
        for campaign in campaigns:
            self.assertRegex(campaign, r"^[a-z0-9]+(-[a-z0-9]+)*$")
            self.assertLessEqual(len(f"web-{campaign}"), 30, f"{campaign} is too long for Apple's ct")
        bad = ("mpiliardo/Αθήνα/", "mpiliardo/a_b/", "mpiliardo/athens/x/", "Support.html",
               "en/billiards/" + "x" * 24 + "/")
        for path in bad:
            with self.assertRaises(SystemExit, msg=path):
                b.campaign_for(path)

    def test_app_store_links_stay_plain_until_the_provider_token_exists(self):
        go_js = (b.ROOT / "go" / "go.js").read_text(encoding="utf-8")
        self.assertEqual(b.PROVIDER_TOKEN, re.search(r'var PROVIDER_TOKEN = "([^"]*)";', go_js).group(1),
                         "paste the pt into go/go.js and tools/build_directory.py together")
        self.assertEqual(b.app_store_url("el-athens", ""), b.APP_STORE)
        self.assertEqual(b.app_store_url("el-athens", "12aB34"),
                         "https://apps.apple.com/gr/app/apple-store/id6800614202?pt=12aB34&ct=web-el-athens&mt=8")
        with self.assertRaises(SystemExit):
            b.app_store_url("home", "12aB&ct=x")
        checked = set()
        for rel, text in published(".html"):
            if rel in OWN_SOURCE:
                continue
            for link in store_hrefs(text, "apps.apple.com"):
                self.assertEqual(link, b.app_store_url(b.campaign_for(site_path(rel))), rel)
                checked.add(rel)
        self.assertEqual(checked, rendered_pages())

    def test_every_app_store_url_names_the_greek_storefront(self):
        # Without a storefront the web falls back to the US store and answers 404 on a computer.
        # Every published file counts, not only pages; only go.js may pick another open country's.
        for built in (b.APP_STORE, b.app_store_url("home", ""), b.app_store_url("home", "12aB34")):
            self.assertTrue(built.startswith(GREEK_APP_STORE), f"the build writes {built}")
        seen = set()
        for rel, f in published_files():
            # Images and fonts decode to noise, which holds no URL.
            text = f.read_bytes().decode("utf-8", "replace")
            if rel == "go/go.js":
                text = self.go_store_base_checked(text)
            for found in app_store_urls(text):
                self.assertTrue(found.startswith(GREEK_APP_STORE),
                                f"{rel}: {found} does not start with {GREEK_APP_STORE}")
                seen.add(rel)
        self.assertEqual(seen, rendered_pages() | OWN_SOURCE | {"go/go.js"},
                         "the files with App Store links changed: add the page to HAND_PAGES or to this list")

    def go_store_base_checked(self, text):
        """go.js with its one storefront expression read as Greek, once its storefront map checks out."""
        self.assertEqual(1, text.count(GO_STORE_BASE), "go.js builds every App Store URL in one expression")
        self.assertIn('var DEFAULT_STOREFRONT = "gr";', text, "a slug with no country prefix opens the Greek store")
        stores = re.search(r"var STOREFRONTS = \{([^}]*)\};", text)
        self.assertIsNotNone(stores, "go.js has no STOREFRONTS map")
        for code, store in re.findall(r"""(\w+)\s*:\s*["']([^"']*)["']""", stores.group(1)):
            self.assertRegex(store, r"^[a-z]{2}$", f"slug prefix {code} opens no storefront: {store!r}")
        return text.replace(GO_STORE_BASE, f'"{GREEK_APP_STORE}"')

    def test_the_go_storefront_exception_is_that_one_expression(self):
        good = (f'var STOREFRONTS = {{ cy: "cy" }};\nvar DEFAULT_STOREFRONT = "gr";\n'
                f"var store = {GO_STORE_BASE};\n")
        self.assertNotIn("apps.apple.com/\"", self.go_store_base_checked(good))
        for bad in (good + f"var again = {GO_STORE_BASE};\n",
                    good.replace(GO_STORE_BASE, '"https://apps.apple.com/" + code + "/app/"'),
                    good.replace('DEFAULT_STOREFRONT = "gr"', 'DEFAULT_STOREFRONT = "us"'),
                    good.replace('cy: "cy"', 'cy: ""'),
                    good.replace("var STOREFRONTS = { cy: \"cy\" };\n", "")):
            with self.subTest(bad=bad), self.assertRaises(AssertionError):
                self.go_store_base_checked(bad)

    def test_the_storefront_guard_reads_a_url_however_it_is_written(self):
        escaped = r'{"sameAs":["https:\/\/apps.apple.com\/gr\/app\/id6800614202"]}'
        self.assertEqual(app_store_urls(escaped), ["https://apps.apple.com/gr/app/id6800614202"])
        for bad in (r"https:\/\/apps.apple.com\/app\/id6800614202", "https://Apps.Apple.com/app/id6800614202",
                    "//apps.apple.com/gr/app/id6800614202", "http://itunes.apple.com/gr/app/id6800614202",
                    "apps.apple.com/gr/app/id6800614202", "https%3A%2F%2Fapps.apple.com%2Fgr%2Fapp%2Fid6800614202"):
            (found,) = app_store_urls(f'<a href="{bad}">')
            self.assertFalse(found.startswith(GREEK_APP_STORE), bad)

    def test_english_home_has_its_own_campaign(self):
        self.assertEqual(b.campaign_for("en/"), "en-home")
        self.assertEqual(b.campaign_for(""), "home")

    def test_both_homes_get_counts_and_the_city_grid(self):
        cities = b.group_by_city(b.load_venues())
        total, count = sum(len(h) for h in cities.values()), len(cities)
        files = b.render()
        for home, (lang, root) in {"index.html": ("el", "mpiliardo"), "en/index.html": ("en", "en/billiards")}.items():
            text = files[b.ROOT / home]
            self.assertIn(f'<span data-count="venues">{total}</span>', text, home)
            self.assertIn(f'<span data-count="cities">{count}</span>', text, home)
            grid = re.search(r"<!-- city-grid -->(.*?)<!-- /city-grid -->", text, re.S).group(1)
            hrefs = re.findall(r'<a href="([^"]+)"', grid)
            self.assertEqual(len(hrefs), count, home)
            for href in hrefs:
                page = (b.ROOT / home).parent / href / "index.html"
                self.assertIn(page.resolve(), {p.resolve() for p in files}, f"{home} links {href}")
                self.assertTrue(page.resolve().as_posix().startswith((b.ROOT / root).resolve().as_posix()), href)

    def test_home_without_city_grid_markers_is_refused(self):
        cities = b.group_by_city(b.load_venues())
        with self.assertRaises(SystemExit):
            b.home_with_city_grid("<p>no markers here</p>", cities, "el")

    def test_a_city_page_lists_its_halls_a_to_z_whatever_their_sort_order(self):
        names = ["King 8", "L' Amorti", "athens billiard club", "Ώρα", "Ωμέγα", "Cue Club"]
        venues = [{"id": f"venue-ath-{i}", "name": n, "city": "Athens", "address": "Οδός 1", "sortOrder": i}
                  for i, n in enumerate(names)]
        listed = [v["name"] for v in b.group_by_city(venues)["Athens"]]
        # No case, accents or punctuation, Latin before Greek: the app's order without a position.
        self.assertEqual(listed, ["athens billiard club", "Cue Club", "King 8", "L' Amorti", "Ωμέγα", "Ώρα"])

    def test_summary_names_both_homes(self):
        cities = b.group_by_city(b.load_venues())
        line = b.summary(b.render(), cities)
        self.assertIn(f"for {sum(map(len, cities.values()))} halls in {len(cities)} cities", line)
        self.assertIn("the counts and city grid on both homes", line)
        self.assertNotIn("counts in index.html", line, "the English home gets them too")

    def test_no_page_tracks_visitors_or_loads_from_another_host(self):
        for rel, text in published(".html"):
            for tag in re.findall(r"<script\b[^>]*>", text):
                self.assertRegex(tag, rf'^<script (type="application/ld\+json"|src="{LOCAL}[^"]+" defer)>$', rel)
            for tag in re.findall(r"<link\b[^>]*>", text):
                if not re.search(r'rel="(canonical|alternate)"', tag):
                    self.assertRegex(tag, rf'\shref="{LOCAL}', f"{rel}: {tag}")
            for value in re.findall(r'\s(?:src|srcset|poster|data|action|formaction)="([^"]*)"', text):
                self.assertRegex(value, rf"^{LOCAL}", f"{rel} loads {value}")
            self.assertNotRegex(text, r"(?i)<(iframe|embed|object|frame)\b|\sping=", rel)
        for rel, text in published(".html", ".css"):
            self.assertNotRegex(text, r"""(?i)(url\(|@import)\s*['"]?(https?:)?//""", f"{rel} imports from another host")
        for rel, text in published(".js"):
            for api in (r"document\.cookie", r"localStorage", r"sessionStorage", r"indexedDB", r"sendBeacon",
                        r"\bfetch\(", r"XMLHttpRequest", r"WebSocket", r"new Image\b", r"createElement\("):
                self.assertNotRegex(text, api, f"{rel} uses {api}")
        for rel, text in published(".html", ".js", ".css"):
            for tracker in (r"gtag\(", r"googletagmanager", r"google-analytics\.com", r"fbq\(", r"connect\.facebook\.net",
                            r"plausible\.io", r"matomo", r"hotjar", r"clarity\.ms", r"cloudflareinsights", r"segment\.com"):
                self.assertNotRegex(text, tracker, f"{rel} mentions {tracker}")


class ImportCountryTest(unittest.TestCase):
    """--import lists only the halls of open countries, and writes nothing until the build passes."""

    def setUp(self):
        self.committed = b.DATA.read_text(encoding="utf-8")
        # The committed halls as the app's backup holds them, country included, and one of a closed country.
        self.backup = [dict(v) for v in json.loads(self.committed)] + [dict(BERLIN)]

    def test_a_closed_countrys_halls_are_skipped_and_the_import_runs_clean(self):
        self.assertEqual(imported(self.backup), self.committed)
        with tempfile.TemporaryDirectory() as tmp:
            code, printed = generate("--import", str(app_data(tmp, self.backup)), "--check")
        self.assertEqual((code, printed), (0, ""), "the import would change data/venues.json or a page")

    def test_an_open_countrys_unknown_city_stops_the_import_before_it_writes(self):
        all_open = [dict(c, open=True) for c in COUNTRIES]
        with tempfile.TemporaryDirectory() as tmp:
            site, source = Path(tmp, "site"), app_data(Path(tmp, "app"), self.backup, all_open)
            data = site / "data" / "venues.json"
            data.parent.mkdir(parents=True)
            data.write_text(self.committed, encoding="utf-8")
            # ROOT too, so nothing this run writes can reach the real site.
            with mock.patch.multiple(b, ROOT=site, DATA=data):
                code, _ = generate("--import", str(source))
            self.assertIn("venue-de-ber-test: unknown city 'Berlin'", str(code))
            self.assertIn("venue-de-ber-test: unknown country 'DE'", str(code))
            self.assertEqual(data.read_text(encoding="utf-8"), self.committed, "a stopped import wrote the data")

    def test_a_check_with_an_import_writes_nothing_and_reports_the_data(self):
        self.backup[-2]["sortOrder"] += 1  # changes data/venues.json and no page
        before = b.DATA.read_bytes()
        self.addCleanup(b.DATA.write_bytes, before)
        with tempfile.TemporaryDirectory() as tmp:
            code, printed = generate("--import", str(app_data(tmp, self.backup)), "--check")
        self.assertEqual(b.DATA.read_bytes(), before, "--check wrote data/venues.json")
        self.assertEqual((code, printed), (1, f"out of date: {Path('data', 'venues.json')}\n"))


def graph(text):
    """The nodes of a page's JSON-LD."""
    return json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.S).group(1))["@graph"]


class CountryPagesTest(unittest.TestCase):
    """Each country's halls: their own city pages, a heading on the directory, their country in the data."""

    @staticmethod
    def two_countries():
        """Two Greek cities and two Cypriot ones, as group_by_city returns them. One hall has carom."""
        return b.group_by_city([dict(hall("venue-ath-a", "Odos 1", "Athens"), caromTables=2),
                                hall("venue-ath-b", "Odos 2", "Athens"), hall("venue-lar-a", "Odos 3"),
                                hall("venue-cy-nic-a", "Odos 4", "Nicosia", "CY"),
                                hall("venue-cy-lim-a", "Odos 5", "Limassol", "CY")])

    def test_every_hall_names_a_known_country_and_every_city_has_one(self):
        country_of_city = {}
        for v in b.load_venues():
            self.assertIn(v["country"], b.COUNTRIES, v["id"])
            self.assertEqual(country_of_city.setdefault(v["city"], v["country"]), v["country"], v["id"])

    def test_the_build_refuses_a_hall_with_no_known_country_or_a_city_in_two(self):
        cases = {"venue-x: unknown country None": [hall("venue-x", "Odos 1", country=None)],
                 "venue-x: unknown country 'XX'": [hall("venue-x", "Odos 1", country="XX")],
                 "venue-y: Larissa is in GR on another hall, not in CY": [hall("venue-x", "Odos 1"),
                                                                           hall("venue-y", "Odos 2", country="CY")]}
        for message, venues in cases.items():
            with self.subTest(message), tempfile.TemporaryDirectory() as tmp:
                data = Path(tmp, "venues.json")
                data.write_text(json.dumps(venues), encoding="utf-8")
                with mock.patch.object(b, "DATA", data), self.assertRaises(SystemExit) as stop:
                    b.load_venues()
                self.assertIn(message, str(stop.exception.code))

    def test_structured_data_names_each_halls_own_country(self):
        cyprus = hall("venue-cy-nic-a", "Odos 4", "Nicosia", "CY")
        self.assertEqual(b.business(cyprus)["address"], {"@type": "PostalAddress", "streetAddress": "Odos 4",
                                                         "addressLocality": "Λευκωσία", "addressCountry": "CY"})
        for v in b.load_venues():
            self.assertEqual(b.business(v)["address"]["addressCountry"], v["country"], v["id"])

    def test_the_directory_gives_each_country_a_heading_over_its_cities(self):
        cities = self.two_countries()
        expected = {"el": ("Αίθουσες μπιλιάρδου στην Ελλάδα και στην Κύπρο", "", ("Ελλάδα", "Κύπρος")),
                    "en": ("Billiard halls in Greece and Cyprus", " by city", ("Greece", "Cyprus"))}
        for lang, (h1, by_city, headings) in expected.items():
            text = b.index_page(cities, lang)
            self.assertIn(f"<h1>{h1}</h1>", text)
            self.assertIn(f"<title>{h1}{by_city} | RackUp</title>", text)
            sections = re.findall(r'<section class="country" id="([a-z]{2})">\n<h3>([^<]*)</h3>\n'
                                  r'<ul class="city-grid">\n(.*?)\n</ul>\n</section>', text, re.S)
            self.assertEqual([(code, name) for code, name, _ in sections], [("gr", headings[0]), ("cy", headings[1])])
            grids = [re.findall(r'<a href="([^"]*)/">', grid) for _, _, grid in sections]
            self.assertEqual(grids, [["athens", "larissa"], ["lemesos", "lefkosia"]], lang)
            (listing,) = [n for n in graph(text) if n["@type"] == "ItemList"]
            self.assertEqual([item["url"].rsplit("/", 2)[1] for item in listing["itemListElement"]],
                             grids[0] + grids[1], "the structured list follows the page")
        greece = {city: halls for city, halls in cities.items() if b.country_of(halls) == "GR"}
        alone = b.index_page(greece, "el")
        self.assertNotIn('<section class="country"', alone, "a lone country needs no heading of its own")
        self.assertIn("<title>Αίθουσες μπιλιάρδου στην Ελλάδα ανά πόλη | RackUp</title>", alone)

    def test_other_cities_are_the_pages_own_countrys(self):
        cities = self.two_countries()
        for city, others in {"Athens": ["larissa"], "Nicosia": ["lemesos"]}.items():
            for lang in ("el", "en"):
                text = b.city_page(city, cities[city], cities, lang)
                nav = re.search(r'<nav class="other".*?</nav>', text, re.S).group(0)
                self.assertEqual(re.findall(r'href="\.\./([^/]*)/"', nav), others, f"{city} {lang}")
        alone = b.city_page("Nicosia", cities["Nicosia"], {"Nicosia": cities["Nicosia"]}, "el")
        self.assertNotIn('<nav class="other"', alone, "a country's only city has no other cities to list")
        real = b.group_by_city(b.load_venues())
        for city, halls in real.items():
            mine = {b.CITIES[c][0] for c in real if c != city and b.country_of(real[c]) == b.country_of(halls)}
            nav = re.search(r'<nav class="other".*?</nav>', b.city_page(city, halls, real, "en"), re.S).group(0)
            self.assertEqual(set(re.findall(r'href="\.\./([^/]*)/"', nav)), mine, city)

    def test_homes_name_every_country_the_directory_lists(self):
        cities = b.group_by_city(b.load_venues())
        files = b.render()
        for home in b.HOMES:
            (app,) = [n for n in graph(files[b.ROOT / home]) if n["@type"] == "MobileApplication"]
            self.assertEqual(app["countriesSupported"], list(b.by_country(cities)), home)
        with self.assertRaises(SystemExit):
            b.home_with_countries("<p>no structured data</p>", cities)

    def test_the_sitemap_lists_every_city_page_once_country_by_country(self):
        cities = b.group_by_city(b.load_venues())
        locs = re.findall(r"<loc>([^<]+)</loc>", b.render()[b.ROOT / "sitemap.xml"])
        for city in cities:
            for root in (b.EL_ROOT, b.EN_ROOT):
                self.assertEqual(locs.count(b.url(f"{root}/{b.CITIES[city][0]}/")), 1, f"{root} {city}")
        country_of_slug = {b.CITIES[c][0]: b.country_of(h) for c, h in cities.items()}
        listed = [country_of_slug[loc.rsplit("/", 2)[1]] for loc in locs if loc.startswith(b.url(f"{b.EL_ROOT}/"))
                  and loc != b.url(f"{b.EL_ROOT}/")]
        self.assertEqual(listed, sorted(listed, key=list(b.by_country(cities)).index))

    def test_english_pages_mark_greek_text_and_only_greek_text_as_greek(self):
        latin, greek = hall("venue-a", "Kantaras 12"), hall("venue-b", "Νικολάου Έλληνα 51, Έμπα")
        self.assertIn('<p class="addr">Kantaras 12</p>', b.hall_item(latin, "en"))
        self.assertIn('<p class="addr" lang="el">Νικολάου Έλληνα 51, Έμπα</p>', b.hall_item(greek, "en"))
        self.assertIn('<p class="addr">Νικολάου Έλληνα 51, Έμπα</p>', b.hall_item(greek, "el"))


if __name__ == "__main__":
    unittest.main()
