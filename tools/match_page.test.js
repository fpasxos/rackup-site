// Tests for the match share page (m/index.html, m/open.js).
// Node 18 or newer, no packages: node --test tools/match_page.test.js
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const read = (file) => fs.readFileSync(path.join(ROOT, file), "utf8");
const page = require(path.join(ROOT, "m", "open.js"));
const HALLS = require(path.join(ROOT, "m", "halls.js"));
const html = read("m/index.html");

const AUTO_ID = "Xy12abCDef34GhIjKl56";
const ANDROID_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/128.0 Mobile Safari/537.36";
const IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1";
const DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36";

// The literal the app repo's LaunchIntentOpensOnceTest parses; change both together.
const EXPECTED_INTENT = "intent://match/Xy12ab_CD-ef#Intent;scheme=rackup;package=com.rackup.app;" +
  "S.browser_fallback_url=https%3A%2F%2Fplay.google.com%2Fstore%2Fapps%2Fdetails%3Fid%3Dcom.rackup.app" +
  "%26referrer%3Dutm_source%253Dshare%2526utm_medium%253Dmatch_link;end";

const GAME_IDS = ["game", "game-note", "game-what", "game-what-en", "game-when", "game-when-en", "game-hall", "game-city",
  "game-where-en"];

function fakeDocument() {
  const elements = {};
  for (const id of ["android", "open-app", "bad-link", "app-store", "google-play", "stores-note", "note-android", "note-ios",
    ...GAME_IDS]) {
    elements[id] = {
      hidden: !["app-store", "google-play", "stores-note"].includes(id), attributes: {}, textContent: "",
      setAttribute(k, v) { this.attributes[k] = v; }
    };
  }
  return { elements, getElementById: (id) => elements[id] };
}

// What app 2.4.8 shares for a 9-Ball race to 5 at ManCave on Sunday 15 November 2026, 21:00.
const DETAILS = `?id=${"Xy12abCDef34GhIjKl56"}&g=NINE_BALL&r=5&t=202611152100&v=venue-koz-mancave`;

function shown(search, ua = IPHONE_UA) {
  const doc = fakeDocument();
  page.wire(doc, ua, search, HALLS);
  return doc.elements;
}

test("a Firestore auto id and the full allowed alphabet are accepted", () => {
  assert.equal(page.matchIdFrom(`?id=${AUTO_ID}`), AUTO_ID);
  assert.equal(page.matchIdFrom("?id=a_B-9"), "a_B-9");
  assert.equal(page.matchIdFrom(`?id=${"a".repeat(128)}`), "a".repeat(128));
});

test("ids that could break out of an href or change the intent are rejected", () => {
  const hostile = [
    "", "a".repeat(129), "abc;end", "abc#Intent", "abc/../x", "a b", "a\"b", "a'b", "a<b",
    "javascript:alert(1)", "a%2Fb", "abc%0A", "ματς", "a.b", "a&b"
  ];
  for (const id of hostile) {
    assert.equal(page.matchIdFrom(`?id=${encodeURIComponent(id)}`), null, `accepted ${JSON.stringify(id)}`);
    assert.equal(page.isValidMatchId(id), false, `valid ${JSON.stringify(id)}`);
  }
  assert.equal(page.matchIdFrom(""), null);
  assert.equal(page.matchIdFrom("?match=abc"), null);
  assert.equal(page.matchIdFrom("?id=abc%0A"), null, "a trailing newline must not pass");
});

test("the intent url opens rackup match links in the RackUp package", () => {
  assert.equal(page.intentUrl("Xy12ab_CD-ef"), EXPECTED_INTENT);
});

test("the fallback decodes once to the Play listing with the share referrer", () => {
  const fallback = page.intentUrl(AUTO_ID).match(/;S\.browser_fallback_url=([^;]*);end$/)[1];
  const play = new URL(decodeURIComponent(fallback));
  assert.equal(play.origin + play.pathname, "https://play.google.com/store/apps/details");
  assert.equal(play.searchParams.get("id"), "com.rackup.app");
  assert.equal(play.searchParams.get("referrer"), "utm_source=share&utm_medium=match_link");
});

test("building an intent for an invalid id throws instead of emitting it", () => {
  assert.throws(() => page.intentUrl("x;end;S.evil=1"));
  assert.throws(() => page.intentUrl(null));
});

test("only Android user agents count as Android", () => {
  assert.equal(page.isAndroid(ANDROID_UA), true);
  assert.equal(page.isAndroid(IPHONE_UA), false);
  assert.equal(page.isAndroid(DESKTOP_UA), false);
  assert.equal(page.isAndroid(undefined), false);
});

