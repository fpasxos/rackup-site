// Tests for the invite page (f/index.html, f/invite.js).
// Node 18 or newer, no packages: node --test tools/invite_page.test.js
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const ROOT = path.resolve(__dirname, "..");
const read = (file) => fs.readFileSync(path.join(ROOT, file), "utf8");
const page = require(path.join(ROOT, "f", "invite.js"));
const go = require(path.join(ROOT, "go", "go.js"));
const HALLS = require(path.join(ROOT, "m", "halls.js"));
const html = read("f/index.html");
const TOKEN = read("go/go.js").match(/var PROVIDER_TOKEN = "([^"]*)"/)[1];

// The links the app repo's invite code builds and reads; change both together.
const LINK = "?h=ath-king8&c=7KQ4M2XP";
const INVITE_PLAY = "https://play.google.com/store/apps/details?id=com.rackup.app" +
  "&referrer=utm_source%3Dfriend%26utm_medium%3Dinvite%26utm_campaign%3Dath-king8%26rackup_invite%3D7KQ4M2XP";
const INVITE_INTENT = "intent://invite/7KQ4M2XP?h=ath-king8#Intent;scheme=rackup;package=com.rackup.app;" +
  "S.browser_fallback_url=https%3A%2F%2Fplay.google.com%2Fstore%2Fapps%2Fdetails%3Fid%3Dcom.rackup.app" +
  "%26referrer%3Dutm_source%253Dfriend%2526utm_medium%253Dinvite%2526utm_campaign%253Dath-king8" +
  "%2526rackup_invite%253D7KQ4M2XP;end";
const APP_LINK = "rackup://invite/7KQ4M2XP?h=ath-king8";
const INVITE_APP_STORE = `https://apps.apple.com/gr/app/apple-store/id6800614202?pt=${TOKEN}&ct=f-ath-king8&mt=8`;
// A bad link keeps the static buttons: an invite with no hall and no code.
const GENERAL_PLAY = "https://play.google.com/store/apps/details?id=com.rackup.app" +
  "&referrer=utm_source%3Dfriend%26utm_medium%3Dinvite%26utm_campaign%3Dgeneral";
const GENERAL_APP_STORE = `https://apps.apple.com/gr/app/apple-store/id6800614202?pt=${TOKEN}&ct=f-general&mt=8`;
const ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ";

const UA = {
  androidChrome: "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
  samsungInternet: "Mozilla/5.0 (Linux; Android 14; SAMSUNG SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0.0.0 Mobile Safari/537.36",
  instagramAndroid: "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36 Instagram 344.0.0.34.89 Android (34/14; 480dpi; 1080x2340; samsung; SM-S918B; dm3q; qcom; el_GR; 630012345)",
  messengerAndroid: "Mozilla/5.0 (Linux; Android 13; Pixel 7 Build/TQ3A.230901.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36 [FB_IAB/Orca-Android;FBAV/450.0.0.38.108;]",
  iphoneSafari: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
  ipadDesktopMode: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
  instagramIos: "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 330.0.3.30.93 (iPhone15,2; iOS 17_5; el_GR; el; scale=3.00; 1179x2556; 598563473)",
  macSafari: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
  windowsChrome: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
};
const ANDROID = [[UA.androidChrome, 5], [UA.samsungInternet, 5], [UA.instagramAndroid, 5], [UA.messengerAndroid, 5]];
const IOS = [[UA.iphoneSafari, 5], [UA.ipadDesktopMode, 5], [UA.instagramIos, 5]];
const DESKTOP = [[UA.macSafari, 0], [UA.windowsChrome, 0]];

// Starts as f/index.html does: only the two store buttons show.
const IDS = ["hall", "hall-name", "hall-city", "hall-en", "android", "open-app", "bad-link", "app-store", "google-play",
  "ios-open", "open-ios", "code-box", "code"];
const STARTS_HIDDEN = ["hall", "android", "bad-link", "ios-open", "code-box"];

