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


def strip_tags(fragment):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def visible_text(text):
    """What a reader sees: the body, without scripts or tags."""
    body = re.search(r"<body>(.*)</body>", text, re.S).group(1)
    return strip_tags(re.sub(r"<script\b.*?</script>", " ", body, flags=re.S))


def card_text(text):
    return strip_tags(re.search(r'<section class="cta-card" id="download">(.*?)</section>', text, re.S).group(1))


def is_greek(rel):
    return rel.startswith(f"{b.EL_ROOT}/")


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


class LeadTest(unittest.TestCase):
    WRITE_EL = f'<a href="mailto:{b.EMAIL}">Γράψε μας</a>'
    WRITE_EN = f'<a href="mailto:{b.EMAIL}">Email us</a>'

    def lead(self, city, halls, lang):
        return re.search(r'<p class="lead">(.*?)</p>', b.city_page(city, halls, {}, lang), re.S).group(1)

    def test_one_hall_lead_names_the_hall_and_its_district(self):
        naxos = [hall("venue-n", "Εξαρχοπούλου, Χώρα", "+30 698", city="Naxos", name="Galaxias Billiards")]
        self.assertEqual(self.lead("Naxos", naxos, "el"),
                         "Νάξος: ο κατάλογος του RackUp έχει μία αίθουσα μπιλιάρδου, το Galaxias Billiards (Χώρα). "
                         f"Ξέρεις κι άλλα μπιλιάρδα στη Νάξο; {self.WRITE_EL}.")
        self.assertEqual(self.lead("Naxos", naxos, "en"),
                         'Naxos (<span lang="el">Νάξος</span>): RackUp\'s directory lists one billiard hall, '
                         'Galaxias Billiards (<span lang="el">Χώρα</span>). '
                         f"Know another billiard hall in Naxos? {self.WRITE_EN}.")
        patras = [hall("venue-p", "Αγίου Ανδρέου 74", city="Patras", name="Πικέ Hall")]
        self.assertEqual(self.lead("Patras", patras, "el"),
                         "Πάτρα: ο κατάλογος του RackUp έχει μία αίθουσα μπιλιάρδου, το Πικέ Hall. "
                         f"Ξέρεις κι άλλα μπιλιάρδα στην Πάτρα; {self.WRITE_EL}.")
        self.assertEqual(self.lead("Patras", patras, "en"),
                         'Patras (<span lang="el">Πάτρα</span>): RackUp\'s directory lists one billiard hall, '
                         f'<span lang="el">Πικέ Hall</span>. Know another billiard hall in Patras? {self.WRITE_EN}.')

    def test_lead_lists_up_to_four_districts_and_says_when_halls_lie_elsewhere(self):
        covered = [hall("a", "Odos 1, Kalamaria", "+30 1"), hall("b", "Odos 2, Pylaia", "+30 2")]
        self.assertEqual(self.lead("Larissa", covered, "el"),
                         "Λάρισα: 2 αίθουσες μπιλιάρδου στον κατάλογο του RackUp, σε Kalamaria και Pylaia. "
                         "Παρακάτω θα βρεις τα μπιλιάρδα με τις διευθύνσεις και τα τηλέφωνά τους.")
        self.assertEqual(self.lead("Larissa", covered, "en"),
                         'Larissa (<span lang="el">Λάρισα</span>): RackUp\'s directory lists 2 billiard halls, in '
                         '<span lang="el">Kalamaria</span> and <span lang="el">Pylaia</span>. '
                         "Below, each hall comes with its address and phone number.")
        unplaced = covered + [hall("c", "Odos 3")]
        self.assertIn("σε Kalamaria, Pylaia και αλλού.", self.lead("Larissa", unplaced, "el"))
        self.assertIn('<span lang="el">Pylaia</span> and elsewhere.', self.lead("Larissa", unplaced, "en"))
        many = [hall(f"h{i}", f"Odos {i}, {area}") for i, area in enumerate(("Ano", "Kato", "Mesa", "Exo", "Pano"))]
        self.assertIn("σε Ano, Kato, Mesa, Exo και αλλού. Παρακάτω θα βρεις τα μπιλιάρδα με τις "
                      "διευθύνσεις τους.", self.lead("Larissa", many, "el"))
        self.assertIn("Below, each hall comes with its address.", self.lead("Larissa", many, "en"))

    def test_every_city_page_opens_with_the_city_and_says_mpiliarda_once(self):
        for city, _, lang, text in city_pages():
            name_el = b.CITIES[city][1]
            lead = re.search(r'<p class="lead">(.*?)</p>', text, re.S).group(1)
            if lang == "el":
                self.assertTrue(lead.startswith(f"{name_el}: "), lead)
                self.assertEqual(len(re.findall(r"\bμπιλιάρδα\b", visible_text(text))), 1, city)
            else:
                self.assertTrue(lead.startswith(f'{city} (<span lang="el">{name_el}</span>): '), lead)


class DownloadCardTest(unittest.TestCase):

    def test_card_names_pool_and_carom_and_how_the_app_finds_a_game(self):
        greek = ("αμερικάνικο (8-Ball, 9-Ball, 10-Ball)", "γαλλικό (τρίσποντο, μονόσποντο)",
                 "στις αίθουσες με τραπέζια γαλλικού", "ζήτα να μπεις σε τραπέζι που άνοιξε κάποιος άλλος",
                 "Στη ροή φιλτράρεις ανά πόλη", "κατάταξη ανά πόλη και αίθουσα")
        english = ("pool (8-Ball, 9-Ball, 10-Ball)", "carom (3-cushion, 1-cushion)", "at halls with carom tables",
                   "ask to join a table someone else opened", "The feed filters by city",
                   "a ranking by city and hall")
        for rel, text in directory_pages().items():
            card = card_text(text)
            for phrase in greek if is_greek(rel) else english:
                self.assertIn(phrase, card, rel)
            self.assertNotIn("8άρα", card, rel)

    def test_greek_pages_say_amerikaniko_and_never_poul(self):
        poul = re.compile(r"\bπουλ\b", re.I)
        for rel, text in directory_pages().items():
            seen = visible_text(text)
            if is_greek(rel):
                self.assertIn("αμερικάνικο", seen, rel)
                self.assertIn("γαλλικό", seen, rel)
                self.assertNotRegex(seen, poul, rel)
            else:
                self.assertIn("carom", seen, rel)


if __name__ == "__main__":
    unittest.main()