test("on Android with a valid id the open button appears with the intent url", () => {
  const doc = fakeDocument();
  page.wire(doc, ANDROID_UA, "?id=Xy12ab_CD-ef");
  assert.equal(doc.elements.android.hidden, false);
  assert.equal(doc.elements["open-app"].attributes.href, EXPECTED_INTENT);
  assert.equal(doc.elements["bad-link"].hidden, true);
});

test("off Android the open button stays hidden and has no href", () => {
  for (const ua of [IPHONE_UA, DESKTOP_UA]) {
    const doc = fakeDocument();
    page.wire(doc, ua, `?id=${AUTO_ID}`);
    assert.equal(doc.elements.android.hidden, true);
    assert.equal(doc.elements["open-app"].attributes.href, undefined);
    assert.equal(doc.elements["bad-link"].hidden, true);
  }
});

test("a hostile id on Android shows the bad link note and never sets an href", () => {
  const doc = fakeDocument();
  page.wire(doc, ANDROID_UA, "?id=" + encodeURIComponent("x\" onclick=\"alert(1)"));
  assert.equal(doc.elements.android.hidden, true);
  assert.equal(doc.elements["open-app"].attributes.href, undefined);
  assert.equal(doc.elements["bad-link"].hidden, false);
});

test("the page is noindex, previews well and loads no script but its own", () => {
  assert.match(html, /<meta name="robots" content="noindex">/);
  for (const property of ["og:title", "og:description", "og:image", "og:url"]) {
    assert.match(html, new RegExp(`<meta property="${property}" content="[^"]+">`), property);
  }
  assert.match(html, /<meta name="twitter:card" content="summary_large_image">/);
  assert.match(html, /<meta property="og:image" content="https:\/\/getrackup\.com\/assets\/og-card-2026-11-12\.png">/);
  const image = html.match(/property="og:image" content="https:\/\/getrackup\.com\/([^"]+)"/)[1];
  assert.ok(fs.existsSync(path.join(ROOT, image)), `og:image ${image} is not in the repo`);
  const scripts = [...html.matchAll(/<script\b[^>]*>/g)].map((m) => m[0]);
  // The halls first: deferred scripts run in order, and open.js names a hall from them.
  assert.deepEqual(scripts, ['<script src="halls.js" defer>', '<script src="open.js" defer>']);
  assert.match(html, /script-src 'self'/);
});

test("the Content Security Policy allows only this site, fonts included", () => {
  const csp = html.match(/http-equiv="Content-Security-Policy" content="([^"]+)"/)[1];
  assert.equal(csp, "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; " +
    "font-src 'self'; base-uri 'none'; form-action 'none'");
});

test("the page is styled by the site stylesheet and nothing else", () => {
  const sheets = [...html.matchAll(/<link\b[^>]*rel="stylesheet"[^>]*>/g)].map((m) => m[0]);
  assert.deepEqual(sheets, ['<link rel="stylesheet" href="../assets/site.css">']);
});

test("every element the script touches exists and starts hidden", () => {
  for (const id of GAME_IDS) assert.match(html, new RegExp(`id="${id}"`), id);
  for (const id of ["android", "bad-link", "game", "game-note"]) {
    assert.match(html, new RegExp(`id="${id}"[^>]*\\bhidden\\b`), id);
  }
  assert.match(html, /<a id="open-app"(?![^>]*href)[^>]*>/, "open-app must have no href until the script sets one");
});

