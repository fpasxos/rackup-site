# getrackup.com redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild every page of getrackup.com in the app's Felt and Neon style, Greek first, without breaking a URL, an SEO tag, a tracked store link or the share and QR scripts.

**Architecture:** Static GitHub Pages site. One stylesheet (`assets/site.css`) and self-hosted fonts replace `assets/style.css` and the privacy page's inline style. Hand-written pages (two homes, support, privacy, 404, go, m) share one header and footer markup; the generator (`tools/build_directory.py`) renders the directory pages with the same markup and keeps injecting counts, tagged store links and, new, a city grid into the homes.

**Tech Stack:** HTML, CSS, Python 3.8+ standard library (generator and tests), Node 18+ (JS tests), dev-only fonttools + brotli + Pillow, headless Edge for renders.

**Spec:** `docs/superpowers/specs/2026-10-02-getrackup-redesign-design.md`

## Global Constraints

- Work only in `C:\Users\Fanis\VibeCoding\rackup-site-redesign`, branch `redesign/felt-neon`. If the Edit/Write tools are refused there, edit with Bash (python or sed).
- Colours, verbatim: `--bg #0E1512`, `--surface #18221C`, `--surface-low #131C17`, `--surface-high #1E2A23`, `--ink #EAF2ED`, `--ink2 #B4C3BA`, `--muted #8A9C90`, `--faint #5E7268`, `--outline #28312C`, `--accent #C6F24E`, `--on-accent #0E1512`, `--good #3FD597`; balls `#101010 #F4C81E #2F6BE0 #C8453A #F4F4EE`. `theme-color` is `#0E1512`. The old `#0C3B2A` and `#FFC66E` must vanish.
- Fonts: families `"RackUp Display"` and `"RackUp Text"`; Latin faces Space Grotesk and Hanken Grotesk, Greek face Commissioner for both, split by `unicode-range`; `font-display: swap`.
- No request to another host, no cookies, no analytics, no inline `<style>` or `style=""` on go/ and m/ (their CSP), no `<img>` on go/.
- No en or em dash anywhere (U+2012 to U+2015). Code comments at most five lines.
- Copy claims only what the live store version does today (2.1.0). No platform-difference lists outside support.html.
- Privacy policy text stays word for word.
- Every existing id stays, notably `venue-*` on hall cards and every id the go/ and m/ scripts touch.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Full check, run before every commit: `python tools/build_directory.py --check && python -m unittest discover -s tools && node --test tools/go_page.test.js && node --test tools/match_page.test.js`. Read the counts; zero tests run is a failure.

## Review Focus

- Greek text silently falling back to a system font because a `unicode-range` or a font path is wrong. Pinned by `test_greek_and_latin_faces_cover_their_scripts` (Task 1) and the renders in Task 8.
- Horizontal scroll on 320 to 390 px phones (the mockup had it). Pinned by the scroll-width check in Task 8.
- Hall QR links (`#venue-<id>`) landing under the sticky header. Pinned by `test_anchors_clear_the_sticky_header` (Task 1).
- Support page anchors and the share/QR scripts' ids changing in the restyle. Pinned by `test_support_keeps_its_ids` (Task 5) and the existing JS tests (Task 6).
- Motion for people who asked for none. Pinned by `test_motion_stops_under_reduced_motion` (Task 1).

---

### Task 1: Fonts and the design system stylesheet

**Files:**
- Create: `assets/fonts/space-grotesk-latin.woff2`, `assets/fonts/hanken-grotesk-latin.woff2`, `assets/fonts/commissioner-greek.woff2`, `assets/fonts/OFL-SpaceGrotesk.txt`, `assets/fonts/OFL-HankenGrotesk.txt`, `assets/fonts/OFL-Commissioner.txt`
- Create: `assets/site.css`
- Create: `tools/test_site.py` (site-wide guards; this task adds the CSS ones)
- Create: `tools/make_fonts.py` (dev-only, documents the subsetting)

