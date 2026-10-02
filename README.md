# rackup-site

The public website for RackUp, served by GitHub Pages from `master` at
<https://getrackup.com/>. Plain HTML and CSS, no framework.
Anything merged to `master` goes live, so treat a merge as publishing.
The old `https://fpasxos.github.io/rackup-site/` addresses redirect to the same
path on `getrackup.com`, so links already in the app and on QR codes keep working.

| Path | What it is | Edited by |
|---|---|---|
| `index.html` | English home page | hand, except the two `data-count` spans |
| `support.html`, `privacy.html` | Support and privacy policy (store listings link here, so keep the URLs) | hand |
| `mpiliardo/` | Greek hall directory: index plus one page per city | generator |
| `en/billiards/` | The same directory in English | generator |
| `sitemap.xml` | Every page on the site | generator |
| `m/` | Landing page for match links shared from the app (`noindex`, not in the sitemap) | hand |
| `go/` | Where printed QR codes point: sends phones to their app store with tagged links (`noindex`, not in the sitemap) | hand |
| `assets/` | Shared stylesheet and the app icon | hand |
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
home page, and removes the folder of any city that no longer has a hall. Review
the diff, commit, and open a pull request.

Other modes:

```bash
python tools/build_directory.py           # rebuild from the committed data/venues.json
python tools/build_directory.py --check   # exit 1 if any generated page is out of date
python -m unittest discover -s tools      # generator tests, standard library only
```

Never edit a generated page by hand; the next run overwrites it. Change the
template in the script instead.

To preview locally, serve the repo root and open `http://localhost:8000/`:

```bash
python -m http.server 8000
```

## Rules the generator enforces

- **Only name, city, address, sort order, phone and website leave the app
  repo.** This repo is public, so `--import` drops coordinates, prices, hours,
  amenities and every other field, and the build refuses a `data/venues.json`
  that contains them.
- **No maps.** No embeds, no Google Maps links and no coordinates in pages or
  structured data. The venue data licence rules in the app repo's `CLAUDE.md`
  are the reason.
- **Nothing that is not in the data.** A phone or website appears only when the
  venue record has one. `LocalBusiness` structured data carries only name,
  address, city, and phone or website when present.
- **A new city needs a line in `CITIES`** at the top of the script: its URL slug,
  Greek name and the Greek "in the city" phrase (`στη Θεσσαλονίκη`,
  `στον Βόλο`). The build stops and says so if one is missing, mirroring
  `GreekCity.kt` in the app.
- **No en or em dashes** in any generated page. The build stops if one appears.

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

## Search

Submit `https://getrackup.com/sitemap.xml` in Google Search Console, under a
Domain property for `getrackup.com` or a URL-prefix property for
`https://getrackup.com/`. With its own host the site could now carry a
`robots.txt` at the repo root; there is none yet.