function fakeDocument() {
  const elements = {};
  for (const id of IDS) {
    elements[id] = {
      hidden: STARTS_HIDDEN.includes(id), attributes: {}, textContent: "",
      setAttribute(k, v) { this.attributes[k] = v; }
    };
  }
  return { elements, getElementById: (id) => elements[id] || null };
}

function run(userAgent, maxTouchPoints, search, halls = HALLS) {
  const doc = fakeDocument();
  const loc = { search, replaced: [], replace(url) { this.replaced.push(url); } };
  page.wire(doc, { userAgent, maxTouchPoints }, loc, halls);
  return { el: doc.elements, loc };
}

test("a code is 8 of the 31 symbols, with no 0, 1, I, L or O", () => {
  for (const code of ["7KQ4M2XP", "23456789", "ABCDEFGH", "JKMNPQRS", "TUVWXYZ2", "ZZZZZZZZ"]) {
    assert.equal(page.isValidCode(code), true, code);
  }
  const symbols = [];
  for (let c = 32; c < 127; c++) {
    if (page.isValidCode(String.fromCharCode(c).repeat(8))) symbols.push(String.fromCharCode(c));
  }
  assert.equal(symbols.join(""), ALPHABET);
  const bad = ["", "7KQ4M2X", "7KQ4M2XPA", "7kq4m2xp", "7KQ4 M2XP", "7KQ4-M2XP", "0KQ4M2XP", "1KQ4M2XP", "IKQ4M2XP",
    "LKQ4M2XP", "OKQ4M2XP", "7KQ4M2X%", "7KQ4M2XP\n", "ΑΒΓΔΕΖΗΘ", "7KQ4M2ΧP", "7KQ4M2XP;end", null, undefined, 12345678];
  for (const code of bad) assert.equal(page.isValidCode(code), false, JSON.stringify(code));
});

test("an invite link names one listed hall and one code; anything else is a bad link", () => {
  const invite = page.inviteFrom(LINK, HALLS);
  assert.deepEqual(invite, {
    code: "7KQ4M2XP", slug: "ath-king8",
    hall: { id: "venue-ath-king8", name: "King 8", city: { el: "Αθήνα", en: "Athens" }, citySlug: "athens" }
  });
  assert.equal(page.inviteFrom("?c=7KQ4M2XP&h=ath-king8&fbclid=IwAR0abc&utm_source=evil", HALLS).code, "7KQ4M2XP");
  const bad = [
    "", "?", undefined, "?h=ath-king8", "?c=7KQ4M2XP", "?h=ath-king8&c=7kq4m2xp", "?h=ath-king8&c=7KQ4M2X",
    "?h=ath-tonight&c=7KQ4M2XP", "?h=venue-ath-king8&c=7KQ4M2XP", "?h=ATH-KING8&c=7KQ4M2XP",
    "?h=ath-king8&h=ath-king8&c=7KQ4M2XP", "?h=ath-king8&c=7KQ4M2XP&c=7KQ4M2XP", "?h=ath-king8&c=7KQ4M2XP&c=",
    "?H=ath-king8&C=7KQ4M2XP", "?h=__proto__&c=7KQ4M2XP", "?h=constructor&c=7KQ4M2XP",
    "?h=ath-king8&c=" + encodeURIComponent("7KQ4M2XP;S.evil=1"), "?h=" + encodeURIComponent("ath-king8#Intent") + "&c=7KQ4M2XP"
  ];
  for (const search of bad) assert.equal(page.inviteFrom(search, HALLS), null, String(search));
  // With no hall list nothing can be named, so no link is good.
  for (const halls of [undefined, null, {}]) assert.equal(page.inviteFrom(LINK, halls), null);
});