**Interfaces:**
- Produces, for every later task, this class contract in `site.css`:
  - Layout: `.container` (max 1180px, 20px gutters on phones), `.section`, `.section-head` (`.eyebrow`, `h2`, `.lead`), `.skip-link`, `.sr-only`, `.muted`, `.hl` (lime text)
  - Header: `header.site-header > .container.nav > a.wordmark` (`span.ball.b8` + `span.wm`: `RACK<span>UP</span>`), `nav.nav-links` (links, `a.lang`, `a.btn.btn-primary.btn-sm`)
  - Buttons: `.btn`, `.btn-primary`, `.btn-ghost`, `.btn-sm`, `.btn-store` (`svg.glyph` + `span` with `small` and the store name), `.stores`
  - Balls: `.ball` sized by `--s`, colours `.b8 .b9 .b10 .cr .cy .cw`, number `.n`
  - `.phone` (frame around `img`), `.phone-front`, `.phone-back`; `.toast` (`.toast-icon`, `b`, `span`); `.chip`, `.chips`; `.stats > .stat` (`b`, `span`); `.eyebrow` with `.live-dot`
  - `.steps > .step` (`.step-n`, `h3`, `p`); `.bento > .tile` (`.tile-wide`); `.city-grid` (`li > a > .city + .count`); `.halls > .hall` (`h2`, `.addr`, `.contact`); `.cta-band`; `.faq` (`details`, `summary`); `.crumbs`; `.prose` (privacy and support); `.share-card` (go and m); `.rack-bg`; `footer.site-footer`
- Font families `"RackUp Display"`, `"RackUp Text"` as in Global Constraints.

- [ ] **Step 1: Write the failing CSS guards in `tools/test_site.py`** (unittest, standard library only, reusing `published()` and `b.ROOT` from `test_build_directory` by import):
  - `test_greek_and_latin_faces_cover_their_scripts`: `site.css` has four `@font-face` blocks; for each family the Greek face's `unicode-range` contains `U+0370-03FF` and `U+1F00-1FFF` and points at `fonts/commissioner-greek.woff2`; the Latin faces point at the two Latin files; every `url(...)` in `site.css` resolves to an existing file.
  - `test_anchors_clear_the_sticky_header`: `site.css` sets `scroll-margin-top` on `[id]` (or on `.hall` and `section[id]`) to at least the header height.
  - `test_motion_stops_under_reduced_motion`: a `@media (prefers-reduced-motion: reduce)` block sets `animation: none` (or `animation-duration` near zero) for `*`.
  - `test_stylesheet_carries_the_app_palette`: every colour in Global Constraints appears in `site.css`; `#0C3B2A` and `#FFC66E` (any case) do not; file under 25 KB.
- [ ] **Step 2: Run** `python -m unittest tools.test_site -v` (from repo root, `cd tools` if imports need it). Expected: 4 failures, missing `site.css`.
- [ ] **Step 3: Fetch and subset the fonts** with `tools/make_fonts.py`: download `SpaceGrotesk[wght].ttf`, `HankenGrotesk[wght].ttf`, `Commissioner[FLAR,VOLM,slnt,wght].ttf` and each `OFL.txt` from `https://github.com/google/fonts/raw/main/ofl/<family>/`; pin Commissioner's FLAR, VOLM and slnt to their defaults with `fontTools.varLib.instancer`, keep `wght` 400 to 800; subset with `fontTools.subset` to Google's latin range (`U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD`) for the two Latin files and `U+0370-0377,U+037A-037F,U+0384-038A,U+038C,U+038E-03A1,U+03A3-03FF,U+1F00-1FFF` for Commissioner; flavor woff2. Dev install: `pip install fonttools brotli`. Expected: three woff2 files totalling under 140 KB.
- [ ] **Step 4: Write `assets/site.css`** to the class contract, matching direction A of `C:\Users\Fanis\AppData\Local\Temp\claude\C--Users-Fanis-VibeCoding-rackup\8b0d7cd7-fa2c-497f-8338-fb8f755901cb\scratchpad\mock\template.html` (lime glow, dot grid, phone tilt, glass toast, pill buttons) but mobile first, no horizontal overflow at 320 px, lime `:focus-visible` rings, sticky header with backdrop blur, the reduced-motion block, and `scroll-margin-top`.
- [ ] **Step 5: Run** the Task 1 tests. Expected: 4 passed. Run the full check: existing suites still pass (nothing links the new CSS yet).
- [ ] **Step 6: Commit** `assets/fonts assets/site.css tools/make_fonts.py tools/test_site.py` as "Design system: the app's Felt and Neon tokens, components and self-hosted fonts".

### Task 2: Images and the social card

