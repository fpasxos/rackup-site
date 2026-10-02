"""The IndexNow key file and tools/indexnow.py, without touching the network.
Python 3.8+, no packages: python -m unittest discover -s tools
"""
import contextlib
import io
import json
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402
import indexnow  # noqa: E402

# A literal, so a typo in the tool or a renamed key file fails here.
KEY = "0a9442a5613cbbd088b30f789f206e74"
KEY_FILE = b.ROOT / f"{KEY}.txt"


def sitemap_locs():
    return re.findall(r"<loc>([^<]+)</loc>", (b.ROOT / "sitemap.xml").read_text(encoding="utf-8"))


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = indexnow.main(list(argv))
    return code, out.getvalue()


class KeyFileTest(unittest.TestCase):

    def test_key_file_at_the_root_holds_exactly_the_key(self):
        self.assertTrue(KEY_FILE.is_file(), f"{KEY_FILE.name} is missing from the repo root")
        # No newline at all, so a CRLF checkout cannot change what the site serves.
        self.assertEqual(KEY_FILE.read_bytes(), KEY.encode("ascii"))
        self.assertEqual(indexnow.KEY, KEY)
        self.assertRegex(KEY, r"^[a-zA-Z0-9-]{8,128}$", "IndexNow's key format")

    def test_github_pages_publishes_the_key_file(self):
        config = (b.ROOT / "_config.yml").read_text(encoding="utf-8")
        excluded = [line.strip()[2:].strip() for line in config.splitlines() if line.strip().startswith("- ")]
        self.assertNotIn(KEY_FILE.name, excluded)
        self.assertFalse(KEY_FILE.name.startswith(("_", ".", "#", "~")), "Jekyll skips such names")


class PayloadTest(unittest.TestCase):

    def test_payload_lists_every_sitemap_url(self):
        body = indexnow.payload(indexnow.sitemap_urls())
        self.assertEqual(body["host"], "getrackup.com")
        self.assertEqual(body["key"], KEY)
        self.assertEqual(body["keyLocation"], f"https://getrackup.com/{KEY}.txt")
        self.assertEqual(body["urlList"], sitemap_locs())
        self.assertGreater(len(body["urlList"]), 6, "the directory pages are missing")
        for link in body["urlList"]:
            self.assertTrue(link.startswith("https://getrackup.com/"), link)

    def test_request_is_a_json_post_to_indexnow(self):
        body = indexnow.payload(["https://getrackup.com/"])
        request = indexnow.request_for(body)
        self.assertEqual(request.full_url, "https://api.indexnow.org/indexnow")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/json; charset=utf-8")
        self.assertEqual(json.loads(request.data.decode("utf-8")), body)

    def test_default_is_a_dry_run(self):
        with mock.patch.object(indexnow, "send", side_effect=AssertionError("a dry run sent")):
            code, out = run()
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out[out.index("{"):]), indexnow.payload(sitemap_locs()))

    def test_urls_given_as_arguments_replace_the_sitemap(self):
        with mock.patch.object(indexnow, "send", side_effect=AssertionError("a dry run sent")):
            _, out = run("https://getrackup.com/mpiliardo/athens/")
        self.assertEqual(json.loads(out[out.index("{"):])["urlList"], ["https://getrackup.com/mpiliardo/athens/"])

    def test_urls_on_another_host_are_refused(self):
        for link in ("https://example.com/", "http://getrackup.com/", "https://getrackup.com.evil/"):
            with self.subTest(link=link), self.assertRaises(SystemExit):
                run(link)

    def test_send_posts_the_payload_and_reports_the_status(self):
        with mock.patch.object(indexnow, "send", return_value=202) as send:
            code, out = run("--send")
        send.assert_called_once_with(indexnow.payload(sitemap_locs()))
        self.assertEqual(code, 0)
        self.assertIn("202", out)
        with mock.patch.object(indexnow, "send", return_value=403):
            code, out = run("--send")
        self.assertEqual(code, 1, "a refused key must fail the command")
        self.assertIn("403", out)


if __name__ == "__main__":
    unittest.main()
