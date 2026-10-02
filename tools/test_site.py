"""Site-wide guards for the Felt and Neon design. Python 3.8+, no packages:
python -m unittest discover -s tools
"""
import json
import re
from html.parser import HTMLParser
import sys
import unittest
from pathlib import Path
from urllib.parse import urljoin, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402
from test_build_directory import published, site_path  # noqa: E402

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


def style_rules(text):
    """(enclosing at-rules, selector, declarations) for every style rule, in source order."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    rules, opened, start = [], [], 0
    for brace in re.finditer(r"[{}]", text):
        if brace.group() == "{":
            opened.append(" ".join(text[start:brace.start()].split()))
        else:
            prelude = opened.pop()
            if not prelude.startswith("@"):
                rules.append((tuple(opened), prelude, text[start:brace.start()]))
        start = brace.end()
    return rules


PLAIN_GLYPH = r"""^("[^"]+"|'[^']+')$"""
SILENT_GLYPH = r"""^("[^"]+"|'[^']+')\s*/\s*(""|'')$"""
HOVER_MEDIA = r"@media\s*\(\s*hover\s*:\s*hover\s*\)"


class StylesheetTest(unittest.TestCase):

    def test_glyphs_drawn_in_css_have_empty_alt_text(self):
        # Screen readers announce a pseudo-element's glyph unless content gives it alt text: "x" / "".
        values = {}
        for _, selectors, body in style_rules(css()):
            content = [v.strip() for v in re.findall(r"(?:^|;)\s*content\s*:\s*([^;]+)", body)]
            for selector in (" ".join(s.split()) for s in selectors.split(",")):
                if content and re.search(r"::?(before|after)$", selector):
                    values.setdefault(selector, []).append(content)
        glyphs = {sel: rules for sel, rules in values.items()
                  if any(re.match(r"""^("[^"]|'[^'])""", v) for rule in rules for v in rule)}
        self.assertLessEqual({".trust li::before", ".faq summary::after"}, set(glyphs), "the walk found no glyphs")
        for selector, rules in glyphs.items():
            last = rules[-1]
            self.assertRegex(last[-1], SILENT_GLYPH, f"{selector}: screen readers read the glyph aloud")
            self.assertRegex(last[0], PLAIN_GLYPH, f"{selector}: browsers without alt text need the plain glyph first")

    def test_hover_styles_apply_only_where_a_pointer_hovers(self):
        # A tap on iOS leaves :hover on until the next tap, so a card or button would stay lifted.
        hovers = [(at, selector) for at, selector, _ in style_rules(css()) if ":hover" in selector]
        self.assertGreater(len(hovers), 0, "the walk found no hover rules")
        for at, selector in hovers:
            self.assertTrue(any(re.fullmatch(HOVER_MEDIA, rule) for rule in at),
                            f"{selector} is outside @media (hover:hover) and sticks on phones")

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

    def test_muted_text_stays_muted_inside_prose(self):
        self.assertRegex(css(), r"\.prose \.muted\s*{[^}]*color\s*:\s*var\(--muted\)")

    def test_latin_faces_cover_arrows(self):
        for face in font_faces(css()):
            if "-latin.woff2" in face:
                self.assertIn("U+2190-2193", face.replace(" ", ""), "Profile → Settings needs the arrow")

    def test_phone_tap_targets_and_wrapping(self):
        text = css()
        for selector in (r"\.nav-links a", r"\.btn-sm", r"\.foot nav a", r"\.other \.chip", r"\.wordmark"):
            self.assertRegex(text, selector + r"\s*{[^}]*min-height\s*:\s*44px", f"{selector} is under 44 px to tap")
        self.assertRegex(text, r"\.prose code,\s*\.prose a\s*{[^}]*overflow-wrap\s*:\s*anywhere", "long code runs off a zoomed phone")
        self.assertRegex(text, r"@media \(max-width:479px\)\s*{\s*\.city-grid\s*{[^}]*repeat\(2", "27 cities in one column on a phone")

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


def depth_prefix(rel):
    return "../" * rel.count("/")


def resolves(rel, ref):
    target = ref.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return True
    base = b.ROOT if target.startswith("/") else (b.ROOT / rel).parent
    path = (base / target.lstrip("/")).resolve()
    return path.is_file() or (path / "index.html").is_file()


