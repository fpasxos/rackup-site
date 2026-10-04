// Tests for the store redirect page (go/index.html, go/go.js).
// Node 18 or newer, no packages: node --test tools/go_page.test.js
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const read = (file) => fs.readFileSync(path.join(ROOT, file), "utf8");
const page = require(path.join(ROOT, "go", "go.js"));
const html = read("go/index.html");

// Literals the app repo's store-assets/hall-links/hall_links.py builds; change both together.
const HALL_PLAY = "https://play.google.com/store/apps/details?id=com.rackup.app" +
  "&referrer=utm_source%3Dhall%26utm_medium%3Dqr%26utm_campaign%3Dnax-galaxias";
const GENERAL_PLAY = "https://play.google.com/store/apps/details?id=com.rackup.app" +
  "&referrer=utm_source%3Dshare%26utm_medium%3Dqr%26utm_campaign%3Dgeneral";
const PLAIN_APP_STORE = "https://apps.apple.com/gr/app/id6800614202";
const HALL_APP_STORE = "https://apps.apple.com/gr/app/apple-store/id6800614202?pt=12aB34&ct=nax-galaxias&mt=8";
const GENERAL_APP_STORE = "https://apps.apple.com/gr/app/apple-store/id6800614202?pt=12aB34&ct=general&mt=8";

// Ad and bio links, built only on this site: s sets utm_source and utm_medium, h stays the campaign.
const META_PLAY = "https://play.google.com/store/apps/details?id=com.rackup.app" +
  "&referrer=utm_source%3Dmeta%26utm_medium%3Dpaid%26utm_campaign%3Dath-tonight";
const IG_PLAY = "https://play.google.com/store/apps/details?id=com.rackup.app" +
  "&referrer=utm_source%3Dinstagram%26utm_medium%3Dsocial%26utm_campaign%3Dbio";
const FB_PLAY = "https://play.google.com/store/apps/details?id=com.rackup.app" +
  "&referrer=utm_source%3Dfacebook%26utm_medium%3Dsocial%26utm_campaign%3Dpage";
const META_APP_STORE = "https://apps.apple.com/gr/app/apple-store/id6800614202?pt=12aB34&ct=meta-ath-tonight&mt=8";

const UA = {
  iphoneSafari: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
  iphoneChrome: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/128.0.6613.98 Mobile/15E148 Safari/604.1",
  ipadMobile: "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
  ipadDesktopMode: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
  macSafari: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
  instagramIos: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 330.0.3.30.93 (iPhone15,2; iOS 17_5; el_GR; el; scale=3.00; 1179x2556; 598563473)",
  facebookIos: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 [FBAN/FBIOS;FBAV/470.0.0.39.108;FBBV/612345678;FBDV/iPhone15,2;FBMD/iPhone;FBSN/iOS;FBSV/17.5;FBSS/3;FBID/phone;FBLC/el_GR;FBOP/5]",
  androidChrome: "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
  samsungInternet: "Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0.0.0 Mobile Safari/537.36",
  instagramAndroid: "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36 Instagram 344.0.0.34.89 Android (34/14; 480dpi; 1080x2340; samsung; SM-S918B; dm3q; qcom; el_GR; 630012345)",
  facebookAndroid: "Mozilla/5.0 (Linux; Android 13; Pixel 7 Build/TQ3A.230901.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/475.0.0.43.111;]",
  windowsChrome: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
};

// Starts as go/index.html does: only the desktop block is hidden.
function fakeDocument() {
  const elements = {};
  for (const id of ["app-store", "google-play", "opening", "desktop"]) {
    elements[id] = { hidden: id === "desktop", attributes: {}, setAttribute(k, v) { this.attributes[k] = v; } };
  }
  return { elements, getElementById: (id) => elements[id] };
}

function fakeLocation(search) {
  return { search, replaced: [], replace(url) { this.replaced.push(url); } };
}

function run(userAgent, maxTouchPoints, search) {
  const doc = fakeDocument();
  const loc = fakeLocation(search);
  page.wire(doc, { userAgent, maxTouchPoints }, loc);
  return { doc, loc, hrefs: [doc.elements["app-store"].attributes.href, doc.elements["google-play"].attributes.href] };
}

