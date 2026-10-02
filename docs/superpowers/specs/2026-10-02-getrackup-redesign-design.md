# getrackup.com redesign: Felt and Neon

Date: 2026-10-02. Owner: Fanis. Status: draft for review.

## Intent

**What Fanis asked for:** revamp getrackup.com into the most eye-catching site it can be, in the
app's colours. Greek first, English at `/en/`. Direction "A, night in the hall" for the hero,
plus direction B's 01/02/03 how-it-works section and a subtle rack triangle lower on the page.

**Assumed goal (Claude's reading):** turn visitors into installs and make RackUp look like a
real, trustworthy product. Visitors arrive from the Facebook and Instagram profiles, Google
searches for halls ("μπιλιάρδο Πάτρα"), the App Store marketing link, hall QR codes, and soon
paid ads (from about 8 October). Success means: the site looks like the app, loads fast on a
phone, keeps every SEO signal and tracked link working, and makes "download" the obvious next
step on every page.

## Constraints

- **Brand is the app's "Felt and Neon"** (`RackUpColors.kt`): background `#0E1512`, surfaces
  `#18221C` / `#131C17` / `#1E2A23`, ink `#EAF2ED`, ink2 `#B4C3BA`, muted `#8A9C90`, outline
  `#28312C`, one accent, neon lime `#C6F24E`, text on lime `#0E1512`. Signals `#3FD597`.
  Ball colours as the app. Wordmark RACK + UP in lime. Dark only. No cue sticks, baize,
  casino or neon-sign pastiche, nothing that reads as a pool video game (logo brief).
- **Type:** Space Grotesk (display) and Hanken Grotesk (body), as the app. Neither has Greek,
  so Greek glyphs come from **Commissioner** (variable, OFL, has Greek) through `unicode-range`.
- **No third-party requests, no cookies, no analytics.** Fonts are self-hosted. The existing
  `test_no_page_tracks_visitors_or_loads_from_another_host` keeps guarding this.
- **Nothing that works today may break:** every URL, canonical, hreflang, JSON-LD and sitemap
  entry; the generator's counts and campaign-tagged store links (PR #14); the `/go/` and `/m/`
  scripts, their element ids and their tests; the privacy policy text, word for word.
- **Copy:** no em or en dashes (the generator already refuses them). Claims must be true of the
  app version live in both stores on the day the page goes live.
- **Comments in code: five lines at most.**

## Information architecture

| URL | Language | Source | Change |
|---|---|---|---|
| `/` | Greek (new) | hand-written `index.html` | New Greek home |
| `/en/` | English (new path) | hand-written `en/index.html` | English home moves here, redesigned |
| `/mpiliardo/`, `/mpiliardo/<city>/` | Greek | generator | New template, same content and SEO |
| `/en/billiards/`, `/en/billiards/<city>/` | English | generator | New template, same content and SEO |
| `/support.html` | English | hand-written | Restyled, text unchanged in this PR |
| `/privacy.html` | English | hand-written | Restyled, text verbatim |
| `/go/`, `/m/` | Greek + English | hand-written + JS | Restyled, ids and logic unchanged |
| `/404.html` | Greek + English | hand-written | New, GitHub Pages serves it for missing paths |

`/` and `/en/` are an hreflang pair (`x-default` is `/`). Header language switch links the pair.
The App Store marketing URL `https://getrackup.com/` therefore lands on Greek, with EN one tap
away. `campaign_for()` maps `en/` to campaign `en-home`; `/` stays `home`.

## Design system

One stylesheet, `assets/site.css`, replaces `assets/style.css` and the privacy page's inline
`<style>`. Tokens are CSS custom properties named after the app's (`--bg`, `--surface`,
`--accent`, ...). Components:

- **Header:** sticky, translucent `#0E1512` with blur; wordmark (CSS 8-ball + RACKUP); links
  (Αίθουσες, Πώς δουλεύει, Βοήθεια, EN/ΕΛ); a lime "Κατέβασέ το" pill that jumps to
  `#download`. On phones the links collapse to the pill and the language switch.
- **Buttons:** lime primary, outlined secondary, 16px radius, Apple and Play glyphs.
- **Balls:** CSS-drawn 8, 9, 10 and the three carom balls (no images).
- **Phone frame:** CSS frame around a real app screenshot.
- **Notification card:** the floating glass card from the mockup.
- **Cards, chips, stats, FAQ (`<details>`), breadcrumbs, footer.**
- **Motion:** only the live-dot pulse and a slow float on the hero ball; all of it off under
  `prefers-reduced-motion`.
- **Accessibility:** WCAG AA contrast (lime on `#0E1512` and ink2 on surfaces both pass), visible
  lime focus rings, skip link, `lang` on every mixed-language span, alt text in the page's language.

