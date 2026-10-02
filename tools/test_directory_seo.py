"""Search copy on the directory pages: titles, descriptions, leads, the download card, JSON-LD.
Python 3.8+, no packages: python -m unittest discover -s tools
"""
import html
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402

TITLE_LIMIT = 60
TAIL_EL = "Βρες αντίπαλο με το δωρεάν RackUp."
TAIL_EN = "Find an opponent with the free RackUp app."


def hall(vid, address, phone=None, city="Larissa", name=None):
    v = {"id": vid, "name": name or vid.title(), "city": city, "address": address, "sortOrder": 1}
    if phone:
        v["phone"] = phone
    return v


def directory_pages():
    """Repo path -> text for every generated page under the two directory roots."""
    roots = (f"{b.EL_ROOT}/", f"{b.EN_ROOT}/")
    pages = {}
    for path, text in b.render().items():
        rel = path.relative_to(b.ROOT).as_posix()
        if path.suffix == ".html" and rel.startswith(roots):
            pages[rel] = text
    return dict(sorted(pages.items()))


def city_pages():
    """(city, halls, lang, text) for every generated city page."""
    cities = b.group_by_city(b.load_venues())
    for city, halls in sorted(cities.items()):
        for lang in ("el", "en"):
            yield city, halls, lang, b.city_page(city, halls, cities, lang)


def title(text):
    return html.unescape(re.search(r"<title>(.*?)</title>", text).group(1))


def description(text):
    return html.unescape(re.search(r'<meta name="description" content="([^"]*)">', text).group(1))


class TitleAndDescriptionTest(unittest.TestCase):

    def test_titles_name_the_hall_count_and_fit_sixty_characters(self):
        for city, halls, lang, text in city_pages():
            n, (_, _, in_el) = len(halls), b.CITIES[city]
            if n == 1:
                continue
            expected = (f"Μπιλιάρδο {in_el}: {n} αίθουσες μπιλιάρδου | RackUp" if lang == "el"
                        else f"Pool and billiards in {city}: {n} halls | RackUp")
            self.assertEqual(title(text), expected, f"{city} {lang}")
        for rel, text in directory_pages().items():
            self.assertLessEqual(len(title(text)), TITLE_LIMIT, f"{rel}: {title(text)}")

    def test_one_hall_titles_name_the_hall_and_drop_the_brand_only_to_fit(self):
        naxos = b.city_page("Naxos", [hall("venue-n", "Odos 1", city="Naxos", name="Galaxias Billiards")],
                            {}, "el")
        self.assertEqual(title(naxos), "Μπιλιάρδο στη Νάξο: Galaxias Billiards | RackUp")
        long_name = "Rolling Billiards & Coffee Bar"
        sparti = b.city_page("Sparti", [hall("venue-s", "Odos 1", city="Sparti", name=long_name)], {}, "el")
        self.assertEqual(title(sparti), f"Μπιλιάρδο στη Σπάρτη: {long_name}")

    def test_descriptions_fit_are_unique_and_name_the_city(self):
        self.assertEqual(b.DESCRIPTION_LIMIT, 155)
        seen = {}
        for rel, text in directory_pages().items():
            found = description(text)
            self.assertLessEqual(len(found), b.DESCRIPTION_LIMIT, f"{rel}: {found}")
            self.assertNotIn(found, seen, f"{rel} repeats the description of {seen.get(found)}")
            seen[found] = rel
        for city, _, lang, text in city_pages():
            self.assertIn(b.CITIES[city][2] if lang == "el" else city, description(text), f"{city} {lang}")

    def test_descriptions_say_what_each_hall_comes_with(self):
        phones = [hall("a", "Odos 1, Kalamaria", "+30 1"), hall("b", "Odos 2, Pylaia", "+30 2")]
        mixed = [hall("a", "Odos 1"), hall("b", "Odos 2", "+30 2")]
        self.assertEqual(description(b.city_page("Larissa", phones, {}, "el")),
                         f"Μπιλιάρδο στη Λάρισα: 2 αίθουσες με διευθύνσεις και τηλέφωνα. "
                         f"Περιοχές: Kalamaria, Pylaia. {TAIL_EL}")
        self.assertEqual(description(b.city_page("Larissa", mixed, {}, "el")),
                         f"Μπιλιάρδο στη Λάρισα: 2 αίθουσες με διευθύνσεις. {TAIL_EL}")
        self.assertEqual(description(b.city_page("Larissa", phones, {}, "en")),
                         f"Billiards in Larissa: 2 halls with addresses and phone numbers. "
                         f"Areas: Kalamaria, Pylaia. {TAIL_EN}")
        self.assertEqual(description(b.city_page("Larissa", mixed, {}, "en")),
                         f"Billiards in Larissa: 2 halls with addresses. {TAIL_EN}")

    def test_one_hall_descriptions_carry_the_phone_when_there_is_one(self):
        with_phone = [hall("a", "Odos 1, Chora", "+30 698", city="Naxos", name="Galaxias")]
        without = [hall("a", "Odos 1, Chora", city="Naxos", name="Galaxias")]
        self.assertEqual(description(b.city_page("Naxos", with_phone, {}, "el")),
                         f"Μπιλιάρδο στη Νάξο: Galaxias, Odos 1, Chora, τηλ. +30 698. {TAIL_EL}")
        self.assertEqual(description(b.city_page("Naxos", without, {}, "el")),
                         f"Μπιλιάρδο στη Νάξο: Galaxias, Odos 1, Chora. {TAIL_EL}")
        self.assertEqual(description(b.city_page("Naxos", with_phone, {}, "en")),
                         f"Billiards in Naxos: Galaxias, Odos 1, Chora, phone +30 698. {TAIL_EN}")
        self.assertEqual(description(b.city_page("Naxos", without, {}, "en")),
                         f"Billiards in Naxos: Galaxias, Odos 1, Chora. {TAIL_EN}")


if __name__ == "__main__":
    unittest.main()
