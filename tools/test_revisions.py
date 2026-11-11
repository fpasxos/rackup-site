"""Revision dates: each directory page's <lastmod> and visible date is the day its listing last changed.
Python 3.8+, no packages: python -m unittest discover -s tools
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402
from test_build_directory import app_data, generate  # noqa: E402

# Later than any real revision, so a city dated after this test was written never beats it.
DAY = "2999-12-31"


def committed():
    """The committed halls, each a fresh copy, as the app's backup holds them."""
    return [dict(v) for v in json.loads(b.DATA.read_text(encoding="utf-8"))]


def cities_of(venues):
    return b.group_by_city(venues)


def lastmods():
    """Sitemap URL -> its <lastmod>, or None."""
    text = b.render()[b.ROOT / "sitemap.xml"]
    return {loc: day or None for loc, day in
            re.findall(r"<url><loc>([^<]+)</loc>(?:<lastmod>([^<]+)</lastmod>)?</url>", text)}


def no_carom_hall_with_a_phone():
    """A hall whose change touches its own city page only: it has a phone and no carom."""
    return next(v for v in committed() if v.get("phone") and not b.offers_carom(v))


class SitemapDateTest(unittest.TestCase):

    def test_directory_pages_carry_their_listings_date_and_hand_pages_none(self):
        dates, found = b.load_dates(cities_of(b.load_venues())), lastmods()
        expected = {b.url(p): None for p in ("", "en/", "support.html", "privacy.html", "press/")}
        for root in (b.EL_ROOT, b.EN_ROOT):
            expected[b.url(f"{root}/")] = dates["directory"]
            for city, day in dates["cities"].items():
                expected[b.url(f"{root}/{b.CITIES[city][0]}/")] = day
            for code, day in dates["hubs"].items():
                expected[b.url(f"{root}/{b.HUBS[code]}/")] = day
        for lang in ("el", "en"):
            expected[b.url(f"{b.CAROM[lang]}/")] = dates["carom"]
        self.assertEqual(found, expected)

    def test_every_page_shows_its_sitemap_date_in_its_own_language(self):
        found, checked = lastmods(), 0
        for path, text in b.render().items():
            rel = path.relative_to(b.ROOT).as_posix()
            loc = b.url(re.sub(r"index\.html$", "", rel))
            if path.suffix != ".html" or not found.get(loc):
                continue
            day = datetime.date.fromisoformat(found[loc])
            lang = "en" if rel.startswith("en/") else "el"
            label = "Τελευταία ενημέρωση" if lang == "el" else "Last updated"
            month = b.MONTHS[lang][day.month - 1]
            shown = f'{label}: <time datetime="{found[loc]}">{day.day} {month} {day.year}</time>. '
            self.assertEqual(text.count("<time "), 1, rel)
            self.assertIn(f'<p class="note">{shown}', text, rel)
            checked += 1
        # Per language: the index, the carom page, every city page and every country hub.
        cities = cities_of(b.load_venues())
        self.assertEqual(checked, 2 * (2 + len(cities) + len(b.hubs_of(cities))))

    def test_the_build_reads_no_clock(self):
        # Only fromisoformat is left on datetime.date: a call to today() or now() would fail the build.
        expected = b.render()
        stub = types.SimpleNamespace(date=types.SimpleNamespace(fromisoformat=datetime.date.fromisoformat))
        with mock.patch.object(b, "datetime", stub):
            self.assertEqual(b.render(), expected)

    def test_greek_months_are_genitive(self):
        self.assertIn('<time datetime="2026-05-03">3 Μαΐου 2026</time>', b.updated("2026-05-03", "el"))
        self.assertIn('<time datetime="2026-11-30">30 November 2026</time>', b.updated("2026-11-30", "en"))
        self.assertEqual(b.updated(None, "el"), "")