test("hall slugs as hall_links.py derives them are accepted", () => {
  for (const slug of ["nax-galaxias", "ath-king8", "vol-galaxy", "a", "9", "a1-b2-c3", "a".repeat(30)]) {
    assert.equal(page.hallFrom(`?h=${slug}`), slug);
    assert.equal(page.isValidHall(slug), true, slug);
  }
  assert.equal(page.hallFrom("?h=nax-galaxias&utm_source=x"), "nax-galaxias");
});

test("hostile or malformed hall values fall back to the general code", () => {
  const hostile = [
    "", "a".repeat(31), "Nax-galaxias", "NAX", "nax galaxias", "nax\"x", "nax'x", "nax&x", "nax#x",
    "nax%x", "nax%2Fx", "nax/x", "nax_x", "nax.x", "-nax", "nax-", "nax--x", "νάξος", "nax\n",
    "<script>", "javascript:alert(1)", "nax;ct=evil"
  ];
  for (const h of hostile) {
    assert.equal(page.hallFrom(`?h=${encodeURIComponent(h)}`), null, `accepted ${JSON.stringify(h)}`);
    assert.equal(page.isValidHall(h), false, `valid ${JSON.stringify(h)}`);
  }
  for (const raw of ["?h=nax galaxias", "?h=nax+galaxias", "?h=%", "?h=nax%", "?h=nax#x", "?h=%E2%80%94", "?h"]) {
    assert.equal(page.hallFrom(raw), null, `accepted raw ${raw}`);
  }
  assert.equal(page.isValidHall(null), false);
  assert.equal(page.isValidHall(undefined), false);
});

test("a missing, renamed or repeated h is the general code", () => {
  for (const search of ["", "?", undefined, "?x=nax-galaxias", "?H=nax-galaxias",
    "?h=nax-galaxias&h=ath-king8", "?h=nax-galaxias&h=nax-galaxias", "?h=nax-galaxias&h="]) {
    assert.equal(page.hallFrom(search), null, `accepted ${search}`);
  }
});

test("the Play links are the literals hall_links.py builds", () => {
  assert.equal(page.playUrl("nax-galaxias"), HALL_PLAY);
  assert.equal(page.playUrl(null), GENERAL_PLAY);
  const referrer = new URL(HALL_PLAY).searchParams.get("referrer");
  assert.equal(referrer, "utm_source=hall&utm_medium=qr&utm_campaign=nax-galaxias");
  assert.equal(new URL(GENERAL_PLAY).searchParams.get("id"), "com.rackup.app");
});

test("without a provider token every App Store link is the plain Greek storefront one", () => {
  assert.equal(page.buildAppStoreUrl("nax-galaxias", ""), PLAIN_APP_STORE);
  assert.equal(page.buildAppStoreUrl(null, ""), PLAIN_APP_STORE);
});

test("with a provider token the App Store links carry pt, ct and mt", () => {
  assert.equal(page.buildAppStoreUrl("nax-galaxias", "12aB34"), HALL_APP_STORE);
  assert.equal(page.buildAppStoreUrl(null, "12aB34"), GENERAL_APP_STORE);
  assert.equal(page.buildAppStoreUrl("a".repeat(30), "12aB34").match(/ct=([^&]*)/)[1].length, 30);
});

