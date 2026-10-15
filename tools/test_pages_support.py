"""Support and privacy in the new design: the policy's words and the pages' anchors survive.
Python 3.8+, no packages: python -m unittest discover -s tools
"""
import html
import json
import re
import sys
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402
from test_build_directory import published  # noqa: E402

# Frozen from 210b04f, the policy Apple and Google accepted, so a shallow clone runs these too.
# After a deliberate policy change, refresh the text: python tools/test_pages_support.py --capture
FIXTURES = Path(__file__).resolve().parent / "fixtures"
POLICY_TEXT = FIXTURES / "privacy-text.txt"
PAGE_IDS = FIXTURES / "support-privacy-ids.json"
GREEK_JUMP = '<p lang="el"><a href="#el">Στα Ελληνικά</a></p>'


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


def policy_words(page):
    """The policy's words; the jump link to the Greek summary is navigation, not policy."""
    return visible_text(main_html(page).replace(GREEK_JUMP, "", 1)).split()


def frozen_ids(name):
    return set(json.loads(PAGE_IDS.read_text(encoding="utf-8"))[name])


def capture():
    text = textwrap.fill(" ".join(policy_words(current("privacy.html"))), width=100,
                         break_long_words=False, break_on_hyphens=False)
    with open(POLICY_TEXT, "w", encoding="utf-8", newline="\n") as out:
        out.write(text + "\n")
    print(f"Captured the policy text into {POLICY_TEXT.relative_to(b.ROOT).as_posix()}")


class SupportAndPrivacyTest(unittest.TestCase):

    def test_privacy_text_is_unchanged(self):
        # Every word of the policy must match the frozen text; only navigation may change around it.
        was = POLICY_TEXT.read_text(encoding="utf-8").split()
        now = policy_words(current("privacy.html"))
        self.assertIn("Deleting", was, "baseline did not load")
        if now != was:
            at = next((i for i, (x, y) in enumerate(zip(was, now)) if x != y), min(len(was), len(now)))
            near = slice(max(at - 6, 0), at + 6)
            self.fail(f"policy text differs at word {at}: was {' '.join(was[near])!r}, "
                      f"now {' '.join(now[near])!r}")

    def test_support_keeps_its_ids(self):
        missing = frozen_ids("support.html") - ids(current("support.html"))
        self.assertEqual(missing, set(), "support.html lost anchors other sites may link to")

    def test_privacy_keeps_its_ids(self):
        # support.html links privacy.html#delete, so the policy's anchors are pinned too.
        old = frozen_ids("privacy.html")
        self.assertIn("delete", old)
        self.assertEqual(old - ids(current("privacy.html")), set())

    def test_no_inline_style_blocks(self):
        offenders = [path for path, text in published(".html") if re.search(r"<style\b", text, re.I)]
        self.assertEqual(offenders, [], "site.css is the only stylesheet")


MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December")


def as_date(text):
    """The calendar date in "16 October 2026", or None for a placeholder or an impossible day."""
    import datetime
    parts = (text or "").split()
    if len(parts) != 3 or not parts[0].isdigit() or parts[1] not in MONTHS or not parts[2].isdigit():
        return None
    try:
        return datetime.date(int(parts[2]), MONTHS.index(parts[1]) + 1, int(parts[0]))
    except ValueError:
        return None


def is_real_date(text):
    return as_date(text) is not None


def policy_dates(page):
    """The effective date, the newest change note's date and "This version, dated"."""
    text = visible_text(main_html(page))
    effective = re.search(r"Effective date: (.+?) ·", text)
    newest = re.search(r"What changed on (.+?)\.", text)
    this_version = re.search(r"This version, dated (.+?),", text)
    return [m.group(1) if m else None for m in (effective, newest, this_version)]


def superseded_date(page):
    """The date of the version this one supersedes, or None when it replaces one of the same day."""
    found = re.search(r"This version, dated .+?, .*?supersedes the version dated (.+?),",
                      visible_text(main_html(page)))
    return found.group(1) if found else None


def placeholders(page):
    return re.findall(r"\b[A-Z]{2} (?:%s) \d{4}" % "|".join(MONTHS), visible_text(main_html(page)))


class PolicyDateTest(unittest.TestCase):

    def test_the_policy_carries_one_real_date(self):
        # Merging publishes: a draft's placeholder date must be set to the merge day first.
        page = current("privacy.html")
        self.assertEqual([], placeholders(page), "set every placeholder date")
        dates = policy_dates(page)
        self.assertTrue(all(is_real_date(d) for d in dates), f"set the policy date: {dates}")
        self.assertEqual(len(set(dates)), 1, f"the three dates differ: {dates}")
        older = superseded_date(page)
        if older is not None:
            self.assertTrue(is_real_date(older), f"the superseded date is not a date: {older}")
            self.assertGreater(as_date(dates[0]), as_date(older), "the new version predates the old")

    def test_the_date_check_rejects_a_placeholder(self):
        self.assertFalse(is_real_date("XX October 2026"))
        self.assertFalse(is_real_date("31 February 2026"))
        self.assertTrue(is_real_date("16 October 2026"))
        page = ('<main><p>Effective date: 9 May 2027 · x</p><p>What changed on 9 May 2027. y</p>'
                '<p>This version, dated 9 May 2027, adds a, and supersedes the version dated '
                '7 October 2026, which b. Earlier: XX October 2026.</p></main>')
        self.assertEqual(["9 May 2027"] * 3, policy_dates(page))
        self.assertEqual("7 October 2026", superseded_date(page))
        self.assertEqual(["XX October 2026"], placeholders(page))


if __name__ == "__main__":
    if sys.argv[1:] == ["--capture"]:
        capture()
    else:
        unittest.main()
