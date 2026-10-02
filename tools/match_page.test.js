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
const html = read("m/index.html");

const AUTO_ID = "Xy12abCDef34GhIjKl56";
const ANDROID_UA = "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/128.0 Mobile Safari/537.36";
const IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1";
const DESKTOP_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0 Safari/537.36";

// The literal the app repo's LaunchIntentOpensOnceTest parses; change both together.
const EXPECTED_INTENT = "intent://match/Xy12ab_CD-ef#Intent;scheme=rackup;package=com.rackup.app;" +
  "S.browser_fallback_url=https%3A%2F%2Fplay.google.com%2Fstore%2Fapps%2Fdetails%3Fid%3Dcom.rackup.app" +
  "%26referrer%3Dutm_source%253Dshare%2526utm_medium%253Dmatch_link;end";

function fakeDocument() {
  const elements = {};
  for (const id of ["android", "open-app", "bad-link"]) {
    elements[id] = { hidden: true, attributes: {}, setAttribute(k, v) { this.attributes[k] = v; } };
  }
  return { elements, getElementById: (id) => elements[id] };
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
  assert.match(html, /<meta name="twitter:card" content="summary">/);
  const image = html.match(/property="og:image" content="https:\/\/getrackup\.com\/([^"]+)"/)[1];
  assert.ok(fs.existsSync(path.join(ROOT, image)), `og:image ${image} is not in the repo`);
  const scripts = [...html.matchAll(/<script\b[^>]*>/g)].map((m) => m[0]);
  assert.deepEqual(scripts, ['<script src="open.js" defer>']);
  assert.match(html, /script-src 'self'/);
});

test("every element the script touches exists and starts hidden", () => {
  for (const id of ["android", "bad-link"]) {
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
  assert.equal(appStoreHref, `https://apps.apple.com/app/apple-store/id6800614202?pt=${token}&ct=share&mt=8`);
});

test("the page stays out of the sitemap, is published, and has no en or em dash", () => {
  assert.ok(!read("sitemap.xml").includes("/m/"), "sitemap.xml lists the share page");
  const excluded = read("_config.yml").split("\n").map((l) => l.trim()).filter((l) => l.startsWith("- "));
  assert.ok(!excluded.some((l) => /^- m\/?$/.test(l)), "_config.yml excludes m/");
  const dashes = /[\u2012\u2013\u2014\u2015]/;
  assert.ok(!dashes.test(html), "m/index.html has a dash");
  assert.ok(!dashes.test(read("m/open.js")), "m/open.js has a dash");
});