test("the static store links match the script and the home page", () => {
  const unescape = (s) => s.replace(/&amp;/g, "&");
  const playHref = unescape(html.match(/id="google-play" href="([^"]+)"/)[1]);
  assert.equal(playHref, page.PLAY_URL);
  const appStoreHref = unescape(html.match(/id="app-store" href="([^"]+)"/)[1]);
  // Share installs carry ct=share under the same pt as go/go.js, mirroring the Play referrer.
  const token = read("go/go.js").match(/var PROVIDER_TOKEN = "([^"]*)"/)[1];
  // /gr/ is the only storefront with RackUp; without it the link is a 404 on a computer.
  assert.equal(appStoreHref, `https://apps.apple.com/gr/app/apple-store/id6800614202?pt=${token}&ct=share&mt=8`);
  for (const url of html.match(/apps\.apple\.com[^\s"'<>]*/g)) {
    assert.ok(url.startsWith("apps.apple.com/gr/app/"), `${url} names no storefront`);
  }
});

test("the page stays out of the sitemap, is published, and has no en or em dash", () => {
  assert.ok(!read("sitemap.xml").includes("/m/"), "sitemap.xml lists the share page");
  const excluded = read("_config.yml").split("\n").map((l) => l.trim()).filter((l) => l.startsWith("- "));
  assert.ok(!excluded.some((l) => /^- m\/?$/.test(l)), "_config.yml excludes m/");
  const dashes = /[\u2012\u2013\u2014\u2015]/;
  assert.ok(!dashes.test(html), "m/index.html has a dash");
  assert.ok(!dashes.test(read("m/open.js")), "m/open.js has a dash");
});

test("a phone sees only its own store and one line; a desktop keeps both buttons", () => {
  const cases = [
    [ANDROID_UA, "app-store", "note-android"],
    [IPHONE_UA, "google-play", "note-ios"]
  ];
  for (const [ua, hiddenStore, note] of cases) {
    const doc = fakeDocument();
    page.wire(doc, ua, `?id=${AUTO_ID}`);
    assert.equal(doc.elements[hiddenStore].hidden, true, hiddenStore);
    assert.equal(doc.elements[note].hidden, false, note);
    assert.equal(doc.elements["stores-note"].hidden, true);
  }
  const doc = fakeDocument();
  page.wire(doc, DESKTOP_UA, `?id=${AUTO_ID}`);
  assert.equal(doc.elements["app-store"].hidden, false);
  assert.equal(doc.elements["google-play"].hidden, false);
  assert.equal(doc.elements["note-android"].hidden, true);
  assert.equal(doc.elements["note-ios"].hidden, true);
  for (const id of ["note-android", "note-ios", "stores-note"]) assert.match(html, new RegExp(`id="${id}"`));
});

// The test above sets .hidden on a fake document; a browser still drew the other store's
// button, because .btn sets display and an author rule beats the hidden attribute's.
test("the hidden attribute wins over the button styles, so a phone's other store really goes", () => {
  const css = read("assets/site.css");
  assert.match(css, /\[hidden\]\s*\{\s*display\s*:\s*none\s*!important\s*;?\s*\}/);
  for (const id of ["app-store", "google-play"]) {
    const classes = html.match(new RegExp(`<a class="([^"]+)" id="${id}"`))[1].split(/\s+/);
    assert.ok(classes.includes("btn"), `${id} is no longer a .btn; recheck what hides it`);
  }
  assert.match(css, /\.btn\{display:inline-flex/);
});

test("an Android visitor is told once that Google Play opens, not twice", () => {
  const androidBlock = html.match(/<div id="android" hidden>([\s\S]*?)<\/div>/)[1];
  const noteAndroid = html.match(/<p class="note" id="note-android" hidden>([\s\S]*?)<\/p>/)[1];
  assert.match(androidBlock, /Google Play/);
  assert.doesNotMatch(noteAndroid, /Google Play/);
  assert.match(noteAndroid, /πάτα ξανά τον σύνδεσμο/);
  assert.match(noteAndroid, /tap the link again/);
});

test("a 2.4.8 link shows the game, its time at the hall and the hall, as sent", () => {
  const el = shown(DETAILS);
  assert.equal(el.game.hidden, false);
  assert.equal(el["game-note"].hidden, false);
  assert.equal(el["game-what"].textContent, "9-Ball · Race στα 5");
  assert.equal(el["game-what-en"].textContent, "9-Ball · Race to 5");
  assert.equal(el["game-when"].textContent, "Κυριακή 15 Νοεμβρίου, 21:00");
  assert.equal(el["game-when-en"].textContent, "Sunday 15 November, 21:00");
  assert.equal(el["game-hall"].textContent, "ManCave");
  assert.equal(el["game-hall"].attributes.href, "../mpiliardo/kozani/#venue-koz-mancave");
  assert.equal(el["game-city"].textContent, ", Κοζάνη");
  assert.equal(el["game-where-en"].textContent, "ManCave, Kozani");
  assert.equal(el["bad-link"].hidden, true);
});

test("on Android the details come with the open button", () => {
  const el = shown(DETAILS, ANDROID_UA);
  assert.equal(el.game.hidden, false);
  assert.equal(el.android.hidden, false);
  assert.match(el["open-app"].attributes.href, /^intent:\/\/match\/Xy12abCDef34GhIjKl56#/);
});

test("carom counts points, and a game posted with no race shows the game alone", () => {
  const carom = shown("?id=a&g=THREE_CUSHION&r=30&t=202611152100&v=venue-cy-lim-century");
  assert.equal(carom["game-what"].textContent, "3-Cushion · Στους 30 πόντους");
  assert.equal(carom["game-what-en"].textContent, "3-Cushion · To 30 points");
  assert.equal(carom["game-where-en"].textContent, "Century House of Billiards, Limassol");
  assert.equal(carom["game-hall"].attributes.href, "../mpiliardo/lemesos/#venue-cy-lim-century");
  for (const race of ["", "&r=0", "&r=1000", "&r=5a", "&r=-3", "&r=05"]) {
    const el = shown(`?id=a&g=EIGHT_BALL${race}&t=202611152100&v=venue-koz-mancave`);
    assert.equal(el["game-what"].textContent, "8-Ball", race);
    assert.equal(el.game.hidden, false, race);
  }
});

test("a link from an older app, or one with a detail that is not sound, shows the page as before", () => {
  const broken = [
    "?id=a",
    "?id=a&g=NINE_BALL&t=202611152100",
    "?id=a&t=202611152100&v=venue-koz-mancave",
    "?id=a&g=NINE_BALL&v=venue-koz-mancave",
    "?id=a&g=SNOOKER&t=202611152100&v=venue-koz-mancave",
    "?id=a&g=nine_ball&t=202611152100&v=venue-koz-mancave",
    "?id=a&g=toString&t=202611152100&v=venue-koz-mancave",
    "?id=a&g=NINE_BALL&t=202611312100&v=venue-koz-mancave",
    "?id=a&g=NINE_BALL&t=202702291200&v=venue-koz-mancave",
    "?id=a&g=NINE_BALL&t=202611152500&v=venue-koz-mancave",
    "?id=a&g=NINE_BALL&t=202611152160&v=venue-koz-mancave",
    "?id=a&g=NINE_BALL&t=2026-11-15T21:00&v=venue-koz-mancave",
    "?id=a&g=NINE_BALL&t=202611152100&v=venue-nowhere",
    "?id=a&g=NINE_BALL&t=202611152100&v=constructor",
    "?id=a&g=NINE_BALL&t=202611152100&v=" + encodeURIComponent("<img src=x onerror=alert(1)>")
  ];
  for (const search of broken) {
    const el = shown(search);
    assert.equal(el.game.hidden, true, search);
    assert.equal(el["game-note"].hidden, true, search);
    assert.equal(el["game-hall"].textContent, "", search);
    assert.equal(el["game-hall"].attributes.href, undefined, search);
  }
  // A bad id shows the bad link note and no details, whatever else the link says.
  const bad = shown("?id=a;b&g=NINE_BALL&t=202611152100&v=venue-koz-mancave");
  assert.equal(bad["bad-link"].hidden, false);
  assert.equal(bad.game.hidden, true);
});

test("a leap day is a day, and the start is the time at the hall, not the reader's", () => {
  assert.deepEqual(page.startFrom("202802291930"), { year: 2028, month: 2, day: 29, hour: 19, minute: 30, weekday: 2 });
  assert.equal(page.startFrom("202702291930"), null);
  assert.equal(page.whenText(page.startFrom("202701020905"), "el"), "Σάββατο 2 Ιανουαρίου, 09:05");
  assert.equal(page.whenText(page.startFrom("202705030000"), "en"), "Monday 3 May, 00:00");
  assert.equal(page.whenText(page.startFrom("202705030000"), "el"), "Δευτέρα 3 Μαΐου, 00:00");
});

test("the hall's name and city come from the directory, never from the link", () => {
  const el = shown(DETAILS + "&name=" + encodeURIComponent("Call 6900000000") + "&h=Fake");
  assert.equal(el["game-hall"].textContent, "ManCave");
  for (const id of GAME_IDS) assert.ok(!/6900000000|Fake/.test(el[id].textContent || ""), id);
  const source = read("m/open.js");
  assert.doesNotMatch(source, /innerHTML|outerHTML|insertAdjacentHTML|document\.write/);
});

test("every game the app can share has the app's own words", () => {
  // The app's GameType names, as its MatchLinkDetailsTest pins them; change both together.
  assert.deepEqual(Object.keys(page.GAMES), ["EIGHT_BALL", "NINE_BALL", "TEN_BALL", "THREE_CUSHION", "ONE_CUSHION"]);
  assert.deepEqual(Object.values(page.GAMES).map((g) => g.label), ["8-Ball", "9-Ball", "10-Ball", "3-Cushion", "1-Cushion"]);
});

test("the halls the page can name are the directory's, with each one's city", () => {
  const venues = JSON.parse(read("data/venues.json"));
  assert.deepEqual(Object.keys(HALLS).sort(), venues.map((v) => v.id).sort());
  for (const v of venues) {
    const [name, cityEl, cityEn, slug] = HALLS[v.id];
    assert.equal(name, v.name, v.id);
    assert.equal(cityEn, v.city, v.id);
    assert.ok(fs.existsSync(path.join(ROOT, "mpiliardo", slug, "index.html")), `${v.id}: no page for ${slug}`);
    assert.ok(read(`mpiliardo/${slug}/index.html`).includes(`id="${v.id}"`), `${v.id} is not anchored on its page`);
    assert.match(cityEl, /[\u0370-\u03FF]/, v.id);
  }
});