// Without /gr/ the web falls back to the US store, which has no RackUp: a 404 on a computer.
test("every App Store link names the Greek storefront, tagged or plain", () => {
  const greek = "apps.apple.com/gr/app/";
  for (const token of ["", "12aB34", page.PROVIDER_TOKEN]) {
    for (const hall of [null, "nax-galaxias", "a".repeat(30)]) {
      for (const source of [null, undefined, "meta", "ig", "fb"]) {
        const url = page.buildAppStoreUrl(hall, token, source);
        assert.ok(url.startsWith("https://" + greek), `${url} names no storefront`);
      }
    }
  }
  const everywhere = /apps\.apple\.com[^\s"'<>]*/g;
  for (const file of ["go/go.js", "go/index.html"]) {
    const found = read(file).match(everywhere) || [];
    assert.ok(found.length > 0, `${file} has no App Store link`);
    for (const url of found) assert.ok(url.startsWith(greek), `${file}: ${url} names no storefront`);
  }
});

test("the builders refuse a bad hall or token instead of emitting it", () => {
  assert.throws(() => page.playUrl("nax&x"));
  assert.throws(() => page.playUrl(""));
  assert.throws(() => page.buildAppStoreUrl("NAX", "12aB34"));
  assert.throws(() => page.buildAppStoreUrl("nax-galaxias", "12aB&ct=x"));
  assert.throws(() => page.buildAppStoreUrl(null, "PASTE PT"));
});

test("the provider token is empty or letters and digits, and appStoreUrl uses it", () => {
  assert.match(page.PROVIDER_TOKEN, /^[A-Za-z0-9]*$/);
  for (const hall of ["nax-galaxias", null]) {
    assert.equal(page.appStoreUrl(hall), page.buildAppStoreUrl(hall, page.PROVIDER_TOKEN));
  }
});

test("iPhones, iPads and iPadOS desktop mode are iOS", () => {
  assert.equal(page.platformOf(UA.iphoneSafari, 5), "ios");
  assert.equal(page.platformOf(UA.iphoneChrome, 5), "ios");
  assert.equal(page.platformOf(UA.ipadMobile, 5), "ios");
  assert.equal(page.platformOf(UA.ipadDesktopMode, 5), "ios");
  assert.equal(page.platformOf(UA.instagramIos, 5), "ios");
  assert.equal(page.platformOf(UA.facebookIos, 5), "ios");
  assert.equal(page.platformOf("Mozilla/5.0 (iPod touch; CPU iPhone OS 15_8 like Mac OS X)", 5), "ios");
});

test("Android browsers and in-app browsers are Android", () => {
  for (const ua of [UA.androidChrome, UA.samsungInternet, UA.instagramAndroid, UA.facebookAndroid]) {
    assert.equal(page.platformOf(ua, 5), "android", ua);
  }
});

test("a real Mac, Windows and unknown agents are other", () => {
  assert.equal(page.platformOf(UA.macSafari, 0), "other");
  assert.equal(page.platformOf(UA.macSafari, 1), "other");
  assert.equal(page.platformOf(UA.macSafari, undefined), "other");
  assert.equal(page.platformOf(UA.windowsChrome, 0), "other");
  assert.equal(page.platformOf(UA.windowsChrome, 10), "other", "a Windows touch screen is not a phone");
  assert.equal(page.platformOf(undefined, undefined), "other");
  assert.equal(page.platformOf("", 0), "other");
});

test("on iOS a hall code sets both buttons and goes to the App Store once", () => {
  for (const [ua, touch] of [[UA.iphoneSafari, 5], [UA.ipadDesktopMode, 5], [UA.instagramIos, 5]]) {
    const { doc, loc, hrefs } = run(ua, touch, "?h=nax-galaxias");
    assert.deepEqual(hrefs, [page.appStoreUrl("nax-galaxias"), HALL_PLAY]);
    assert.deepEqual(loc.replaced, [page.appStoreUrl("nax-galaxias")]);
    assert.equal(doc.elements.opening.hidden, false);
    assert.equal(doc.elements.desktop.hidden, true);
  }
});

test("on Android a hall code sets both buttons and goes to Play once", () => {
  for (const ua of [UA.androidChrome, UA.samsungInternet, UA.facebookAndroid]) {
    const { doc, loc, hrefs } = run(ua, 5, "?h=nax-galaxias");
    assert.deepEqual(hrefs, [page.appStoreUrl("nax-galaxias"), HALL_PLAY]);
    assert.deepEqual(loc.replaced, [HALL_PLAY]);
    assert.equal(doc.elements.opening.hidden, false);
    assert.equal(doc.elements.desktop.hidden, true);
  }
});

test("elsewhere the buttons are set, Get RackUp replaces the opening text and nothing redirects", () => {
  for (const [ua, touch] of [[UA.macSafari, 0], [UA.windowsChrome, 0]]) {
    const { doc, loc, hrefs } = run(ua, touch, "?h=nax-galaxias");
    assert.deepEqual(hrefs, [page.appStoreUrl("nax-galaxias"), HALL_PLAY]);
    assert.deepEqual(loc.replaced, []);
    assert.equal(doc.elements.opening.hidden, true, "a desktop must not read Opening the app store");
    assert.equal(doc.elements.desktop.hidden, false);
  }
});

test("the opening text and the desktop heading sit in the blocks the script toggles", () => {
  const block = (id) => html.match(new RegExp(`<div id="${id}"( hidden)?>([\\s\\S]*?)</div>`));
  const opening = block("opening");
  assert.equal(opening[1], undefined, "#opening must start visible");
  assert.match(opening[2], /<h1>Ανοίγει το κατάστημα εφαρμογών…<\/h1>/);
  assert.match(opening[2], /Αν δεν ανοίξει αυτόματα/);
  const desktop = block("desktop");
  assert.equal(desktop[1], " hidden", "#desktop must start hidden");
  assert.match(desktop[2], /<h1>Κατέβασε το RackUp<\/h1>/);
  assert.match(desktop[2], /<p class="tag" lang="en">Get RackUp<\/p>/);
  assert.equal((html.match(/Ανοίγει το κατάστημα/g) || []).length, 1, "the opening heading appears outside #opening");
});

test("the general code and a hostile h both send phones to the general links", () => {
  for (const search of ["", "?h=" + encodeURIComponent("x\" onclick=\"alert(1)")]) {
    assert.deepEqual(run(UA.androidChrome, 5, search).loc.replaced, [GENERAL_PLAY]);
    const ios = run(UA.iphoneSafari, 5, search);
    assert.deepEqual(ios.loc.replaced, [page.appStoreUrl(null)]);
    assert.deepEqual(ios.hrefs, [page.appStoreUrl(null), GENERAL_PLAY]);
  }
});

test("only meta, ig and fb are sources, and only when s appears once", () => {
  for (const key of ["meta", "ig", "fb"]) {
    assert.equal(page.sourceFrom(`?s=${key}`), key);
    assert.equal(page.sourceFrom(`?s=${key}&h=ath-tonight&fbclid=IwAR0abc`), key);
    assert.equal(page.isValidSource(key), true, key);
  }
  const rejected = [
    "", "META", "Meta", "meta ", " meta", "instagram", "facebook", "google", "tiktok", "hall", "share", "qr",
    "__proto__", "constructor", "toString", "hasOwnProperty", "valueOf", "meta&h=x", "meta-ig", "<script>"
  ];
  for (const s of rejected) {
    assert.equal(page.sourceFrom(`?s=${encodeURIComponent(s)}`), null, `accepted ${JSON.stringify(s)}`);
    assert.equal(page.isValidSource(s), false, `valid ${JSON.stringify(s)}`);
  }
  for (const search of ["", "?", undefined, "?S=meta", "?source=meta", "?s=meta&s=ig", "?s=meta&s=meta",
    "?s=meta&s=", "?s", "?s=meta+"]) {
    assert.equal(page.sourceFrom(search), null, `accepted ${search}`);
  }
  for (const value of [null, undefined, 1, {}, ["meta"]]) {
    assert.equal(page.isValidSource(value), false, String(value));
  }
});

test("a source sets utm_source and utm_medium, and h stays the campaign", () => {
  assert.equal(page.playUrl("ath-tonight", "meta"), META_PLAY);
  assert.equal(page.playUrl("bio", "ig"), IG_PLAY);
  assert.equal(page.playUrl("page", "fb"), FB_PLAY);
  const referrer = (url) => new URL(url).searchParams.get("referrer");
  assert.equal(referrer(META_PLAY), "utm_source=meta&utm_medium=paid&utm_campaign=ath-tonight");
  assert.equal(referrer(IG_PLAY), "utm_source=instagram&utm_medium=social&utm_campaign=bio");
  assert.equal(referrer(FB_PLAY), "utm_source=facebook&utm_medium=social&utm_campaign=page");
  assert.equal(referrer(page.playUrl(null, "meta")), "utm_source=meta&utm_medium=paid&utm_campaign=general");
});

test("no source leaves every hall QR link byte for byte as it was", () => {
  for (const source of [null, undefined]) {
    assert.equal(page.playUrl("nax-galaxias", source), HALL_PLAY);
    assert.equal(page.playUrl(null, source), GENERAL_PLAY);
    assert.equal(page.buildAppStoreUrl("nax-galaxias", "12aB34", source), HALL_APP_STORE);
    assert.equal(page.buildAppStoreUrl(null, "12aB34", source), GENERAL_APP_STORE);
    assert.equal(page.buildAppStoreUrl("nax-galaxias", "", source), PLAIN_APP_STORE);
  }
});

test("with a provider token a source prefixes ct, and without one the link stays plain", () => {
  assert.equal(page.buildAppStoreUrl("ath-tonight", "12aB34", "meta"), META_APP_STORE);
  const ct = (hall, source) => new URL(page.buildAppStoreUrl(hall, "12aB34", source)).searchParams.get("ct");
  assert.equal(ct("bio", "ig"), "ig-bio");
  assert.equal(ct("page", "fb"), "fb-page");
  assert.equal(ct(null, "meta"), "meta-general");
  for (const source of ["meta", "ig", "fb"]) {
    assert.equal(page.buildAppStoreUrl("ath-tonight", "", source), PLAIN_APP_STORE, source);
    assert.equal(page.appStoreUrl("ath-tonight", source), page.buildAppStoreUrl("ath-tonight", page.PROVIDER_TOKEN, source));
  }
});

test("a ct that would pass Apple's 30 characters drops the source, never the campaign", () => {
  assert.equal(page.campaignToken("a".repeat(25), "meta"), "meta-" + "a".repeat(25));
  assert.equal(page.campaignToken("a".repeat(26), "meta"), "a".repeat(26));
  assert.equal(page.campaignToken("a".repeat(27), "ig"), "ig-" + "a".repeat(27));
  assert.equal(page.campaignToken("a".repeat(28), "fb"), "a".repeat(28));
  for (const source of ["meta", "ig", "fb", null]) {
    for (let n = 1; n <= 30; n++) {
      const token = page.campaignToken("a".repeat(n), source);
      assert.ok(token.length <= 30, `${source} with ${n} gives ${token.length}`);
      assert.ok(token.endsWith("a".repeat(n)), `${source} with ${n} lost the campaign`);
    }
  }
  const long = "a".repeat(30);
  assert.equal(new URL(page.buildAppStoreUrl(long, "12aB34", "meta")).searchParams.get("ct"), long);
});

test("the builders refuse a source outside the list instead of emitting it", () => {
  for (const bad of ["", "META", "instagram", "__proto__", "constructor", "meta&x", 1]) {
    assert.throws(() => page.playUrl("ath-tonight", bad), /invalid source/, String(bad));
    assert.throws(() => page.buildAppStoreUrl("ath-tonight", "12aB34", bad), /invalid source/, String(bad));
    assert.throws(() => page.buildAppStoreUrl("ath-tonight", "", bad), /invalid source/, String(bad));
  }
  assert.throws(() => page.playUrl("ath tonight", "meta"), /invalid hall slug/);
});

test("an ad link goes to the App Store on iOS and to Play on Android, with its source", () => {
  const search = "?s=meta&h=ath-tonight&fbclid=IwAR0abc";
  const apple = page.appStoreUrl("ath-tonight", "meta");
  for (const [ua, touch] of [[UA.iphoneSafari, 5], [UA.instagramIos, 5], [UA.facebookIos, 5], [UA.ipadDesktopMode, 5]]) {
    const { doc, loc, hrefs } = run(ua, touch, search);
    assert.deepEqual(hrefs, [apple, META_PLAY]);
    assert.deepEqual(loc.replaced, [apple]);
    assert.equal(doc.elements.desktop.hidden, true);
  }
  for (const ua of [UA.androidChrome, UA.instagramAndroid, UA.facebookAndroid]) {
    const { doc, loc, hrefs } = run(ua, 5, search);
    assert.deepEqual(hrefs, [apple, META_PLAY]);
    assert.deepEqual(loc.replaced, [META_PLAY]);
    assert.equal(doc.elements.desktop.hidden, true);
  }
  const badCampaign = "?s=meta&h=" + encodeURIComponent("x\" onclick=\"alert(1)");
  assert.deepEqual(run(UA.androidChrome, 5, badCampaign).loc.replaced, [page.playUrl(null, "meta")]);
});

test("on a desktop a bio link sets the buttons and redirects nowhere", () => {
  for (const [search, hall, source, play] of [["?s=ig&h=bio", "bio", "ig", IG_PLAY], ["?s=fb&h=page", "page", "fb", FB_PLAY]]) {
    for (const [ua, touch] of [[UA.macSafari, 0], [UA.windowsChrome, 0]]) {
      const { doc, loc, hrefs } = run(ua, touch, search);
      assert.deepEqual(hrefs, [page.appStoreUrl(hall, source), play]);
      assert.deepEqual(loc.replaced, []);
      assert.equal(doc.elements.opening.hidden, true);
      assert.equal(doc.elements.desktop.hidden, false);
    }
  }
});

test("an unknown, repeated or empty s behaves exactly like the same link without it", () => {
  const extras = ["s=google", "s=META", "s=", "s", "s=meta&s=ig", "s=ig&s=ig", "s=__proto__", "s=constructor", "S=meta"];
  for (const base of ["?h=nax-galaxias", ""]) {
    for (const extra of extras) {
      const search = base ? `${base}&${extra}` : `?${extra}`;
      assert.equal(page.sourceFrom(search), null, search);
      for (const [ua, touch] of [[UA.iphoneSafari, 5], [UA.androidChrome, 5], [UA.windowsChrome, 0]]) {
        const plain = run(ua, touch, base);
        const tagged = run(ua, touch, search);
        assert.deepEqual(tagged.hrefs, plain.hrefs, search);
        assert.deepEqual(tagged.loc.replaced, plain.loc.replaced, search);
        assert.equal(tagged.doc.elements.desktop.hidden, plain.doc.elements.desktop.hidden, search);
      }
    }
  }
  assert.deepEqual(run(UA.androidChrome, 5, "?s=google&h=nax-galaxias").loc.replaced, [HALL_PLAY]);
  assert.deepEqual(run(UA.androidChrome, 5, "?s=google").loc.replaced, [GENERAL_PLAY]);
});

test("the page is noindex, previews well and loads no script but its own", () => {
  assert.match(html, /<html lang="el">/);
  assert.match(html, /<meta name="robots" content="noindex">/);
  assert.match(html, /<meta name="referrer" content="no-referrer">/);
  for (const property of ["og:title", "og:description", "og:image", "og:url"]) {
    assert.match(html, new RegExp(`<meta property="${property}" content="[^"]+">`), property);
  }
  assert.match(html, /<meta property="og:url" content="https:\/\/getrackup\.com\/go\/">/);
  assert.match(html, /<meta property="og:image" content="https:\/\/getrackup\.com\/assets\/og-card\.png">/);
  assert.match(html, /<meta name="twitter:card" content="summary_large_image">/);
  const image = html.match(/property="og:image" content="https:\/\/getrackup\.com\/([^"]+)"/)[1];
  assert.ok(fs.existsSync(path.join(ROOT, image)), `og:image ${image} is not in the repo`);
  const scripts = [...html.matchAll(/<script\b[^>]*>/g)].map((m) => m[0]);
  assert.deepEqual(scripts, ['<script src="go.js" defer>']);
  assert.doesNotMatch(html, /<img\b|<iframe\b|gtag|googletagmanager|analytics/i);
});

