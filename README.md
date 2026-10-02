# rackup-site

The public website for RackUp, served by GitHub Pages from `master` at
<https://getrackup.com/>. Plain HTML and CSS, no framework.
Anything merged to `master` goes live, so treat a merge as publishing.
The old `https://fpasxos.github.io/rackup-site/` addresses redirect to the same
path on `getrackup.com`, so links already in the app and on QR codes keep working.

| Path | What it is | Edited by |
|---|---|---|
| `index.html` | Greek home page, served at `/` | hand, except the `data-count` spans, the city grid and the store links |
| `en/index.html` | English home page, served at `/en/` | hand, likewise |
| `404.html` | Bilingual page GitHub Pages serves for any missing path (root-relative links only) | hand, except the store links |
| `support.html`, `privacy.html` | Support and privacy policy (store listings link here, so keep the URLs) | hand, except the store links in `support.html` |
| `mpiliardo/` | Greek hall directory: index plus one page per city | generator |
| `en/billiards/` | The same directory in English | generator |
| `sitemap.xml` | Every page on the site | generator |
| `m/` | Landing page for match links shared from the app (`noindex`, not in the sitemap) | hand |
| `go/` | Where printed QR codes point: sends phones to their app store with tagged links (`noindex`, not in the sitemap) | hand |
| `assets/site.css` | The one stylesheet: the app's Felt and Neon tokens and every component | hand |
| `assets/fonts/` | Self-hosted Space Grotesk, Hanken Grotesk (Latin) and Commissioner (Greek), with their OFL licences | `tools/make_fonts.py` |
| `assets/img/`, `assets/og-card.png` | App screenshots as WebP, and the 1200x630 social card | `tools/make_images.py` |
| `CNAME` | The custom domain, `getrackup.com`, that GitHub Pages serves the site on | hand |
| `data/venues.json` | Public copy of the venue directory | generator (`--import`) |
| `tools/build_directory.py` | The generator | hand |

## Regenerating the hall directory

Needs Python 3.8 or newer and nothing else. When venue data changes in the app
repo, run this from the root of this repo:

```bash
python tools/build_directory.py --import ../rackup/data/venues-backup.json
```

That refreshes `data/venues.json`, rewrites every page under `mpiliardo/` and
`en/billiards/`, rewrites `sitemap.xml`, updates the hall and city counts on the
home pages, fills the city grid on both homes, tags the store links on the hand
pages (`HAND_PAGES`), and removes
the folder of any city that no longer has a hall. Review
the diff, commit, and open a pull request.

Other modes:

```bash
python tools/build_directory.py           # rebuild from the committed data/venues.json
python tools/build_directory.py --check   # exit 1 if any generated page is out of date
python -m unittest discover -s tools      # generator and site tests, standard library only
```

The full check, run before every commit:

```bash
python tools/build_directory.py --check && python -m unittest discover -s tools && node --test tools/go_page.test.js && node --test tools/match_page.test.js
```

Never edit a generated page by hand; the next run overwrites it. Change the
template in the script instead.

To preview locally, serve the repo root and open `http://localhost:8000/`:

```bash
python -m http.server 8000
```

## Design

The site wears the app's "Felt and Neon" design: the colours in `assets/site.css`
are the tokens from `RackUpColors.kt`, one neon lime accent, dark only. Keep it
that way; `tools/test_site.py` fails on the old green and gold palette.

- **Fonts.** The app's fonts have no Greek, so Commissioner supplies Greek inside
  the same two families through `unicode-range`. Both faces of a family must
  declare the same `font-weight` range, or Chrome never uses the Greek one.
  `python tools/make_fonts.py` rebuilds the subsets (needs `pip install fonttools brotli`).
- **Images.** `python tools/make_images.py` rebuilds the WebP screenshots from the
  app repo's store screenshots (never `1-venues.png`, its hall count is stale) and,
  with `--og-card`, optimises the social card rendered from `tools/og-card.html`.
- **Checking a phone layout.** Headless Edge will not lay out narrower than 484 px,
  so load pages into a same-origin iframe of the width you want and compare
  `scrollWidth` with `clientWidth`.

## Rules the generator enforces

- **Only name, city, address, sort order, phone and website leave the app
  repo.** This repo is public, so `--import` drops coordinates, prices, hours,
  amenities and every other field, and the build refuses a `data/venues.json`
  that contains them.
- **No maps.** No embeds, no Google Maps links and no coordinates in pages or
  structured data. The venue data licence rules in the app repo's `CLAUDE.md`
  are the reason.
- **Nothing that is not in the data.** A phone or website appears only when the
  venue record has one, and copy promises phones only when every hall in the
  city has one. Each hall's structured data is a `SportsActivityLocation` (a
  `LocalBusiness` type) with only name, address, city, and phone or website
  when present; its `@id` is the hall's anchor on the Greek city page, the
  same in both languages.
- **Titles at most 60 characters, descriptions at most 155** (`TITLE_LIMIT`,
  `DESCRIPTION_LIMIT`). A one-hall title drops `| RackUp` before it passes 60;
  districts join a description only while it fits. `tools/test_directory_seo.py`
  checks every directory page, and that no two descriptions are the same.
- **Pool is «αμερικάνικο» in Greek, never «πουλ»**; carom is «γαλλικό»
  (τρίσποντο, μονόσποντο). The tests fail on «πουλ» on any Greek directory page.
