"""Support and privacy in the new design: the policy's words and the pages' anchors survive.
Python 3.8+, no packages: python -m unittest discover -s tools
"""
import html
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402
from test_build_directory import published  # noqa: E402

# origin/master before the redesign: the policy text Apple and Google accepted.
BASELINE = "210b04f"
BILLIARDS_EMOJI = "\U0001F3B1"


def at_baseline(name):
    return subprocess.run(["git", "show", f"{BASELINE}:{name}"], cwd=b.ROOT,
                          capture_output=True, check=True).stdout.decode("utf-8")


def current(name):
    return (b.ROOT / name).read_text(encoding="utf-8")


def main_html(page):
    found = re.search(r"<main\b[^>]*>(.*?)</main>", page, re.S)
    if not found:
        raise AssertionError("page has no <main>")
    return found.group(1)


def visible_text(fragment):
    """Tags out, entities decoded, whitespace collapsed: what a reader of the page sees."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def ids(page):
    return set(re.findall(r'\bid="([^"]+)"', page))


class SupportAndPrivacyTest(unittest.TestCase):

    def test_privacy_text_is_unchanged(self):
        # The restyle moves two things out of <main>, so only they leave the baseline: the old
        # in-page nav (Home, Support), which the shared header replaces, and the decorative
        # billiards emoji in the H1. Every other word must match.
        old = main_html(at_baseline("privacy.html"))
        old = re.sub(r"<nav>.*?</nav>", "", old, count=1, flags=re.S).replace(BILLIARDS_EMOJI, "")
        new = main_html(current("privacy.html"))
        was, now = visible_text(old).split(), visible_text(new).split()
        self.assertIn("Deleting", was, "baseline did not load")
        if now != was:
            at = next((i for i, (x, y) in enumerate(zip(was, now)) if x != y), min(len(was), len(now)))
            near = slice(max(at - 6, 0), at + 6)
            self.fail(f"policy text differs at word {at}: was {' '.join(was[near])!r}, "
                      f"now {' '.join(now[near])!r}")

    def test_support_keeps_its_ids(self):
        missing = ids(at_baseline("support.html")) - ids(current("support.html"))
        self.assertEqual(missing, set(), "support.html lost anchors other sites may link to")

    def test_privacy_keeps_its_ids(self):
        # support.html links privacy.html#delete, so the policy's anchors are pinned too.
        old = ids(at_baseline("privacy.html"))
        self.assertIn("delete", old)
        self.assertEqual(old - ids(current("privacy.html")), set())

    def test_no_inline_style_blocks(self):
        offenders = [path for path, text in published(".html") if re.search(r"<style\b", text, re.I)]
        self.assertEqual(offenders, [], "site.css is the only stylesheet")


if __name__ == "__main__":
    unittest.main()