class SiteWideTest(unittest.TestCase):

    def test_one_stylesheet_everywhere(self):
        for rel, text in published(".html"):
            sheets = re.findall(r'<link rel="stylesheet" href="([^"]+)">', text)
            want = "/assets/site.css" if rel == "404.html" else depth_prefix(rel) + "assets/site.css"
            self.assertEqual(sheets, [want], rel)

    def test_old_palette_is_gone(self):
        for rel, text in published(".html", ".css", ".js"):
            for colour in OLD_PALETTE:
                self.assertNotIn(colour.lower(), text.lower(), f"{rel} still uses {colour}")

    def test_internal_links_resolve(self):
        for rel, text in published(".html"):
            for ref in re.findall(r'\s(?:href|src)="([^"]+)"', text):
                if re.match(r"(?i)[a-z][a-z0-9+.-]*:|//", ref):
                    continue
                self.assertTrue(resolves(rel, ref), f"{rel} links to missing {ref}")
            for srcset in re.findall(r'\ssrcset="([^"]+)"', text):
                for ref in (part.split()[0] for part in srcset.split(",")):
                    self.assertTrue(resolves(rel, ref), f"{rel} srcset names missing {ref}")

    def test_every_page_has_the_shared_header_and_footer(self):
        for rel, text in published(".html"):
            self.assertIn('<header class="site-header">', text, rel)
            self.assertIn('<footer class="site-footer">', text, rel)
            self.assertIn('<main id="main"', text, rel)
            self.assertIn('class="skip-link" href="#main"', text, rel)

    def test_header_and_footer_are_the_same_on_every_page_of_a_language(self):
        homes = {lang: home for home, lang in b.HOMES.items()}
        pages = dict(published(".html"))
        for rel, text in pages.items():
            lang = re.search(r'<html lang="([^"]+)">', text).group(1)
            for part in ("header", "footer"):
                with self.subTest(page=rel, part=part):
                    mine, home = chrome(rel, text, part), chrome(homes[lang], pages[homes[lang]], part)
                    if mine != home:
                        at = next((i for i, (x, y) in enumerate(zip(mine, home)) if x != y), min(len(mine), len(home)))
                        self.fail(f"{rel}: the {part} drifted from {homes[lang]}: "
                                  f"{mine[max(at - 2, 0):at + 1]} where the home has {home[max(at - 2, 0):at + 1]}")


def chrome_href(page_url, href, classes):
    """The site path a header or footer link opens, so ../support.html and /support.html compare equal."""
    if "lang" in classes.split():
        return "(this page in the other language)"
    target = urlsplit(urljoin(page_url, href))
    # The download pill opens this page's own store block, or the home's when the page has none.
    return "#download" if target.fragment == "download" else target.geturl()


class Chrome(HTMLParser):
    """Tags, attributes and text of a header or footer, with every href resolved."""

    def __init__(self, page_url):
        super().__init__(convert_charrefs=True)
        self.page_url, self.items = page_url, []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "href" in attrs:
            attrs["href"] = chrome_href(self.page_url, attrs["href"], attrs.get("class") or "")
        self.items.append((tag, sorted(attrs.items())))

    def handle_endtag(self, tag):
        self.items.append(("/" + tag,))

    def handle_data(self, data):
        if data.strip():
            self.items.append(" ".join(data.split()))


def chrome(rel, text, part):
    found = re.findall(rf'<{part} class="site-{part}">.*?</{part}>', text, re.S)
    if len(found) != 1:
        raise AssertionError(f"{rel}: expected one site {part}, found {len(found)}")
    parser = Chrome(f"{b.BASE_URL}/{site_path(rel)}")
    parser.feed(found[0])
    parser.close()
    return parser.items


GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class GreekOutsideGreek(HTMLParser):
    """Collects visible Greek text whose nearest lang is not el."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.found, self.skip = [("root", "")], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("head", "script", "style"):
            self.skip += 1
        if tag not in VOID:
            self.stack.append((tag, dict(attrs).get("lang", self.stack[-1][1])))

    def handle_endtag(self, tag):
        if tag in ("head", "script", "style"):
            self.skip -= 1
        while len(self.stack) > 1:
            if self.stack.pop()[0] == tag:
                break

    def handle_data(self, data):
        if not self.skip and GREEK.search(data) and self.stack[-1][1] != "el":
            self.found.append(data.strip()[:40])


class MeaningTest(unittest.TestCase):

    def test_download_button_stays_on_pages_that_have_store_links(self):
        for rel, text in published(".html"):
            pill = re.search(r'<a class="btn btn-primary btn-sm" href="([^"]+)">', text).group(1)
            if "play.google.com" not in text:
                self.assertTrue(pill.endswith("#download"), rel)
                continue
            self.assertEqual(pill, "#download", f"{rel}: installs from this page would count as the home's")
            after = text.split('id="download"', 1)
            self.assertEqual(len(after), 2, f"{rel} has no #download block")
            self.assertIn("play.google.com", after[1][:6000], f"{rel}: #download holds no store link")

    def test_greek_help_links_land_on_the_greek_section(self):
        for page in ("support.html", "privacy.html"):
            text = (b.ROOT / page).read_text(encoding="utf-8")
            self.assertIn('id="el"', text, page)
            self.assertIn('<a class="lang" href="#el"', text, f"{page}: ΕΛ should jump to the Greek section")
            self.assertIn('<a href="#el">Στα Ελληνικά</a>', text, page)
        for rel, text in published(".html"):
            if '<html lang="el">' not in text:
                continue
            for href in re.findall(r'href="([^"]*(?:support|privacy)\.html[^"]*)"', text):
                self.assertTrue(href.endswith("#el"), f"{rel}: {href} opens the English text")

    def test_greek_text_inside_english_pages_is_marked_greek(self):
        for rel, text in published(".html"):
            if '<html lang="en">' not in text:
                continue
            parser = GreekOutsideGreek()
            parser.feed(text)
            self.assertEqual(parser.found, [], f"{rel}: Greek read with an English voice")


def ld_nodes(text):
    nodes = []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
        data = json.loads(block)
        nodes += data.get("@graph", [data])
    return nodes


class SearchTest(unittest.TestCase):

    def test_robots_txt_allows_crawling_and_names_the_sitemap(self):
        text = (b.ROOT / "robots.txt").read_text(encoding="utf-8")
        self.assertIn("Sitemap: https://getrackup.com/sitemap.xml", text)
        self.assertNotRegex(text, r"(?m)^Disallow:\s*/\s*$", "the whole site would be hidden")

    def test_every_indexable_page_has_a_canonical_and_a_description(self):
        for rel, text in published(".html"):
            if 'content="noindex"' in text:
                continue
            self.assertRegex(text, r'<link rel="canonical" href="https://getrackup\.com/[^"]*">', rel)
            description = re.search(r'<meta name="description" content="([^"]+)">', text)
            self.assertIsNotNone(description, f"{rel} has no meta description")

    def test_homes_lead_with_the_search_words(self):
        for page, word in (("index.html", "μπιλιάρδο"), ("en/index.html", "billiards")):
            text = (b.ROOT / page).read_text(encoding="utf-8")
            self.assertIn(word, re.search(r"<h1>(.*?)</h1>", text, re.S).group(1), page)
            title = re.search(r"<title>(.*?)</title>", text).group(1)
            self.assertIn(word, title, page)
            self.assertTrue(title.endswith("| RackUp"), f"{page}: brand goes last")
            self.assertLessEqual(len(title), 60, page)

    def test_root_names_the_brand_the_site_and_the_app(self):
        nodes = {n["@type"]: n for n in ld_nodes((b.ROOT / "index.html").read_text(encoding="utf-8"))}
        self.assertEqual(nodes["Organization"]["@id"], "https://getrackup.com/#org")
        self.assertEqual(nodes["WebSite"]["url"], "https://getrackup.com/")
        self.assertEqual(nodes["MobileApplication"]["@id"], "https://getrackup.com/#app")
        en = {n["@type"]: n for n in ld_nodes((b.ROOT / "en/index.html").read_text(encoding="utf-8"))}
        self.assertEqual(en["MobileApplication"]["@id"], "https://getrackup.com/#app", "one app, not two")

if __name__ == "__main__":
    unittest.main()
