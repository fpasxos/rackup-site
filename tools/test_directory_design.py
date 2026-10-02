"""The directory pages keep their search signals and hall anchors through the redesign.
Python 3.8+, no packages: python -m unittest discover -s tools
"""
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402

# Frozen from the pre-redesign pages. After a venue import changes a head on purpose, read
# the diff, then refresh it with: python tools/test_directory_design.py --capture
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "directory-head.json"
SOCIAL_CARD = f"{b.BASE_URL}/assets/og-card.png"


def directory_pages():
    """Repo path -> text for every page the generator writes under the two directory roots."""
    roots = tuple(f"{root}/" for root in (b.EL_ROOT, b.EN_ROOT))
    pages = {}
    for path, text in b.render().items():
        rel = path.relative_to(b.ROOT).as_posix()
        if path.suffix == ".html" and rel.startswith(roots):
            pages[rel] = text
    return dict(sorted(pages.items()))


def one(pattern, text, rel):
    found = re.findall(pattern, text)
    if len(found) != 1:
        raise AssertionError(f"{rel}: expected one {pattern!r}, found {len(found)}")
    return found[0]


def head_of(rel, text):
    """The tags search engines and link previews read, verbatim, plus the hall anchors."""
    return {
        "title": one(r"<title>.*?</title>", text, rel),
        "description": one(r'<meta name="description" content="[^"]*">', text, rel),
        "canonical": one(r'<link rel="canonical" href="[^"]*">', text, rel),
        "alternates": re.findall(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">', text),
        "og": re.findall(r'<meta property="og:(?!image")[^"]*" content="[^"]*">', text),
        "jsonld": one(r'<script type="application/ld\+json">(.*?)</script>', text, rel),
        "venues": sorted(re.findall(r'\sid="(venue-[^"]*)"', text)),
    }


def stylesheets(text):
    tags = [t for t in re.findall(r"<link\b[^>]*>", text) if re.search(r'\srel="stylesheet"', t)]
    return [re.search(r'\shref="([^"]*)"', t).group(1) for t in tags]


def capture():
    heads = {rel: head_of(rel, text) for rel, text in directory_pages().items()}
    FIXTURE.parent.mkdir(exist_ok=True)
    FIXTURE.write_text(json.dumps(heads, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"Captured {len(heads)} directory pages into {FIXTURE.relative_to(b.ROOT).as_posix()}")


class DirectoryDesignTest(unittest.TestCase):

    def test_directory_pages_keep_their_seo_and_anchors(self):
        frozen = json.loads(FIXTURE.read_text(encoding="utf-8"))
        pages = directory_pages()
        self.assertEqual(sorted(pages), sorted(frozen), "a directory page appeared or vanished")
        for rel, text in pages.items():
            with self.subTest(page=rel):
                head = head_of(rel, text)
                for field, value in frozen[rel].items():
                    self.assertEqual(head[field], value, f"{rel}: {field} changed")
                self.assertEqual(len(head["alternates"]), 3, rel)
                depth = rel.count("/")
                self.assertEqual(stylesheets(text), [f"{'../' * depth}assets/site.css"],
                                 f"{rel} must link site.css, and only site.css")

    def test_directory_pages_share_the_social_card(self):
        for rel, text in directory_pages().items():
            with self.subTest(page=rel):
                card = SOCIAL_CARD.replace("og-card.png", "og-card-en.png") if rel.startswith("en/") else SOCIAL_CARD
                self.assertIn(f'<meta property="og:image" content="{card}">', text, "English pages preview in English")
                self.assertIn('<meta name="theme-color" content="#0E1512">', text)
                self.assertNotIn("\N{BILLIARDS}", text, "the brand is the CSS 8-ball, not an emoji")


if __name__ == "__main__":
    if sys.argv[1:] == ["--capture"]:
        capture()
    else:
        unittest.main()