test("the Play link carries the invite referrer the app reads once", () => {
  assert.equal(page.playUrl("ath-king8", "7KQ4M2XP"), INVITE_PLAY);
  const referrer = new URL(INVITE_PLAY).searchParams.get("referrer");
  assert.equal(referrer, "utm_source=friend&utm_medium=invite&utm_campaign=ath-king8&rackup_invite=7KQ4M2XP");
  assert.deepEqual([...new URLSearchParams(referrer).keys()], ["utm_source", "utm_medium", "utm_campaign", "rackup_invite"]);
  assert.equal(new URL(INVITE_PLAY).searchParams.get("id"), "com.rackup.app");
  assert.equal(page.playUrl(null, null), GENERAL_PLAY);
});

test("Android's intent opens rackup://invite/<CODE>?h=<hall> in RackUp, or Play with the invite inside", () => {
  assert.equal(page.intentUrl("ath-king8", "7KQ4M2XP"), INVITE_INTENT);
  const fallback = INVITE_INTENT.match(/;S\.browser_fallback_url=([^;]*);end$/)[1];
  assert.equal(decodeURIComponent(fallback), INVITE_PLAY);
  assert.equal(page.appUrl("ath-king8", "7KQ4M2XP"), APP_LINK);
});

test("the App Store link is tagged f-<hall> by go.js's rule, in the hall's storefront", () => {
  assert.equal(page.appStoreUrl("ath-king8"), INVITE_APP_STORE);
  assert.equal(page.appStoreUrl("ath-king8"), go.taggedAppStoreUrl("ath-king8", "f"));
  assert.equal(page.appStoreUrl("cy-lim-century"),
    `https://apps.apple.com/cy/app/apple-store/id6800614202?pt=${TOKEN}&ct=f-cy-lim-century&mt=8`);
  assert.equal(page.appStoreUrl(null), GENERAL_APP_STORE);
  for (const id of Object.keys(HALLS)) {
    const slug = id.replace(/^venue-/, "");
    assert.equal(new URL(page.appStoreUrl(slug)).searchParams.get("ct"), `f-${slug}`, id);
  }
});

test("the builders refuse a bad hall or code instead of emitting it", () => {
  for (const [slug, code] of [["ath king8", "7KQ4M2XP"], ["", "7KQ4M2XP"], ["ath-king8", "7kq4m2xp"],
    ["ath-king8", "7KQ4M2XP;end"], ["ath-king8", ""], [null, "7KQ4M2XP"], ["ath-king8", null]]) {
    assert.throws(() => page.intentUrl(slug, code), /invalid/, `${slug} ${code}`);
    assert.throws(() => page.appUrl(slug, code), /invalid/, `${slug} ${code}`);
  }
  assert.throws(() => page.playUrl("ath-king8", "7KQ4M2X"), /invalid invite code/);
  assert.throws(() => page.playUrl("ath&x", "7KQ4M2XP"), /invalid hall slug/);
  assert.throws(() => page.playUrl(null, "7KQ4M2XP"), /a code needs its hall/);
  assert.throws(() => page.playUrl("ath-king8", null), /a hall needs its code/);
});

test("on Android a good link opens the invite in RackUp, and keeps the hall, the button, the note and Play", () => {
  for (const [ua, touch] of ANDROID) {
    const { el, loc } = run(ua, touch, LINK);
    assert.deepEqual(loc.replaced, [INVITE_INTENT], ua);
    assert.equal(el["open-app"].attributes.href, INVITE_INTENT);
    assert.equal(el.android.hidden, false);
    assert.equal(el.hall.hidden, false);
    assert.equal(el["google-play"].attributes.href, INVITE_PLAY);
    assert.equal(el["google-play"].hidden, false);
    assert.equal(el["app-store"].hidden, true, "an Android phone sees only Google Play");
    for (const id of ["ios-open", "code-box", "bad-link"]) assert.equal(el[id].hidden, true, id);
    assert.equal(el.code.textContent, "", "the code is for iPhones and computers");
  }
});

