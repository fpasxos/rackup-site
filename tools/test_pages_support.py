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


def paragraphs(page):
    """Every paragraph of the policy, in order, as its visible text."""
    return [visible_text(p) for p in re.findall(r"<p\b[^>]*>(.*?)</p>", main_html(page), re.S)]


# From 2.4.9: each new paragraph, the one it must follow, and facts it must keep, in both languages.
INVITE_LINES = (
    ("Sharing a game.", "Inviting a friend.",
     ("From version 2.4.9", "14 days", "never your name or user id", "reads nothing from our database",
      "Anyone with an account who has the code", "30 days after it expires", "when you delete your account")),
    ("Where new players come from.", "Links from posters, invites and shared games.",
     ("From version 2.4.9", "once, on your phone",
      "Of these tags, only the hall, the invite's code and the game they name can reach us",
      "The app logs that it opened one this way as link_opened",
      "when the game is another player's open match, opening it also logs match_viewed",
      "On iPhone the app reads nothing")),
    ("Κοινοποίηση ματς.", "Πρόσκληση σε φίλο.",
     ("Από την έκδοση 2.4.9", "14 ημέρες", "ποτέ το όνομα ή το αναγνωριστικό χρήστη σου",
      "δεν διαβάζει τίποτα από τη βάση δεδομένων μας", "Όποιος έχει λογαριασμό και τον κωδικό",
      "30 ημέρες αφού λήξει", "όταν διαγράψεις τον λογαριασμό σου")),
    ("Στο Android, όταν εγκαθιστάς την εφαρμογή από σύνδεσμό μας",
     "Σύνδεσμοι από αφίσες, προσκλήσεις και κοινοποιημένα ματς.",
     ("Από την έκδοση 2.4.9", "μία φορά, στο τηλέφωνό σου",
      "μόνο η αίθουσα, ο κωδικός της πρόσκλησης και το ματς που αναφέρουν μπορεί να μας φτάσουν",
      "καταγράφει ότι άνοιξε έτσι ένα από αυτά με το συμβάν link_opened",
      "όταν το ματς είναι ανοιχτό ματς άλλου παίκτη, καταγράφει επίσης το match_viewed",
      "Στο iPhone η εφαρμογή δεν διαβάζει τίποτα")),
)


