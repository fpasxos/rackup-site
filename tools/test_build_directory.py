"""Tests for tools/build_directory.py. Python 3.8+, no packages:
python -m unittest discover -s tools
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_directory as b  # noqa: E402


def hall(vid, address, city="Larissa"):
    return {"id": vid, "name": vid.title(), "city": city, "address": address, "sortOrder": 1}


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


if __name__ == "__main__":
    unittest.main()