class ReviseTest(unittest.TestCase):
    """revise() moves the date of exactly the pages whose listing an import changes."""

    def setUp(self):
        self.venues = committed()
        self.dates = b.load_dates(cities_of(self.venues))

    def revised(self, venues, day=lambda: DAY):
        return b.revise(cities_of(self.venues), cities_of(venues), self.dates, day)

    def moved(self, after):
        """The units whose date differs from the committed one."""
        moved = [k for k in ("directory", "carom") if after[k] != self.dates[k]]
        moved += [c for c, d in after["cities"].items() if self.dates["cities"].get(c) != d]
        moved += [f"{c} hub" for c, d in after["hubs"].items() if self.dates["hubs"].get(c) != d]
        return sorted(moved)

    def test_a_new_phone_dates_its_city_only(self):
        hall = no_carom_hall_with_a_phone()
        venues = [dict(v, phone="+30 210 000 0000") if v["id"] == hall["id"] else v for v in self.venues]
        after = self.revised(venues)
        self.assertEqual(self.moved(after), [hall["city"]])
        self.assertEqual(after["cities"][hall["city"]], DAY)

    def test_a_new_hall_dates_its_city_and_the_indexes(self):
        venues = self.venues + [{"id": "venue-lar-new", "name": "New Hall", "city": "Larissa", "country": "GR",
                                 "address": "Odos 1", "sortOrder": 999}]
        self.assertEqual(self.moved(self.revised(venues)), ["Larissa", "directory"])

    def test_a_new_hall_in_a_hub_country_dates_its_hub_too(self):
        venues = self.venues + [{"id": "venue-cy-lar-new", "name": "New Hall", "city": "Larnaca", "country": "CY",
                                 "address": "Odos 1", "sortOrder": 999}]
        self.assertEqual(self.moved(self.revised(venues)), ["CY hub", "Larnaca", "directory"])

    def test_carom_tables_date_the_carom_pages_and_the_city(self):
        hall = no_carom_hall_with_a_phone()
        venues = [dict(v, caromTables=2) if v["id"] == hall["id"] else v for v in self.venues]
        self.assertEqual(self.moved(self.revised(venues)), sorted([hall["city"], "carom"]))

    def test_a_change_no_page_shows_moves_nothing_and_never_asks_git(self):
        venues = [dict(v, sortOrder=v["sortOrder"] + 1) for v in self.venues]

        def git_day():
            raise AssertionError("no listing changed, so no date was needed")

        self.assertEqual(self.revised(venues, git_day), self.dates)

    def test_git_is_asked_once_however_many_pages_change(self):
        calls = []
        venues = [dict(v, address=v["address"] + " ") for v in self.venues]
        after = self.revised(venues, lambda: calls.append(1) or DAY)
        self.assertEqual(len(calls), 1)
        self.assertEqual(set(after["cities"].values()), {DAY})

    def test_a_date_never_goes_back(self):
        hall = no_carom_hall_with_a_phone()
        venues = [dict(v, phone="+30 210 000 0000") if v["id"] == hall["id"] else v for v in self.venues]
        after = self.revised(venues, lambda: "2026-01-01")
        self.assertEqual(after["cities"][hall["city"]], self.dates["cities"][hall["city"]])

    def test_a_city_that_leaves_takes_its_date_along(self):
        gone = "Sparti"
        after = self.revised([v for v in self.venues if v["city"] != gone])
        self.assertNotIn(gone, after["cities"])
        self.assertEqual(after["directory"], DAY)