class InviteLinksPolicyTest(unittest.TestCase):
    """2.4.9 invites and hall links: said beside the paragraphs they extend, in English and Greek."""

    def test_each_paragraph_follows_the_one_it_extends_and_keeps_its_facts(self):
        said = paragraphs(current("privacy.html"))
        for before, opening, facts in INVITE_LINES:
            with self.subTest(paragraph=opening):
                at = [i for i, p in enumerate(said) if p.startswith(before)]
                self.assertEqual(len(at), 1, f"one paragraph should open {before!r}")
                self.assertTrue(said[at[0] + 1].startswith(opening), f"{opening!r} is not right after {before!r}")
                for fact in facts:
                    self.assertIn(fact, said[at[0] + 1])

    def test_the_2_4_9_note_says_what_changed(self):
        newest = next(p for p in paragraphs(current("privacy.html")) if p.startswith("What changed on 18 November 2026."))
        for fact in ("version 2.4.9", "invite a friend", "Google Play", "37 in all", "How long we keep it",
                     "What deletion removes", "of these tags only the hall, the invite's code and the game they name can reach us",
                     "a friend's invite or a shared game's page",
                     "the app logs that it opened one, as link_opened, and a game also as match_viewed when it is another player's open match", "in the summary in Greek too"):
            self.assertIn(fact, newest)
        # link_opened sends Analytics that the app opened a hall or invite from a link or the Play tags.
        self.assertNotIn("Nothing about it is sent to us", visible_text(main_html(current("privacy.html"))))
        self.assertNotIn("nothing about it is sent to us", newest)

    def test_an_invite_gives_its_hall_only_to_a_friend_with_none(self):
        # rackup#723: the star, then the home hall, for any account with none in the hall's country.
        text = visible_text(main_html(current("privacy.html")))
        for said in ("If the hall is in their own country, a friend with no usual hall yet gets it as their usual "
                     "hall and as a starred hall, which brings them its notifications; one who has a usual hall "
                     "keeps it.",
                     "Right after joining, your friend can undo it from the hall's page, which deletes the join and "
                     "takes back the follows, the usual hall and the star the invite made. Later, they can still "
                     "unfollow you, change their usual hall and remove the star.",
                     "home_venue_set, when you pick a home hall, at its end or later, and, from version 2.4.9, "
                     "when a friend's invite gives you one;",
                     "Αν η αίθουσα είναι στη χώρα του, ένας φίλος που δεν έχει ακόμη λέσχη την παίρνει ως λέσχη του "
                     "και στις αγαπημένες του, που του φέρνουν τις ειδοποιήσεις τους, ενώ όποιος έχει ήδη λέσχη "
                     "την κρατά.",
                     "Αμέσως μετά, ο φίλος σου μπορεί να το αναιρέσει από τη σελίδα της αίθουσας, οπότε σβήνουμε την "
                     "καταγραφή και παίρνουμε πίσω ό,τι έκανε η πρόσκληση: το ότι ακολουθείτε ο ένας τον άλλον, τη "
                     "λέσχη και την αγαπημένη αίθουσα. Αργότερα μπορεί ακόμη να σταματήσει να σε ακολουθεί, να αλλάξει "
                     "λέσχη και να βγάλει την αίθουσα από τις αγαπημένες του."):
            self.assertIn(said, text)
        # rackup#723's undo is a card on the hall's page that a restart forgets; the text says so.
        for old in ("A friend who is new to RackUp", "Your friend can undo this.", "Your friend can undo what",
                    "καινούργιος στο RackUp", "Ο φίλος σου μπορεί να το αναιρέσει.",
                    "Ο φίλος σου μπορεί να αναιρέσει ό,τι"):
            self.assertNotIn(old, text)

    def test_invite_shared_never_claims_an_invite_was_sent(self):
        # The app logs it when the share sheet opens or the QR code shows; it cannot see a send.
        main = main_html(current("privacy.html"))
        (item,) = [visible_text(li) for li in re.findall(r"<li>(.*?)</li>", main, re.S) if "<code>invite_shared</code>" in li]
        self.assertIn("when you open your phone's share sheet with an invite to play at a hall, or show its QR code", item)
        self.assertIn("never whether you sent it, or to whom", item)
        text = visible_text(main)
        self.assertIn("όταν ανοίγεις την κοινοποίηση μιας πρόσκλησης για μια αίθουσα ή δείχνεις τον κωδικό QR της", text)
        self.assertIn("όχι όμως αν την έστειλες ή σε ποιον", text)
        for claim in ("when you share an invite", "whether you sent its link", "όταν στέλνεις σε φίλο πρόσκληση",
                      "αν έστειλες τον σύνδεσμο"):
            self.assertNotIn(claim, text)

    def test_invites_are_in_the_notifications_retention_and_deletion_parts(self):
        main = main_html(current("privacy.html"))
        text = visible_text(main)
        lists = {visible_text(li) for li in re.findall(r"<li>(.*?)</li>", main, re.S)}
        self.assertIn("Invites: they work for 14 days and are deleted 30 days after they expire, with their joins.",
                      lists)
        self.assertIn("the invites you made, and your joins through other players' invites;", lists)
        # Each cap as it is: a few a day for the others, per invite for invites.
        self.assertIn('the records that keep the notifications about your new matches, direct challenges and '
                      'invitations to games at the table, and your "No answer yet" notices, to a few a day;', lists)
        self.assertIn("the record that keeps each of your invites to at most 10 friends at a time and 5 pushes;", lists)
        for said in ("each running invite's code, when it ends, the time of each join with it that has not been undone,",
                     "and drops an invite from that record within about a day of its end.",
                     "none goes at night, from 23:00 to 09:00 at the hall's local time, nor later",
                     "One invite acts on at most 10 friends at a time and sends you at most 5 pushes.",
                     "no invite code",
                     "για κάθε πρόσκληση που ισχύει ακόμη, τον κωδικό της, πότε λήγει, "
                     "πότε μπήκε με αυτήν κάθε φίλος που δεν το έχει αναιρέσει",
                     "και τη βγάζει από την εγγραφή μέσα σε περίπου μία ημέρα αφού λήξει.",
                     "Μια πρόσκληση μετρά το πολύ 10 φίλους κάθε φορά και σου στέλνει το πολύ 5 ειδοποιήσεις push.",
                     "οι προσκλήσεις σου σε φίλους και ό,τι καταγράψαμε όταν μπήκες με πρόσκληση άλλου",
                     "μαζί με όσα καταγράψαμε για όσους μπήκαν με αυτήν"):
            self.assertIn(said, text)
        # The server prunes the record in a daily sweep (rackup#714), not the moment an invite ends.
        # An undone join frees its place there, so the cap is 10 at a time and the record keeps each join's time.
        for old in ("drops an invite from that record once it ends", "τη βγάζει από την εγγραφή όταν λήξει",
                    "invitations to games at the table and invites",
                    "10 friends who join", "how many friends joined with it",
                    "10 φίλους και σου", "πόσοι φίλοι μπήκαν με αυτήν"):
            self.assertNotIn(old, text)


