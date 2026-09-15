# rackup-site

The public website for RackUp, served by GitHub Pages from `master` at
<https://fpasxos.github.io/rackup-site/>. Plain HTML and CSS, no framework.
Anything merged to `master` goes live, so treat a merge as publishing.

| Path | What it is | Edited by |
|---|---|---|
| `index.html` | English home page | hand, except the two `data-count` spans |
| `support.html`, `privacy.html` | Support and privacy policy (store listings link here, so keep the URLs) | hand |
| `mpiliardo/` | Greek hall directory: index plus one page per city | generator |
| `en/billiards/` | The same directory in English | generator |
| `sitemap.xml` | Every page on the site | generator |
| `assets/` | Shared stylesheet and the app icon | hand |
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

## Search

`robots.txt` is only read at the root of a host, which for a project site is
`fpasxos.github.io`, not this repo. Submit `sitemap.xml` in Google Search
Console instead, under a URL-prefix property for
`https://fpasxos.github.io/rackup-site/`.