test("on an iPhone the page offers the App Store, the app link and the code, and goes nowhere by itself", () => {
  for (const [ua, touch] of IOS) {
    const { el, loc } = run(ua, touch, LINK);
    assert.deepEqual(loc.replaced, [], ua);
    assert.equal(el["app-store"].attributes.href, INVITE_APP_STORE);
    assert.equal(el["app-store"].hidden, false);
    assert.equal(el["google-play"].hidden, true);
    assert.equal(el["ios-open"].hidden, false);
    assert.equal(el["open-ios"].attributes.href, APP_LINK);
    assert.equal(el["code-box"].hidden, false);
    assert.equal(el.code.textContent, "7KQ4 M2XP");
    for (const id of ["android", "bad-link"]) assert.equal(el[id].hidden, true, id);
    assert.equal(el["open-app"].attributes.href, undefined);
  }
});

test("on a computer the page shows the code and both stores, and goes nowhere", () => {
  for (const [ua, touch] of DESKTOP) {
    const { el, loc } = run(ua, touch, LINK);
    assert.deepEqual(loc.replaced, [], ua);
    assert.equal(el["app-store"].attributes.href, INVITE_APP_STORE);
    assert.equal(el["google-play"].attributes.href, INVITE_PLAY);
    assert.equal(el["app-store"].hidden, false);
    assert.equal(el["google-play"].hidden, false);
    assert.equal(el["code-box"].hidden, false);
    assert.equal(el.code.textContent, "7KQ4 M2XP");
    for (const id of ["android", "ios-open", "bad-link"]) assert.equal(el[id].hidden, true, id);
  }
});

test("a bad link shows a short message and both stores, everywhere, and never a hall or a code", () => {
  const bad = ["", "?h=ath-king8", "?h=ath-tonight&c=7KQ4M2XP", "?h=ath-king8&c=7KQ4M2X0",
    "?h=ath-king8&c=" + encodeURIComponent("x\" onclick=\"alert(1)")];
  for (const search of bad) {
    for (const [ua, touch] of [...ANDROID, ...IOS, ...DESKTOP]) {
      const { el, loc } = run(ua, touch, search);
      assert.deepEqual(loc.replaced, [], search);
      assert.equal(el["bad-link"].hidden, false, search);
      assert.equal(el["app-store"].hidden, false, search);
      assert.equal(el["google-play"].hidden, false, search);
      for (const id of ["hall", "android", "ios-open", "code-box"]) assert.equal(el[id].hidden, true, `${search} ${id}`);
      for (const id of IDS) assert.deepEqual(el[id].attributes, {}, `${search} ${id}: the static links stay`);
      assert.equal(el.code.textContent, "");
    }
  }
});

test("the hall is named from the directory, linked to its place there, and nothing else comes from the link", () => {
  const search = LINK + "&n=Manos&name=" + encodeURIComponent("Μάνος") + "&inviter=Manos&u=uid123&v=venue-nax-galaxias";
  for (const [ua, touch] of [...ANDROID, ...IOS, ...DESKTOP]) {
    const { el } = run(ua, touch, search);
    assert.equal(el["hall-name"].textContent, "King 8");
    assert.equal(el["hall-name"].attributes.href, "../mpiliardo/athens/#venue-ath-king8");
    assert.equal(el["hall-city"].textContent, ", Αθήνα");
    assert.equal(el["hall-en"].textContent, "King 8, Athens");
    for (const id of IDS) {
      const said = el[id].textContent + JSON.stringify(el[id].attributes);
      assert.ok(!/Manos|Μάνος|uid123|Galaxias/.test(said), `${id}: ${said}`);
    }
  }
  assert.ok(read(`mpiliardo/athens/index.html`).includes('id="venue-ath-king8"'));
});