class ImportDateTest(unittest.TestCase):
    """--import writes data/revisions.json with the pages; --check names it when it would change."""

    def test_a_check_with_an_import_names_the_dates_and_the_changed_pages(self):
        hall = no_carom_hall_with_a_phone()
        backup = [dict(v, phone="+30 210 000 0000") if v["id"] == hall["id"] else v for v in committed()]
        slug = b.CITIES[hall["city"]][0]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(b, "revision_date", return_value=DAY):
            code, printed = generate("--import", str(app_data(tmp, backup)), "--check")
        self.assertEqual(code, 1)
        self.assertEqual(sorted(printed.splitlines()), sorted(
            f"out of date: {Path(p)}" for p in ("data/venues.json", "data/revisions.json", "sitemap.xml",
                                                 f"{b.EL_ROOT}/{slug}/index.html", f"{b.EN_ROOT}/{slug}/index.html")))

    def test_the_committed_dates_match_the_committed_halls(self):
        cities = cities_of(b.load_venues())
        dates = b.load_dates(cities)
        self.assertEqual(b.dates_text(dates), b.REVISIONS.read_text(encoding="utf-8"), "run the generator's format")
        # A day of slack: a page dated in Athens just after midnight is still yesterday on a UTC clock.
        newest = max([dates["directory"], dates["carom"], *dates["cities"].values(), *dates["hubs"].values()])
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        self.assertLessEqual(newest, tomorrow.isoformat(), "a page dated in the future")

    def test_dates_that_do_not_fit_the_halls_stop_the_build(self):
        cities = cities_of(b.load_venues())
        good = b.load_dates(cities)
        cases = {"no date for Athens": dict(good, cities={c: d for c, d in good["cities"].items() if c != "Athens"}),
                 "Berlin has no halls but has a date": dict(good, cities=dict(good["cities"], Berlin=DAY)),
                 "carom: '2026-13-01' is not a YYYY-MM-DD date": dict(good, carom="2026-13-01"),
                 "directory: 'today' is not a YYYY-MM-DD date": dict(good, directory="today"),
                 "no date for the CY hub": dict(good, hubs={}),
                 "the DE hub has no page but has a date": dict(good, hubs=dict(good["hubs"], DE=DAY)),
                 "CY hub: '4 Nov' is not a YYYY-MM-DD date": dict(good, hubs={"CY": "4 Nov"}),
                 "it needs exactly directory, carom, cities and hubs": {"cities": good["cities"]}}
        for message, dates in cases.items():
            with self.subTest(message), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp, "revisions.json")
                path.write_text(json.dumps(dates), encoding="utf-8")
                with mock.patch.object(b, "REVISIONS", path), self.assertRaises(SystemExit) as stop:
                    b.load_dates(cities)
                self.assertIn(message, str(stop.exception.code))


@unittest.skipUnless(shutil.which("git"), "git is not installed")
class RevisionDateTest(unittest.TestCase):
    """The import's date is the app repo's last commit of the backup or countries.json, never the clock."""

    def git(self, *args, day="2026-10-31T00:30:00+02:00"):
        env = dict(os.environ, GIT_AUTHOR_DATE=day, GIT_COMMITTER_DATE=day)
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false",
                        *args], cwd=self.app, env=env, check=True, capture_output=True)

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.app = Path(tmp.name, "data")
        self.source = app_data(self.app, [])
        self.git("init", "-q")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "data")

    def test_the_day_of_the_last_commit_in_its_own_time_zone(self):
        # Half past midnight in Athens is still 30 October in UTC: the commit's own zone decides.
        self.assertEqual(b.revision_date(self.source), "2026-10-31")
        Path(self.app, "countries.json").write_text("[]", encoding="utf-8")
        self.git("commit", "-q", "-am", "countries", day="2026-11-02T08:00:00+02:00")
        self.assertEqual(b.revision_date(self.source), "2026-11-02")

    def test_an_uncommitted_backup_stops_the_import(self):
        self.source.write_text("[{}]", encoding="utf-8")
        with self.assertRaises(SystemExit) as stop:
            b.revision_date(self.source)
        self.assertIn("uncommitted changes", str(stop.exception.code))

    def test_a_backup_outside_git_stops_the_import(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(SystemExit):
            b.revision_date(app_data(tmp, []))


if __name__ == "__main__":
    unittest.main()