**Files:**
- Create: `tools/make_images.py` (dev-only, Pillow)
- Create: `assets/img/{el,en}-{venue,create,welcome}-{360,720}.webp` (12 files)
- Create: `tools/og-card.html`, `assets/og-card.png` (1200x630)

**Interfaces:**
- Produces: image paths above, intrinsic size 360x783 at 1x (aspect 1320:2868), and `assets/og-card.png`.

- [ ] **Step 1: Write the failing test** `test_images_are_light_and_sized` in `tools/test_site.py`: the 12 WebP files exist, each under 60 KB, each 360 or 720 wide; `assets/og-card.png` is 1200x630 (read the PNG header with `struct`) and under 300 KB.
- [ ] **Step 2: Run it.** Expected: FAIL, files missing.
- [ ] **Step 3: Implement `tools/make_images.py`:** read `../rackup/store-assets/ios-screenshots/{el,en-GB}/{4-venue,2-create,5-welcome}.png` (path relative to the repo's parent folder), resize with LANCZOS to 360 and 720 wide, save WebP quality 80. Never use `1-venues.png` (it says 65 halls).
- [ ] **Step 4: Build the social card:** `tools/og-card.html` is a 1200x630 page using `../assets/site.css` and an `en-venue`-free layout: wordmark, "Βρες αντίπαλο. Παίξε απόψε.", "getrackup.com", the `el-venue-720.webp` phone over the lime glow. Render with `msedge --headless=new --hide-scrollbars --window-size=1200,630 --screenshot=assets\og-card.png file:///.../tools/og-card.html`, then optimise with Pillow (`optimize=True`).
- [ ] **Step 5: Run** the test and the full check. Expected: pass.
- [ ] **Step 6: Commit** as "Screenshots as WebP and a 1200x630 social card".

### Task 3: The two homes and the generator hooks they need

**Files:**
- Modify: `index.html` (becomes Greek), Create: `en/index.html` (English)
- Modify: `tools/build_directory.py` (`HAND_PAGES`, `campaign_for`, `home_with_counts`, new `city_grid`, `sitemap`)
- Modify: `tools/test_build_directory.py`, `tools/test_site.py`

**Interfaces:**
- Consumes: Task 1 classes, Task 2 images and `assets/og-card.png`.
- Produces:
  - `HAND_PAGES = {"index.html": "", "en/index.html": "en/", "support.html": "support.html", "404.html": "404.html"}` (404 joins in Task 7; add it there, not here, if this task lands first).
  - `HOMES = {"index.html": "el", "en/index.html": "en"}`
  - `campaign_for("en/") -> "en-home"` (everything else unchanged).
  - `city_grid(cities: dict, lang: str) -> str`: `<ul class="city-grid">`, one `<li><a href="{href}"><span class="city">{name}</span> <span class="count">{count}</span></a></li>` per city in `city_order(cities, lang)`; `href` is `mpiliardo/{slug}/` for `el` and `billiards/{slug}/` for `en` (each relative to its own home); `count` uses `plural_el`/`plural_en`.
  - `home_with_city_grid(text: str, cities: dict, lang: str) -> str`: replaces whatever sits between `<!-- city-grid -->` and `<!-- /city-grid -->` with `city_grid(cities, lang)`; `sys.exit` if either marker is missing. `render()` applies it, and `home_with_counts`, to every key of `HOMES`. Both homes keep the two `data-count` spans; `home_with_counts` runs on every key of `HOMES`.
  - `sitemap()` lists `en/` after `""`.

- [ ] **Step 1: Write the failing tests.** In `test_build_directory.py`: `test_english_home_has_its_own_campaign` (`campaign_for("en/") == "en-home"`, `campaign_for("") == "home"`); `test_both_homes_get_counts_and_the_city_grid` (render both, each has the totals from `data/venues.json` and one `<a>` per city pointing at an existing generated page); `test_home_without_city_grid_markers_is_refused` (feed `home_with_city_grid` text without markers, expect `SystemExit`). In `test_site.py`: `test_homes_are_an_hreflang_pair` (`/` is `lang="el"` with canonical `https://getrackup.com/`, alternates el `/`, en `/en/`, x-default `/`; `/en/` mirrors it with `lang="en"`); `test_every_image_has_alt_and_size` (every `<img>` on every published page has non-empty `alt`, `width`, `height`).
- [ ] **Step 2: Run them.** Expected: FAIL.
- [ ] **Step 3: Generator changes** as in Interfaces.
- [ ] **Step 4: Write `index.html` (Greek) and `en/index.html` (English)** to the spec's eight home sections, with the exact Greek hero copy: H1 `Βρες αντίπαλο. <span class="hl">Παίξε απόψε.</span>`; English H1 `Find an opponent. <span class="hl">Play tonight.</span>`. Head: title, description, canonical, three hreflang alternates, og (image `https://getrackup.com/assets/og-card.png`, 1200x630), `theme-color #0E1512`, icons, `<link rel="preload" as="font" type="font/woff2" crossorigin href="assets/fonts/commissioner-greek.woff2">` (English home preloads `../assets/fonts/space-grotesk-latin.woff2`), `assets/site.css`, `FAQPage` JSON-LD whose answers equal the visible FAQ text. Hero phones: front `el-venue`, back `el-create`, `srcset` 360w and 720w, front `fetchpriority="high"`, back and below-fold `loading="lazy"`. No `<script>` other than JSON-LD. Features only from Global Constraints' "today" rule: feed and Play Now, host picks who plays and open challenges by tier, scores, streaks, leaderboards and badges, reliability with block and report, pool and carom.
- [ ] **Step 5: Run the generator,** then the full check. Expected: all pass, `--check` clean.
- [ ] **Step 6: Commit** as "Greek home at /, English home at /en/, city grid from the generator".

### Task 4: Directory and city pages from the generator

**Files:**
- Modify: `tools/build_directory.py` (`page`, `index_page`, `city_page`, `hall_item`, `stores`)
- Regenerate: `mpiliardo/**/index.html`, `en/billiards/**/index.html`, `sitemap.xml`
- Modify: `tools/test_build_directory.py`

**Interfaces:**
- Consumes: Task 1 classes and the header/footer markup Task 3 wrote (copy it exactly; only `prefix` and language differ).
- Produces: `stores(lang, campaign)` emits `.stores` with two `.btn-store` links (lime App Store, ghost Google Play) and the same hrefs as today.

- [ ] **Step 1: Write the failing test** `test_directory_pages_keep_their_seo_and_anchors`: for every generated page, the `<title>`, meta description, canonical, three hreflang links and the JSON-LD text are byte-identical to `git show HEAD:<path>` taken before this task (capture them into the test as a fixture file `tools/fixtures/directory-head.json` in Step 1), and every `venue-*` id still exists; plus `site.css` is the only stylesheet.
- [ ] **Step 2: Run it.** Expected: FAIL on the stylesheet assertion only.
- [ ] **Step 3: Rewrite the templates** to the spec's "Other pages" bullet: hero band with city name and count, `.halls` cards, `.cta-band` with store buttons and a small `el-welcome`/`en-welcome` phone, other cities as `.chips`, `.crumbs`. `og:image` becomes `https://getrackup.com/assets/og-card.png` and `theme-color` `#0E1512`; neither is in the frozen fixture.
- [ ] **Step 4: Run the generator and the full check.** Expected: all pass.
- [ ] **Step 5: Commit** as "Directory and city pages in the new design, same head and anchors".

### Task 5: Support and privacy

**Files:**
- Modify: `support.html`, `privacy.html`
- Modify: `tools/test_site.py`

**Interfaces:**
- Consumes: Task 1 classes (`.prose`), the shared header and footer from Task 3.

- [ ] **Step 1: Write the failing tests:** `test_privacy_text_is_unchanged` (visible text of `<main>` with tags stripped and whitespace collapsed equals the same from `git show 210b04f:privacy.html`); `test_support_keeps_its_ids` (the set of `id="..."` values in support.html contains every id of `git show 210b04f:support.html`); `test_no_inline_style_blocks` (no `<style>` in any published page).
- [ ] **Step 2: Run them.** Expected: `test_no_inline_style_blocks` fails on privacy.html.
- [ ] **Step 3: Restyle both pages:** shared header and footer, `.prose` body, `assets/site.css`, `theme-color #0E1512`; remove the inline style and the emoji headings; text otherwise untouched.
- [ ] **Step 4: Run the generator (support.html is a hand page) and the full check.** Expected: pass.
- [ ] **Step 5: Commit** as "Support and privacy in the new design, text unchanged".

### Task 6: The share and QR pages (m/ and go/)

**Files:**
- Modify: `m/index.html`, `go/index.html`, `tools/go_page.test.js`, `tools/match_page.test.js`

**Interfaces:**
- Consumes: Task 1 classes (`.share-card`, `.ball`, `.btn-store`).

- [ ] **Step 1: Write the failing test changes:** in both JS test files assert the CSP equals exactly `default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'`, and that the page links `../assets/site.css`.
- [ ] **Step 2: Run** both node suites. Expected: those two assertions fail.
- [ ] **Step 3: Restyle both pages** into a centred `.share-card` with the CSS ball row, keeping every id, `hidden` attribute, heading text, store href and script tag exactly; add `font-src 'self'` to both CSPs; `theme-color #0E1512`; og image `https://getrackup.com/assets/og-card.png`. No `<img>` on go/.
- [ ] **Step 4: Run the full check.** Expected: pass.
- [ ] **Step 5: Commit** as "Share and QR pages in the new design; fonts allowed by their CSP".

### Task 7: 404 page

**Files:**
- Create: `404.html`; Modify: `tools/build_directory.py` (`HAND_PAGES` gains `"404.html": "404.html"`), `tools/test_site.py`

- [ ] **Step 1: Write the failing test** `test_not_found_page_helps`: `404.html` exists, is `noindex`, links `/`, `/en/` and `/mpiliardo/` with root-relative hrefs (it is served at any depth), and its assets use root-relative paths (`/assets/...`).
- [ ] **Step 2: Run it.** Expected: FAIL.
- [ ] **Step 3: Write `404.html`:** bilingual `.share-card`, "Αυτή η σελίδα δεν υπάρχει" / "This page does not exist", buttons home and directory, store buttons (so it joins `HAND_PAGES` with campaign `404`).
- [ ] **Step 4: Run the generator and the full check.** Expected: pass.
- [ ] **Step 5: Commit** as "A bilingual 404 page".

### Task 8: Site-wide guards, cleanup, visual and Lighthouse checks

**Files:**
- Modify: `tools/test_site.py`, `README.md`; Delete: `assets/style.css`

- [ ] **Step 1: Write the final guards:** `test_one_stylesheet_everywhere` (every published page links exactly one stylesheet, `site.css`, at the right relative depth); `test_old_palette_is_gone` (no `#0C3B2A`/`#FFC66E` in any published file); `test_internal_links_resolve` (every relative or root-relative `href`/`src` on every published page resolves to a file or a folder with `index.html`, ignoring `#fragment` and `?query`); `test_every_page_has_the_shared_header_and_footer`.
- [ ] **Step 2: Run them, delete `assets/style.css`, run again.** Expected: pass with style.css gone.
- [ ] **Step 3: Visual pass:** serve the worktree with `python -m http.server 8765`; in the built-in browser render `/`, `/en/`, `/mpiliardo/`, `/mpiliardo/athens/`, `/en/billiards/patras/`, `/support.html`, `/privacy.html`, `/go/`, `/m/?id=abc`, `/404.html` at 320, 390, 768 and 1280 wide; on each, `document.documentElement.scrollWidth <= innerWidth` must be true; save screenshots to the session scratchpad.
- [ ] **Step 4: Lighthouse** (chrome-devtools MCP `lighthouse_audit`, mobile) on `/` and `/mpiliardo/athens/`. Expected: 95 or more in performance, accessibility, best practices and SEO; fix and repeat below that.
- [ ] **Step 5: README:** new assets, `make_fonts.py`, `make_images.py`, `test_site.py`, and the full check command.
- [ ] **Step 6: Commit** as "Site-wide guards, README, and the old stylesheet removed".

### Task 9: Pull request

- [ ] **Step 1:** Push `redesign/felt-neon` and open a PR on fpasxos/rackup-site with the test counts, the Lighthouse scores and the screenshot list; body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. Do not merge.
- [ ] **Step 2:** Tell the "Google Ads plan for rack app" session the PR exists and touches `tools/build_directory.py`.
- [ ] **Step 3:** Send Fanis the screenshots; merge only on his yes, then curl `/`, `/en/`, `/mpiliardo/athens/`, `/go/?s=fb&h=page`, `/m/?id=abc`, `/privacy.html` and a missing path for 200/404 and the new `theme-color`.