test("the page reads nothing from a database and writes nothing anywhere", () => {
  const source = read("f/invite.js");
  assert.doesNotMatch(source, /fetch\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon|firebase|firestore|import\(|importScripts/i);
  assert.doesNotMatch(source, /innerHTML|outerHTML|insertAdjacentHTML|document\.write|localStorage|sessionStorage|document\.cookie/);
  // h and c are the only parameters it reads.
  assert.deepEqual([...source.matchAll(/getAll\("([^"]+)"\)/g)].map((m) => m[1]).sort(), ["c", "h"]);
  assert.doesNotMatch(source, /\.get\("/);
});

test("every listed hall makes a good invite link", () => {
  for (const [id, [name]] of Object.entries(HALLS)) {
    const slug = id.replace(/^venue-/, "");
    const { el, loc } = run(UA.androidChrome, 5, `?h=${slug}&c=7KQ4M2XP`);
    assert.equal(loc.replaced[0], page.intentUrl(slug, "7KQ4M2XP"), id);
    assert.ok(loc.replaced[0].startsWith(`intent://invite/7KQ4M2XP?h=${slug}#Intent;scheme=rackup;`), id);
    assert.equal(el["hall-name"].textContent, name, id);
  }
});

test("in a browser the page wires itself with the directory and go.js's builders", () => {
  const elements = fakeDocument().elements;
  const loc = { search: LINK, replaced: [], replace(url) { this.replaced.push(url); } };
  const context = vm.createContext({
    document: { getElementById: (id) => elements[id] || null },
    navigator: { userAgent: UA.androidChrome, maxTouchPoints: 5 },
    location: loc, URLSearchParams
  });
  for (const file of ["m/halls.js", "go/go.js", "f/invite.js"]) vm.runInContext(read(file), context);
  assert.deepEqual(loc.replaced, [INVITE_INTENT]);
  assert.equal(elements["hall-name"].textContent, "King 8");
  // Without go.js the page keeps its static buttons rather than breaking.
  const bare = fakeDocument().elements;
  const still = { search: LINK, replaced: [], replace(url) { this.replaced.push(url); } };
  const lone = vm.createContext({
    document: { getElementById: (id) => bare[id] || null },
    navigator: { userAgent: UA.androidChrome, maxTouchPoints: 5 }, location: still, URLSearchParams
  });
  vm.runInContext(read("m/halls.js"), lone);
  vm.runInContext(read("f/invite.js"), lone);
  assert.deepEqual(still.replaced, []);
  assert.deepEqual(bare["app-store"].attributes, {});
});

test("the page is noindex, sends no referrer, previews as an invite and loads the three scripts in order", () => {
  assert.match(html, /<html lang="el">/);
  assert.match(html, /<meta name="robots" content="noindex">/);
  assert.match(html, /<meta name="referrer" content="no-referrer">/);
  assert.match(html, /<title>Πρόσκληση για μπιλιάρδο \| RackUp<\/title>/);
  assert.match(html, /<meta property="og:title" content="Πρόσκληση για μπιλιάρδο \| RackUp">/);
  assert.match(html, /<meta property="og:url" content="https:\/\/getrackup\.com\/f\/">/);
  for (const property of ["og:title", "og:description", "og:image", "og:url"]) {
    assert.match(html, new RegExp(`<meta property="${property}" content="[^"]+">`), property);
  }
  const image = html.match(/property="og:image" content="https:\/\/getrackup\.com\/([^"]+)"/)[1];
  assert.equal(image, read("m/index.html").match(/property="og:image" content="https:\/\/getrackup\.com\/([^"]+)"/)[1]);
  assert.ok(fs.existsSync(path.join(ROOT, image)), `og:image ${image} is not in the repo`);
  const scripts = [...html.matchAll(/<script\b[^>]*>/g)].map((m) => m[0]);
  // Deferred scripts run in order: the halls, then the store links, then the page.
  assert.deepEqual(scripts, ['<script src="../m/halls.js" defer>', '<script src="../go/go.js" defer>',
    '<script src="invite.js" defer>']);
  assert.doesNotMatch(html, /<img\b|<iframe\b|gtag|googletagmanager|analytics/i);
});

test("the head is the share page's: the same Content Security Policy and the one stylesheet", () => {
  const csp = (source) => source.match(/http-equiv="Content-Security-Policy" content="([^"]+)"/)[1];
  assert.equal(csp(html), csp(read("m/index.html")));
  assert.equal(csp(html), "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; " +
    "font-src 'self'; base-uri 'none'; form-action 'none'");
  const sheets = [...html.matchAll(/<link\b[^>]*rel="stylesheet"[^>]*>/g)].map((m) => m[0]);
  assert.deepEqual(sheets, ['<link rel="stylesheet" href="../assets/site.css">']);
  assert.doesNotMatch(html, /\sstyle="/, "the policy blocks inline styles");
  assert.match(read("assets/site.css"), /\.code-box\{/);
});

test("every element the script touches is there once, the hidden ones start hidden, and no button has an href", () => {
  for (const id of IDS) assert.equal((html.match(new RegExp(`id="${id}"`, "g")) || []).length, 1, id);
  for (const id of STARTS_HIDDEN) assert.match(html, new RegExp(`id="${id}"[^>]*\\bhidden\\b`), id);
  for (const id of ["open-app", "open-ios", "hall-name"]) {
    assert.match(html, new RegExp(`<a id="${id}"(?![^>]*href)[^>]*>`), `${id} has an href before the script runs`);
  }
  // go.js runs its own redirect only on a page with #opening.
  assert.doesNotMatch(html, /id="opening"/);
});

test("the static store links are the builders' links for a bad link", () => {
  const unescape = (s) => s.replace(/&amp;/g, "&");
  assert.equal(unescape(html.match(/id="app-store" href="([^"]+)"/)[1]), GENERAL_APP_STORE);
  assert.equal(unescape(html.match(/id="google-play" href="([^"]+)"/)[1]), GENERAL_PLAY);
  assert.equal(GENERAL_APP_STORE, page.appStoreUrl(null));
});

test("the page says what the approved design says, in Greek with the English beside it", () => {
  const said = [
    "<h1>Πρόσκληση για μπιλιάρδο</h1>",
    '<p class="tag" lang="en">An invite to play billiards</p>',
    "<span>Άνοιξε την πρόσκληση στο RackUp<small lang=\"en\">Open the invite in RackUp</small></span>",
    "Αν δεν έχεις την εφαρμογή, ανοίγει το Google Play και η πρόσκληση σε περιμένει μέσα.",
    '<span lang="en">No app yet? Google Play opens, and the invite waits for you inside.</span>',
    "<span>Το έχεις ήδη; Άνοιξε την πρόσκληση<small lang=\"en\">Already have it? Open the invite</small></span>",
    'Κωδικός πρόσκλησης · <span lang="en">Invite code</span>',
    "Μόλις κατεβάσεις το RackUp, πάτα ξανά τον σύνδεσμο στο μήνυμα, ή γράψε τον κωδικό στο «Έχω κωδικό πρόσκλησης».",
    '<span lang="en">Once you have RackUp, tap the link in the message again, or type the code under ' +
      "\"I have an invite code\".</span>"
  ];
  for (const line of said) assert.ok(html.includes(line), line);
  const badLink = html.match(/<p id="bad-link" class="note" hidden>([\s\S]*?)<\/p>/)[1];
  assert.match(badLink, /Ο σύνδεσμος δεν οδηγεί σε κάποια πρόσκληση/);
  assert.match(badLink, /<span lang="en">This link does not point to an invite\./);
});

test("the page stays out of the sitemap, is published, and has no dash", () => {
  assert.ok(!read("sitemap.xml").includes("/f/"), "sitemap.xml lists the invite page");
  const excluded = read("_config.yml").split("\n").map((l) => l.trim()).filter((l) => l.startsWith("- "));
  assert.ok(!excluded.some((l) => /^- f\/?$/.test(l)), "_config.yml excludes f/");
  const dashes = /[\u2012\u2013\u2014\u2015]/;
  for (const file of ["f/index.html", "f/invite.js", "tools/invite_page.test.js"]) {
    assert.ok(!dashes.test(read(file)), `${file} has a dash`);
  }
});
