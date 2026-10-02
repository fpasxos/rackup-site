"""Tests for tools/build_directory.py. Python 3.8+, no packages:
python -m unittest discover -s tools
"""
import html
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402

# Pages that tag Play with their own source: match shares (m/), QR codes and ads (go/).
OWN_SOURCE = {"m/index.html", "go/index.html"}
# _config.yml keeps these off the site.
UNPUBLISHED = {".git", "tools", "data", "docs", ".superpowers"}
# Not a scheme and not protocol relative, so the browser stays on this site.
LOCAL = r"(?![a-zA-Z][a-zA-Z0-9+.-]*:|//)"


def hall(vid, address, city="Larissa"):
    return {"id": vid, "name": vid.title(), "city": city, "address": address, "sortOrder": 1}


def published(*suffixes):
    """Every file GitHub Pages serves with one of these suffixes, as (repo path, text)."""
    for folder, dirs, names in os.walk(b.ROOT):
        if Path(folder) == b.ROOT:
            dirs[:] = [d for d in dirs if d not in UNPUBLISHED]
        for name in sorted(names):
            if Path(name).suffix in suffixes:
                f = Path(folder, name)
                yield f.relative_to(b.ROOT).as_posix(), f.read_text(encoding="utf-8")


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
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp, "venues-backup.json")
            source.write_text(json.dumps(backup), encoding="utf-8")
            (record,) = json.loads(b.import_backup(source))
        self.assertEqual(record, {"id": "v1", "name": "Club - One", "city": "Volos",
                                  "address": "Odos 1", "sortOrder": 3})

    def test_one_district_among_several_halls_is_not_listed(self):
        halls = [hall("a", "Odos 1"), hall("b", "Odos 2"), hall("c", "Papagou 1A, Giannouli")]
        text = b.city_page("Larissa", halls, {"Larissa": halls}, "el")
        self.assertNotIn("Περιοχ", text)
        self.assertIn('<p class="lead">3 αίθουσες μπιλιάρδου στη Λάρισα.</p>', text)

    def test_two_or_more_districts_are_listed(self):
        halls = [hall("a", "Odos 1, Kalamaria"), hall("b", "Odos 2, Pylaia")]
        text = b.city_page("Larissa", halls, {"Larissa": halls}, "el")
        self.assertIn('<p class="lead">2 αίθουσες μπιλιάρδου στη Λάρισα. Περιοχές: Kalamaria, Pylaia.</p>', text)

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
                    "en/billiards/athens/": "en-athens", "mpiliardo/agios-nikolaos/": "el-agios-nikolaos"}
        for path, campaign in expected.items():
            self.assertEqual(b.campaign_for(path), campaign, path)
        campaigns = [b.campaign_for(site_path(rel)) for rel in sorted(rendered_pages())]
        self.assertEqual(len(campaigns), 2 * len(b.group_by_city(b.load_venues())) + 2 + len(b.HAND_PAGES))
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
                         "https://apps.apple.com/app/apple-store/id6800614202?pt=12aB34&ct=web-el-athens&mt=8")
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


if __name__ == "__main__":
    unittest.main()