test("the Content Security Policy is the share page's, and lets the site's own fonts load", () => {
  const csp = (source) => source.match(/http-equiv="Content-Security-Policy" content="([^"]+)"/)[1];
  assert.equal(csp(html), "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; " +
    "font-src 'self'; base-uri 'none'; form-action 'none'");
  assert.equal(csp(html), csp(read("m/index.html")));
  assert.match(csp(html), /script-src 'self'/);
});

test("the page is styled by the site stylesheet and nothing else", () => {
  const sheets = [...html.matchAll(/<link\b[^>]*rel="stylesheet"[^>]*>/g)].map((m) => m[0]);
  assert.deepEqual(sheets, ['<link rel="stylesheet" href="../assets/site.css">']);
});

test("the store buttons exist, the note starts hidden, and the static links are the general ones", () => {
  assert.match(html, /id="desktop"[^>]*\bhidden\b/);
  for (const id of ["app-store", "google-play", "opening", "desktop"]) {
    assert.equal((html.match(new RegExp(`id="${id}"`, "g")) || []).length, 1, id);
  }
  const unescape = (s) => s.replace(/&amp;/g, "&");
  assert.equal(unescape(html.match(/id="app-store" href="([^"]+)"/)[1]), page.appStoreUrl(null));
  assert.equal(unescape(html.match(/id="google-play" href="([^"]+)"/)[1]), GENERAL_PLAY);
});

test("the page stays out of the sitemap, is published, and has no en or em dash", () => {
  assert.ok(!read("sitemap.xml").includes("/go/"), "sitemap.xml lists the redirect page");
  const excluded = read("_config.yml").split("\n").map((l) => l.trim()).filter((l) => l.startsWith("- "));
  assert.ok(!excluded.some((l) => /^- go\/?$/.test(l)), "_config.yml excludes go/");
  const dashes = /[\u2012\u2013\u2014\u2015]/;
  for (const file of ["go/index.html", "go/go.js", "tools/go_page.test.js"]) {
    assert.ok(!dashes.test(read(file)), `${file} has a dash`);
  }
});
