"""security.txt (RFC 9116) at /.well-known/ and the security page its Policy names.
Python 3.8+, no packages: python -m unittest discover -s tools
"""
import codecs
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402
from test_build_directory import published  # noqa: E402

SECURITY_TXT = b.ROOT / ".well-known" / "security.txt"
PAGE = b.ROOT / "security.html"
# RFC 9116's fields and the registered CSAF one, as rackup's .github/scripts/security_docs.py has them.
FIELDS = {"acknowledgments", "canonical", "contact", "encryption", "expires", "hiring", "policy",
          "preferred-languages", "csaf"}
RFC3339_UTC = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z"


def fields(text):
    """[(lower-case name, value)], comments and blank lines skipped."""
    found = []
    for line in text.splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            name, _, value = line.partition(":")
            found.append((name.strip().lower(), value.strip()))
    return found


def expires_at(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


class SecurityTxtTest(unittest.TestCase):

    def setUp(self):
        self.raw = SECURITY_TXT.read_bytes()
        self.fields = fields(self.raw.decode("utf-8"))
        self.named = dict(self.fields)

    def test_jekyll_publishes_the_well_known_folder(self):
        # Jekyll drops folders that start with a dot unless _config.yml includes them.
        config = (b.ROOT / "_config.yml").read_text(encoding="utf-8")
        self.assertRegex(config, r'(?m)^include:\s*\[\s*"\.well-known"\s*\]\s*$')
        self.assertIn(".well-known/security.txt", {rel for rel, _ in published(".txt")})

    def test_the_file_has_the_rfc_9116_fields_and_no_others(self):
        names = [n for n, _ in self.fields]
        self.assertEqual([], [n for n in names if n not in FIELDS], "a field RFC 9116 does not define")
        self.assertEqual(names.count("expires"), 1, "Expires must appear exactly once")
        self.assertLessEqual(names.count("preferred-languages"), 1)
        self.assertFalse(self.raw.startswith(codecs.BOM_UTF8), "no byte order mark")
        self.raw.decode("ascii")

    def test_contact_is_the_sites_own_address(self):
        contacts = [v for n, v in self.fields if n == "contact"]
        self.assertEqual(contacts[-1], f"mailto:{b.EMAIL}", "the support mailbox stays the last Contact")
        for value in contacts:
            self.assertRegex(value, r"^(mailto:|https://|tel:)")

    def test_canonical_and_policy_are_this_site(self):
        self.assertEqual(self.named["canonical"], "https://getrackup.com/.well-known/security.txt")
        self.assertEqual(self.named["policy"], "https://getrackup.com/security")
        self.assertTrue(PAGE.is_file(), "GitHub Pages serves /security from security.html")
        self.assertEqual(self.named["preferred-languages"], "en, el")

    def test_it_has_not_expired_and_ends_within_a_year(self):
        # RFC 9116 asks for under a year; renew about six months ahead (rackup's weekly watch warns).
        self.assertRegex(self.named["expires"], f"^{RFC3339_UTC}$")
        left = expires_at(self.named["expires"]) - dt.datetime.now(dt.timezone.utc)
        self.assertGreater(left, dt.timedelta(0), "security.txt has expired: set Expires about six months ahead")
        self.assertLess(left, dt.timedelta(days=366), "Expires should be less than a year away")


class SecurityPageTest(unittest.TestCase):

    def test_the_page_gives_the_same_contact_in_both_languages(self):
        text = PAGE.read_text(encoding="utf-8")
        self.assertIn(f'<a href="mailto:{b.EMAIL}?subject=Security">{b.EMAIL}</a>', text)
        self.assertIn('<a href=".well-known/security.txt">security.txt</a>', text)
        english, greek = text.split('<h2 id="el">', 1)
        for said in ("How to report", "What happens next", "Scope", "Safe harbour", "Supported versions",
                     "Critical 7", "There is no bug bounty."):
            self.assertIn(said, english)
        for said in ("Πώς να μας την αναφέρεις.", "Τι γίνεται μετά.", "Τι καλύπτει.", "Έρευνα καλής πίστης.",
                     "μέσα σε 7 ημέρες για μια κρίσιμη", f"mailto:{b.EMAIL}?subject=Security"):
            self.assertIn(said, greek)

    def test_support_links_the_page_in_both_languages(self):
        text = (b.ROOT / "support.html").read_text(encoding="utf-8")
        self.assertIn('href="security.html"', text)
        self.assertIn('href="security.html#el"', text)


if __name__ == "__main__":
    unittest.main()