**Fonts:** `assets/fonts/` holds four woff2 files, subset with fonttools: Space Grotesk and
Hanken Grotesk (Latin and Latin Extended), Commissioner (Greek and Greek Extended, used for
both roles). Two families are declared, `RackUp Display` and `RackUp Text`, each with a Latin
face and a Greek face split by `unicode-range`, `font-display: swap`. The Greek display face is
preloaded on Greek pages, the Latin one on English pages. OFL licence files ship next to them.
Budget about 120 KB of fonts in total. Source: the OFL font files in github.com/google/fonts
(`ofl/spacegrotesk`, `ofl/hankengrotesk`, `ofl/commissioner`), roughly 0.3 to 1 MB each before
subsetting; only the subset woff2 files are committed.

## Home page (Greek and English, same structure)

1. **Hero (direction A):** eyebrow with live dot and the generator-updated counts
   ("76 αίθουσες σε 27 πόλεις"); H1 "Βρες αντίπαλο. Παίξε απόψε." (EN "Find an opponent.
   Play tonight."); lead; App Store and Google Play buttons (generator-tagged); trust row
   (Δωρεάν, Χωρίς διαφημίσεις, iPhone και Android); stage with two phones, two notification
   cards and a floating 9-ball over a lime glow and a faint dot grid.
2. **Games strip:** 8-Ball, 9-Ball, 10-Ball, Τρίσποντο, Σπόντα chips; stats 76 / 27 / 0 €.
3. **How it works (from B):** 01 Δημοσίευσε το τραπέζι, 02 Διάλεξε αντίπαλο, 03 Παίξε και
   κράτα σκορ.
4. **Features:** a bento grid of the app's real features with one screenshot tile. Only what
   is live: feed and Play Now, you pick who plays and open challenges by tier, scores and
   leaderboards and badges, reliability and block/report, carom.
5. **Halls:** "76 αίθουσες σε 27 πόλεις" with a grid of every city and its count, linking to
   the directory. The generator fills it between `<!-- city-grid -->` markers, so it never goes
   stale. A large faint rack triangle sits behind this section.
6. **FAQ:** five short answers (is it free, which games, where, iPhone and Android, how do I
   find an opponent), plus `FAQPage` JSON-LD.
7. **Download (`#download`):** "Το επόμενο ματς σου σε περιμένει." with both store buttons.
8. **Footer:** wordmark, directory, support, privacy, email, language, "RackUp · Ιωάννινα".

No section lists platform differences: they change every release. The support page owns them.

## Other pages

- **Directory index and city pages (generator `page()` and friends):** new header and footer,
  a hero band with the city and its count, hall cards (name, address, phone, website), a CTA
  card with store buttons and a small phone screenshot, other cities as chips, breadcrumbs. Head
  tags, JSON-LD, ids (`#venue-…` anchors used by hall QR links) and text stay as they are.
- **Support and privacy:** new header, footer and typography; privacy text verbatim.
- **`/go/` and `/m/`:** a centred card with the ball row, same headings, buttons and ids. Their
  CSP gains `font-src 'self'` (fonts are blocked today); the tests that pin the CSP change with it.
- **404:** bilingual card, links to home and the directory.
- **Social card:** `assets/og-card.png`, 1200x630, wordmark, headline and a phone, rendered once
  from an HTML file with headless Edge. Used as `og:image` on the homes and directory pages; the
  share and go pages keep their own image tags pointing at it too.

## Screenshots

Hero and tiles use the Greek and English iOS store screenshots (`store-assets/ios-screenshots`),
converted to WebP at 1x and 2x with explicit `width`/`height`. The venues list screenshot says
"65 αίθουσες", so it is **not used**; the venue detail, create and welcome screens are. Fresh
2.2.0 screenshots are a follow-up, not part of this PR.

## Performance and SEO budget

Home under 400 KB transferred on first load (fonts about 120 KB, CSS under 25 KB, images about
200 KB, no JavaScript on the home page). Below-the-fold images lazy-load; the front hero phone
has `fetchpriority="high"`. Lighthouse 95 or more for performance, accessibility, best practices
and SEO on the Greek home and one city page, mobile profile.

## Testing

- All existing tests pass: `python tools/build_directory.py --check`,
  `python -m unittest discover -s tools`, `node --test tools/go_page.test.js` and
  `tools/match_page.test.js`, with the CSP expectations updated deliberately.
- New Python tests: every page links `assets/site.css` and nothing else; the old palette
  (`#0C3B2A`, `#FFC66E`) appears nowhere; every font file referenced exists; every `<img>` has
  `alt`, `width` and `height`; `/` and `/en/` are a correct hreflang pair; both homes carry the
  generated counts and city grid; every internal link resolves to a file.
- Visual: headless Edge screenshots of every page type at 390, 768 and 1280 wide, checked by eye
  and sent to Fanis before merge.

## Rollout

Branch `redesign/felt-neon` in its own worktree, one PR on fpasxos/rackup-site, merged only
after Fanis sees the screenshots and says yes. The ads session is told when the PR opens,
since it also edits the generator (App Store `pt` token).

**Release-day follow-up (2.2.0, a separate small PR):** add player search, direct challenges and
quick messages to the features grid, and correct the support page (carom games, quick messages
and direct challenges now exist, iPhone location and photo).

## Out of scope

Fresh 2.2.0 screenshots, a logo change, a light theme, analytics of any kind, a CMS, and
country folders for expansion (the `/en/` move makes room for them later).