class GameLinksPolicyTest(unittest.TestCase):
    """2.4.9: a shared game's page opens the game, and its Play link carries the game's id."""

    def test_link_opened_names_games_beside_halls_and_invites(self):
        text = visible_text(main_html(current("privacy.html")))
        for said in ("when the app opens a hall, an invite or a game, with which of the three",
                     "ανοίγει μια αίθουσα, μια πρόσκληση ή ένα ματς, με το ποιο από τα τρία ήταν",
                     "the tags the Android app reads after an install from a hall's poster, a hall's share card, "
                     "a friend's invite or a shared game's page",
                     # A game comes only from the Play tags: a tapped game link logs match_viewed instead.
                     "and a game only from those tags", "και ένα ματς μόνο από αυτές τις ετικέτες"):
            self.assertIn(said, text)
        # A poster's hall is loaded by its id too, and a game opened also logs match_viewed.
        for old in ("None of these tags is sent to us", "none of these tags is sent to us",
                    "Καμία από αυτές τις ετικέτες δεν μας στέλνεται", "logs only that it opened",
                    "καταγράφει μόνο ότι άνοιξε", "whether it came from a link, from the tags",
                    "και αν ήρθε από σύνδεσμο, από τις ετικέτες"):
            self.assertNotIn(old, text)
        for old in ("when the app opens a hall or an invite, with which of the two",
                    "ανοίγει μια αίθουσα ή μια πρόσκληση, με το ποια από τις δύο ήταν", "a hall's share card or a friend's invite",
                    "Links from posters and invites.", "Σύνδεσμοι από αφίσες και προσκλήσεις."):
            self.assertNotIn(old, text)


def section(page, title):
    """The visible text of an <h3> section, up to the next heading."""
    found = re.search(r"<h3>%s</h3>(.*?)<h[23]\b" % re.escape(title), main_html(page), re.S)
    if not found:
        raise AssertionError(f"privacy.html has no {title} section")
    return visible_text(found.group(1))


class HallLadderPolicyTest(unittest.TestCase):
    """2.5.0 hall ladders (rackup docs/LADDER.md): who sees a board, what stays private, how long it lasts."""

    def test_the_section_follows_rankings_and_says_who_sees_what(self):
        main = main_html(current("privacy.html"))
        self.assertLess(main.index("<h3>Rankings</h3>"), main.index("<h3>Hall ladders</h3>"))
        self.assertLess(main.index("<h3>Hall ladders</h3>"), main.index("<h3>What you post and write</h3>"))
        text = section(current("privacy.html"), "Hall ladders")
        for said in ("their user id, display name, photo link and category, as on their player card",
                     "once one of their games has counted, their place and points",
                     "It never holds a player's wins, how many games they played or their games this week.",
                     "Only players with an account can read it, never guests",
                     "Only you can read your join and those numbers.",
                     "our server takes you off the board within about an hour",
                     "until the following season ends",
                     "Once final, that board also shows who won the season.",
                     "does not take you off that board; deleting your account does",
                     "which their player card shows to every player with an account for 4 weeks",
                     "a badge that has ended stays there until they win another season or delete their account",
                     "Apple's review account and automated test accounts are never on a board"):
            self.assertIn(said, text)

    def test_a_leave_or_a_hide_is_never_promised_at_once(self):
        # Past a player's 6 rebuilds a day, a leave or a hidden card waits for the hourly run.
        page = current("privacy.html")
        self.assertNotIn("at once", section(page, "Hall ladders"))
        (greek,) = [p for p in paragraphs(page) if p.startswith("Σκάλα της αίθουσας.")]
        self.assertNotIn("αμέσως", greek)
        for said in ("μέσα σε περίπου μία ώρα", "Τη βλέπουν μόνο όσοι έχουν λογαριασμό, ποτέ οι επισκέπτες",
                     "Πόσα ματς σου μέτρησαν τη σεζόν και την εβδομάδα τα βλέπεις μόνο εσύ.",
                     "για 4 εβδομάδες", "σε βγάζει μόνο η διαγραφή του λογαριασμού σου",
                     "Η οριστική σκάλα δείχνει επίσης ποιος κέρδισε τη σεζόν."):
            self.assertIn(said, greek)

    def test_ladders_are_in_the_visibility_retention_and_deletion_parts(self):
        main = main_html(current("privacy.html"))
        lists = [visible_text(li) for li in re.findall(r"<li>(.*?)</li>", main, re.S)]
        self.assertTrue(any(item.startswith("Hall ladders: your join, with how many of your games counted, until you "
                                            "leave the ladder or delete your account.") for item in lists))
        self.assertIn("your joins of hall ladders, with how many of your games counted, your place on every hall's "
                      "ladder board, this season's and the last, your ladder badges, and every mention of you in our "
                      "server's record for each ladder;", lists)
        self.assertIn("the records that keep your ladder pushes to a few a week, and the board updates that your "
                      "joins and player card start to 6 a day;", lists)
        text = visible_text(main)
        for said in ("your joins of hall ladders with how many of your games counted there",
                     "for matches, challenges, player cards and hall ladders the rules also check for an account",
                     "share_opened, ladder_joined and ladder_opened. A hall id names a billiard hall",
                     "οι συμμετοχές σου στις σκάλες των αιθουσών"):
            self.assertIn(said, text)


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