- **Heads are frozen** in `tools/fixtures/directory-head.json`. Before
  re-capturing it after a deliberate change, run the tests: a copy change fails
  only `test_directory_pages_keep_their_seo_and_anchors`, while a moved canonical
  URL, hreflang alternate or hall anchor also fails
  `test_copy_changes_never_move_a_url_an_alternate_or_an_anchor` (as a venue
  import that adds or removes halls does, by design). Then
  `python tools/test_directory_design.py --capture` and read the diff.
- **A new city needs a line in `CITIES`** at the top of the script: its URL slug,
  Greek name and the Greek "in the city" phrase (`στη Θεσσαλονίκη`,
  `στον Βόλο`). The build stops and says so if one is missing, mirroring
  `GreekCity.kt` in the app.
- **No en or em dashes** in any generated page. The build stops if one appears.

## Store links on the site

Every Google Play link on the home page, the support page and the directory
carries a Play referrer, so installs from the site show up by page:
`&referrer=utm_source%3Dwebsite%26utm_medium%3Dorganic%26utm_campaign%3D<campaign>`.
The campaign comes from the page path: `home`, `support`, `el-directory`,
`en-directory`, `el-<city-slug>` and `en-<city-slug>`, lowercase letters, digits
and single hyphens, at most 26 characters. The generator writes all of them,
including the two links in the hand-written `index.html` and `support.html`
(`HAND_PAGES` in the script); a new hand-written page with store links goes there
too, or the tests fail. Nothing runs on the page: Play reads the referrer.

The App Store links stay plain until RackUp has a provider token. Then
`PROVIDER_TOKEN` in `tools/build_directory.py` takes the same `pt` as `go/go.js`
(a test keeps the two equal), a rebuild gives every page
`ct=web-<campaign>`, and the `web-` tells site installs apart from hall QR scans
in App Analytics. `tools/match_page.test.js` checks that the share page's App
Store link matches the home page's, so adjust it in the same change.

## Match share links

The Android app shares a match as `https://getrackup.com/m/?id=<matchId>` (builds that
still use the old github.io address reach the same page through the redirect).
Chat apps turn that into a tappable link with a preview, which a `rackup://` link never
got. `m/index.html` shows the preview tags and the store links; `m/open.js` checks the id
(letters, digits, `_` and `-`, at most 128) and, on Android only, adds an **Open in
RackUp** button pointing at
`intent://match/<id>#Intent;scheme=rackup;package=com.rackup.app;S.browser_fallback_url=...;end`.

- **The page must be live before any app build that shares these links**, or every
  shared match opens a 404.
- The button relies on the app's `rackup://match/{id}` intent filter. The app repo's
  `LaunchIntentOpensOnceTest` parses the same intent string, so change both together.
- The Google Play links carry `referrer=utm_source=share&utm_medium=match_link` so Play
  attributes installs that came from a shared match. Nothing on the page sets a cookie
  or loads a third party script, and its Content Security Policy only allows `open.js`.

Run the tests with Node 18 or newer, no packages needed:

```bash
node --test tools/match_page.test.js
```

## Store QR codes

Printed QR codes point at `https://getrackup.com/go/`, or
`go/?h=<hall-slug>` for a hall's own code (codes made before the move use the old
github.io address and arrive through the redirect). `go/go.js` sends iPhones and iPads to
the App Store and Android phones to Google Play, and shows the two store buttons
everywhere else. A hall slug is lowercase letters, digits and single hyphens, at
most 30 characters; anything else counts as the general code.

- The Play links and the tagged App Store links must match what the app repo's
  `store-assets/hall-links/hall_links.py` builds. `tools/go_page.test.js` pins
  them as literals, so change both together.
- `PROVIDER_TOKEN` in `go/go.js` is empty until the `pt` value from App Store
  Connect is pasted in. Until then every App Store link is the plain
  `https://apps.apple.com/gr/app/id6800614202`, with no campaign. Setting it
  also changes the static App Store `href` in `go/index.html`; the test checks.
- Ads and social bios add a source, `go/?s=<source>&h=<campaign>`, so their
  installs are not counted as hall scans. `s=meta` tags Play with
  `utm_source=meta&utm_medium=paid`, `s=ig` with `instagram` and `social`,
  `s=fb` with `facebook` and `social`; `h` is the campaign. Any other or repeated
  `s` is ignored. Apple's `ct` becomes `<source>-<campaign>`, or just the
  campaign when that would pass Apple's 30 character limit. These links are
  built only here, not by `hall_links.py`.

```bash
node --test tools/go_page.test.js
```

## Social profiles

Every footer links RackUp on Instagram and Facebook: the generator from `INSTAGRAM`
and `FACEBOOK` in `tools/build_directory.py`, the hand pages by hand. The home's
`Organization` lists both in `sameAs`; the store listings stay on the
`MobileApplication`. Plain links only, never an embed, a share widget or a pixel.
`tools/test_social_links.py` checks every page and the structured data.

## Search

Submit `https://getrackup.com/sitemap.xml` in Google Search Console, under a
Domain property for `getrackup.com` or a URL-prefix property for
`https://getrackup.com/`. With its own host the site could now carry a
`robots.txt` at the repo root; there is none yet.