# The app's AnalyticsEvent names (core/presentation Analytics.kt). The app's AnalyticsTest
# pins the same list, so a new event fails there until this list and the policy name it.
APP_EVENTS = {
    "sign_up", "login", "guest_browse_started", "email_verified", "tutorial_complete",
    "home_venue_set", "notification_permission_result", "match_viewed", "match_posted",
    "join_requested", "request_accepted", "score_reported", "score_confirmed", "score_disputed",
    "opponent_rated", "h2h_opened", "h2h_rematch", "reputation_opened",
    "looking_for_game_posted", "looking_for_game_converted", "venue_checked_in",
    "player_followed", "saved_search_created", "notifications_opened", "notification_row_tapped",
    "match_shared", "seat_check_answered", "rankings_opened", "ranking_hall_opened", "share_opened",
    "table_game_logged", "screen_view", "post_started",
    "link_opened", "invite_shared", "invite_joined", "invite_undone",
    "ladder_joined", "ladder_opened",
}

# The app's UserProperty names (core/presentation Analytics.kt, from 2.4.8).
APP_USER_PROPERTIES = {"home_country", "account", "theme"}


def listed_events(page):
    """The event names in the list under App usage analytics."""
    section = re.search(r"<h3>App usage analytics\b.*?</h3>.*?<ul>(.*?)</ul>", main_html(page), re.S)
    if not section:
        raise AssertionError("privacy.html has no App usage analytics list")
    return set(re.findall(r"<code>([a-z0-9_]+)</code>", section.group(1)))


def named_user_properties(page):
    """The <code> names in the User properties paragraph under App usage analytics."""
    found = re.search(r"<h3>App usage analytics\b.*?</h3>.*?<p><strong>User properties\.</strong>(.*?)</p>",
                      main_html(page), re.S)
    if not found:
        raise AssertionError("privacy.html has no User properties paragraph under App usage analytics")
    return set(re.findall(r"<code>([a-z0-9_]+)</code>", found.group(1)))


class AnalyticsCountTest(unittest.TestCase):

    def test_the_policy_lists_every_event_the_apps_log(self):
        self.assertEqual(APP_EVENTS, listed_events(current("privacy.html")))

    def test_both_languages_give_the_count_of_the_listed_events(self):
        text = visible_text(main_html(current("privacy.html")))
        english = re.search(r"We log (\d+) events about how the app is used", text)
        greek = re.search(r"Firebase Analytics \((\d+) συμβάντα χρήσης", text)
        self.assertTrue(english and greek, "a count sentence moved or changed its words")
        self.assertEqual(len(APP_EVENTS), int(english.group(1)))
        self.assertEqual(len(APP_EVENTS), int(greek.group(1)))

    def test_the_policy_names_every_user_property_the_apps_set(self):
        self.assertEqual(APP_USER_PROPERTIES, named_user_properties(current("privacy.html")))

    def test_the_property_check_reads_only_its_own_paragraph(self):
        page = ('<main><h3>App usage analytics</h3><ul><li><code>theme</code></li></ul>'
                '<p><strong>User properties.</strong> <code>account</code> and <code>home_country</code>.</p>'
                '<p><code>theme</code></p></main>')
        self.assertEqual({"account", "home_country"}, named_user_properties(page))


if __name__ == "__main__":
    if sys.argv[1:] == ["--capture"]:
        capture()
    else:
        unittest.main()
