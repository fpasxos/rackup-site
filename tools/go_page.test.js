// Tests for the store redirect page (go/index.html, go/go.js).
// Node 18 or newer, no packages: node --test tools/go_page.test.js
"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const ROOT = path.resolve(__dirname, "..");
const read = (file) => fs.readFileSync(path.join(ROOT, file), "utf8");
const page = require(path.join(ROOT, "go", "go.js"));
const HALLS = require(path.join(ROOT, "m", "halls.js"));
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
// A Meta ad also passes its placement, as utm_content after the campaign.
const META_REELS_PLAY = "https://play.google.com/store/apps/details?id=com.rackup.app" +
  "&referrer=utm_source%3Dmeta%26utm_medium%3Dpaid%26utm_campaign%3Dhalls%26utm_content%3Dig_reels";

// Every live ad adds p={{site_source_name}}&pl={{placement}}. These are the names Meta's docs and
// the 20 Oct link check give, Others being Meta's catch-all, and the tag each becomes.
const PLACEMENTS = [
  ["fb", "Facebook_Mobile_Feed", "fb_mobile_feed"],
  ["fb", "Facebook_Desktop_Feed", "fb_desktop_feed"],
  ["fb", "Facebook_Mobile_Reels", "fb_mobile_reels"],
  ["fb", "Facebook_Stories", "fb_stories"],
  ["fb", "Facebook_Right_Column", "fb_right_column"],
  ["fb", "Facebook_Instream_Video", "fb_instream_video"],
  ["fb", "Facebook_Marketplace", "fb_marketplace"],
  ["fb", "Facebook_Instant_Articles", "fb_instant_articles"],
  ["fb", "Others", "fb_others"],
  ["ig", "Instagram_Feed", "ig_feed"],
  ["ig", "Instagram_Reels", "ig_reels"],
  ["ig", "Instagram_Stories", "ig_stories"],
  ["ig", "Instagram_Explore", "ig_explore"],
  ["ig", "Others", "ig_others"],
  ["msg", "Messenger_Inbox", "msg_inbox"],
  ["msg", "Messenger_Home", "msg_home"],
  ["msg", "Messenger_Stories", "msg_stories"],
  ["an", "an", "an"]
];
// The ad set also served on the Facebook profile feed and in Instagram search, under names no
// source confirms. Any name in Meta's shape gets through the same way.
const MAYBE_PLACEMENTS = [
  ["fb", "Facebook_Profile_Feed", "fb_profile_feed"],
  ["ig", "Instagram_Search_Results", "ig_search_results"],
  ["ig", "Instagram_Explore_Grid_Home", "ig_explore_grid_home"],
  ["ig", "Instagram_Profile_Feed", "ig_profile_feed"]
];
const FBCLID = "IwZXh0bgNhZW0BMABhZGlkAasample_aem_Ab-12_cd";

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
  messengerAndroid: "Mozilla/5.0 (Linux; Android 13; Pixel 7 Build/TQ3A.230901.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/127.0.6533.103 Mobile Safari/537.36 [FB_IAB/Orca-Android;FBAV/450.0.0.38.108;]",
  viberAndroid: "Mozilla/5.0 (Linux; Android 14; SM-A546B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/128.0.6613.127 Mobile Safari/537.36 Viber/24.6.0.0",
  windowsChrome: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
};

// Starts as go/index.html does: the desktop block, the hall block and its in-app heading are hidden.
const HALL_IDS = ["hall-open", "hall-opening", "hall-get", "hall-name", "hall-city", "hall-en", "open-app", "stores-note"];
const STARTS_HIDDEN = ["desktop", "hall-open", "hall-get"];
function fakeDocument() {
  const elements = {};
  for (const id of ["app-store", "google-play", "opening", "desktop", ...HALL_IDS]) {
    elements[id] = {
      hidden: STARTS_HIDDEN.includes(id), attributes: {}, textContent: "",
      setAttribute(k, v) { this.attributes[k] = v; }
    };
  }
  return { elements, getElementById: (id) => elements[id] };
}
// Chrome and Samsung Internet jump to the app; an app's own browser (; wv) only shows the buttons.
const ANDROID_BROWSERS = ["androidChrome", "samsungInternet"];
const ANDROID_WEBVIEWS = ["instagramAndroid", "facebookAndroid", "messengerAndroid", "viberAndroid"];

function fakeLocation(search) {
  return { search, replaced: [], replace(url) { this.replaced.push(url); } };
}

// Without halls the page runs as it did before it knew any: as if m/halls.js had failed to load.
function run(userAgent, maxTouchPoints, search, halls) {
  const doc = fakeDocument();
  const loc = fakeLocation(search);
  page.wire(doc, { userAgent, maxTouchPoints }, loc, halls);
  return { doc, loc, hrefs: [doc.elements["app-store"].attributes.href, doc.elements["google-play"].attributes.href] };
}

// The app repo's link test parses these; change both together. The fallback is the poster's Play link.
const HALL_INTENT = "intent://venue/venue-nax-galaxias#Intent;scheme=rackup;package=com.rackup.app;" +
  "S.browser_fallback_url=https%3A%2F%2Fplay.google.com%2Fstore%2Fapps%2Fdetails%3Fid%3Dcom.rackup.app" +
  "%26referrer%3Dutm_source%253Dhall%2526utm_medium%253Dqr%2526utm_campaign%253Dnax-galaxias;end";
// The Rankings hall card's QR code: s=card.
const CARD_PLAY = "https://play.google.com/store/apps/details?id=com.rackup.app" +
  "&referrer=utm_source%3Dcard%26utm_medium%3Dqr%26utm_campaign%3Dath-king8";
const CARD_INTENT = "intent://venue/venue-ath-king8#Intent;scheme=rackup;package=com.rackup.app;" +
  "S.browser_fallback_url=https%3A%2F%2Fplay.google.com%2Fstore%2Fapps%2Fdetails%3Fid%3Dcom.rackup.app" +
  "%26referrer%3Dutm_source%253Dcard%2526utm_medium%253Dqr%2526utm_campaign%253Dath-king8;end";
const CARD_APP_STORE = "https://apps.apple.com/gr/app/apple-store/id6800614202?pt=12aB34&ct=card-ath-king8&mt=8";

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

// Without a storefront the web falls back to the US store, which has no RackUp: a 404 on a computer.
test("every App Store link names the Greek storefront unless its country's App Store sells RackUp", () => {
  const greek = "apps.apple.com/gr/app/";
  for (const token of ["", "12aB34", page.PROVIDER_TOKEN]) {
    for (const hall of [null, "nax-galaxias", "a".repeat(30), "cy", "cyprus-pool", "lefkosia-cy"]) {
      for (const source of [null, undefined, "meta", "ig", "fb", "card"]) {
        const url = page.buildAppStoreUrl(hall, token, source);
        assert.ok(url.startsWith("https://" + greek), `${url} names no storefront`);
      }
    }
  }
  const literal = /apps\.apple\.com\/[a-z]{2}\/app\/[^\s"'<>]*/g;
  const html = read("go/index.html").match(/apps\.apple\.com[^\s"'<>]*/g) || [];
  assert.ok(html.length > 0, "go/index.html has no App Store link");
  for (const url of html) assert.ok(url.startsWith(greek), `go/index.html: ${url} names no storefront`);
  assert.equal(read("go/go.js").match(literal), null, "go/go.js builds its links, it holds none");
});

test("only a country whose App Store sells RackUp is listed, and its slugs open that storefront", () => {
  // The app repo's data/countries.json has appStoreOpen true for Cyprus as well as Greece.
  assert.deepEqual(Object.keys(page.STOREFRONTS), ["cy"], "a country is listed only once its App Store sells RackUp");
  for (const [code, store] of Object.entries(page.STOREFRONTS)) {
    assert.match(code, /^[a-z]{2}$/);
    assert.equal(page.storefrontOf(`${code}-some-hall`), store);
    assert.equal(page.buildAppStoreUrl(`${code}-some-hall`, ""), `https://apps.apple.com/${store}/app/id6800614202`);
  }
  assert.equal(page.buildAppStoreUrl("cy-lefkosia-room9", "12aB34"),
    "https://apps.apple.com/cy/app/apple-store/id6800614202?pt=12aB34&ct=cy-lefkosia-room9&mt=8");
  assert.equal(page.buildAppStoreUrl("cy-lefkosia", "12aB34", "meta"),
    "https://apps.apple.com/cy/app/apple-store/id6800614202?pt=12aB34&ct=meta-cy-lefkosia&mt=8");
  page.STOREFRONTS.zz = "zz";
  try {
    assert.equal(page.storefrontOf("zz-some-hall"), "zz");
    assert.equal(page.buildAppStoreUrl("zz-some-hall", ""), "https://apps.apple.com/zz/app/id6800614202");
    assert.equal(page.buildAppStoreUrl("zz-some-hall", "12aB34", "meta"),
      "https://apps.apple.com/zz/app/apple-store/id6800614202?pt=12aB34&ct=meta-zz-some-hall&mt=8");
  } finally {
    delete page.STOREFRONTS.zz;
  }
  // An unlisted code, a code with no hyphen, and inherited object keys all stay Greek.
  for (const hall of [null, "nax-galaxias", "cy", "cyprus-pool", "lefkosia-cy", "cyy-x",
    "de-berlin", "constructor-x", "tostring-x", "proto-x"]) {
    assert.equal(page.storefrontOf(hall), "gr", String(hall));
  }
  // Play has no storefront in its links: a Cypriot slug changes only the campaign.
  assert.equal(page.playUrl("cy-lefkosia", "meta"), "https://play.google.com/store/apps/details?id=com.rackup.app" +
    "&referrer=utm_source%3Dmeta%26utm_medium%3Dpaid%26utm_campaign%3Dcy-lefkosia");
});

// hall_links.py names a hall's QR campaign after its id, so the id's country prefix is what picks the store.
test("every hall's slug opens its country's storefront when that is listed, else the Greek one", () => {
  const halls = JSON.parse(read("data/venues.json"));
  assert.ok(halls.some((hall) => page.STOREFRONTS[(hall.country || "GR").toLowerCase()]),
    "no hall is in a listed country: this check would pass on nothing");
  for (const hall of halls) {
    const slug = hall.id.replace(/^venue-/, "");
    const listed = page.STOREFRONTS[(hall.country || "GR").toLowerCase()];
    assert.equal(page.storefrontOf(slug), listed || "gr", hall.id);
  }
});

test("a Cypriot ad link opens the Cypriot App Store on iOS and Play on Android", () => {
  const search = "?s=meta&h=cy-lefkosia&fbclid=IwAR0abc";
  const apple = "https://apps.apple.com/cy/app/apple-store/id6800614202?pt=" + page.PROVIDER_TOKEN +
    "&ct=meta-cy-lefkosia&mt=8";
  const play = page.playUrl("cy-lefkosia", "meta");
  for (const [ua, touch] of [[UA.iphoneSafari, 5], [UA.facebookIos, 5], [UA.instagramIos, 5]]) {
    const { loc, hrefs } = run(ua, touch, search);
    assert.deepEqual(hrefs, [apple, play]);
    assert.deepEqual(loc.replaced, [apple]);
  }
  for (const ua of [UA.androidChrome, UA.facebookAndroid]) {
    assert.deepEqual(run(ua, 5, search).loc.replaced, [play]);
  }
  assert.deepEqual(run(UA.windowsChrome, 0, search).hrefs, [apple, play]);
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

test("only meta, ig, fb and card are sources, and only when s appears once", () => {
  for (const key of ["meta", "ig", "fb", "card"]) {
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
  assert.equal(page.campaignToken("a".repeat(25), "card"), "card-" + "a".repeat(25));
  assert.equal(page.campaignToken("a".repeat(26), "card"), "a".repeat(26));
  for (const source of ["meta", "ig", "fb", "card", null]) {
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

test("every placement Meta sends becomes one lowercase tag of at most 40 characters", () => {
  for (const [p, pl, tag] of [...PLACEMENTS, ...MAYBE_PLACEMENTS]) {
    const search = `?s=meta&h=halls&p=${p}&pl=${pl}&fbclid=${FBCLID}`;
    assert.equal(page.placementFrom(search), tag, search);
    assert.match(tag, /^[a-z0-9_]+$/);
    assert.ok(tag.length <= page.PLACEMENT_MAX, tag);
    assert.equal(page.isValidPlacement(tag), true, tag);
  }
  assert.equal(page.PLACEMENT_MAX, 40);
  // Meta's names arrive percent encoded or not, in any order among the other parameters.
  assert.equal(page.placementFrom("?pl=Instagram%5FReels&fbclid=x&p=ig&s=meta&h=halls"), "ig_reels");
  assert.equal(page.placementFrom("?p=IG&pl=INSTAGRAM_REELS"), "ig_reels");
  // p that pl already starts with is not doubled, and a pl of another platform keeps its word.
  assert.equal(page.placementFrom("?p=fb&pl=fb_feed"), "fb_feed");
  assert.equal(page.placementFrom("?p=an&pl=an_classic"), "an_classic");
  assert.equal(page.placementFrom("?p=ig&pl=Facebook_Mobile_Feed"), "ig_facebook_mobile_feed");
  assert.equal(page.placementFrom("?p=th&pl=Threads_Feed"), "th_threads_feed");
});

test("a missing, repeated or unexpanded p or pl leaves only the other, or nothing", () => {
  const cases = [
    ["?p=fb", "fb"],
    ["?pl=Instagram_Reels", "instagram_reels"],
    ["?p=fb&p=ig&pl=Instagram_Reels", "instagram_reels"],
    ["?p=ig&pl=Instagram_Reels&pl=Facebook_Stories", "ig"],
    ["?p=ig&pl=Instagram_Reels&pl=Instagram_Reels", "ig"],
    ["?p=fb&pl=%7B%7Bplacement%7D%7D", "fb"],
    ["?p=%7B%7Bsite_source_name%7D%7D&pl=Facebook_Stories", "facebook_stories"],
    ["?p=%7B%7Bsite_source_name%7D%7D&pl=%7B%7Bplacement%7D%7D", null],
    ["?p={{site_source_name}}&pl={{placement}}", null],
    ["?p=&pl=", null],
    ["?p&pl", null],
    ["?P=fb&PL=Instagram_Reels", null],
    ["?placement=Instagram_Reels&site_source_name=ig", null],
    ["?s=meta&h=halls&fbclid=" + FBCLID, null],
    ["", null],
    ["?", null],
    [undefined, null]
  ];
  for (const [search, tag] of cases) assert.equal(page.placementFrom(search), tag, String(search));
});

test("the sanitizer keeps Meta's names and drops anything else whole, never repairing it", () => {
  for (const [raw, tag] of [["Facebook_Mobile_Feed", "facebook_mobile_feed"], ["Others", "others"],
    ["an", "an"], ["a1_B2", "a1_b2"], ["A".repeat(40), "a".repeat(40)]]) {
    assert.equal(page.placementFrom(`?pl=${encodeURIComponent(raw)}`), tag, raw);
  }
  const dropped = [
    "", "_", "__", "_fb", "fb_", "fb__feed", "Facebook Mobile Feed", "Facebook-Mobile-Feed",
    "facebook.mobile.feed", "fb/feed", "fb:feed", "fb&utm_source=evil", "fb%26utm_source%3Devil",
    "fb=feed", "fb#feed", "{{placement}}", "[placement]", "<script>", "javascript:alert(1)",
    "\"fb\"", "fb'", "Ροή", "Ελληνικά", "Kelvin", "ſtories", "fb\n", "fb\t", "fb ",
    " fb", "fb\u0000", "a".repeat(41), "IwAR0abc-def", FBCLID
  ];
  for (const raw of dropped) {
    for (const key of ["p", "pl"]) {
      assert.equal(page.placementFrom(`?${key}=${encodeURIComponent(raw)}`), null, `${key} kept ${JSON.stringify(raw)}`);
    }
    assert.equal(page.placementFrom(`?p=fb&pl=${encodeURIComponent(raw)}`), "fb", `pl ${JSON.stringify(raw)}`);
  }
  for (const raw of ["?pl=Facebook+Mobile+Feed", "?pl=Facebook%20Mobile%20Feed", "?pl=%", "?pl=fb%", "?pl=%E2%80%94"]) {
    assert.equal(page.placementFrom(raw), null, raw);
  }
  // Each part may be 40 characters, and so may the tag joined from both, or there is none.
  assert.equal(page.placementFrom(`?p=${"a".repeat(19)}&pl=${"b".repeat(20)}`), `${"a".repeat(19)}_${"b".repeat(20)}`);
  assert.equal(page.placementFrom(`?p=${"a".repeat(20)}&pl=${"b".repeat(20)}`), null);
  assert.equal(page.placementFrom(`?p=fb&pl=Facebook_${"x".repeat(31)}`), `fb_${"x".repeat(31)}`);
  assert.equal(page.placementFrom(`?p=fb&pl=Facebook_${"x".repeat(32)}`), "fb");
});

test("isValidPlacement accepts only the sanitized form", () => {
  for (const ok of ["fb_mobile_feed", "ig_reels", "an", "others", "a1_b2", "a".repeat(40)]) {
    assert.equal(page.isValidPlacement(ok), true, ok);
  }
  for (const bad of ["Fb_feed", "IG_REELS", "fb-feed", "fb feed", "", "_", "fb_", "_fb", "fb__feed",
    "a".repeat(41), "fb%26x", null, undefined, 1, {}, ["fb"]]) {
    assert.equal(page.isValidPlacement(bad), false, String(bad));
  }
});

test("a Meta ad link carries its placement to Play as utm_content, after the campaign", () => {
  assert.equal(page.playUrl("halls", "meta", "ig_reels"), META_REELS_PLAY);
  const referrer = new URL(META_REELS_PLAY).searchParams.get("referrer");
  assert.equal(referrer, "utm_source=meta&utm_medium=paid&utm_campaign=halls&utm_content=ig_reels");
  assert.deepEqual([...new URLSearchParams(referrer).keys()], ["utm_source", "utm_medium", "utm_campaign", "utm_content"]);
  assert.equal(page.playUrl("ath-tonight", "meta", null), META_PLAY);
  assert.equal(page.playUrl("ath-tonight", "meta", undefined), META_PLAY);
  assert.equal(page.playUrl("ath-tonight", "meta"), META_PLAY);
});

test("on every phone and placement, Play gets the placement and the App Store link does not change", () => {
  const ios = [[UA.iphoneSafari, 5], [UA.facebookIos, 5], [UA.instagramIos, 5], [UA.ipadDesktopMode, 5]];
  const android = [[UA.androidChrome, 5], [UA.facebookAndroid, 5], [UA.instagramAndroid, 5], [UA.samsungInternet, 5]];
  const desktop = [[UA.windowsChrome, 0], [UA.macSafari, 0]];
  for (const slug of ["halls", "ath-tonight", "look-around", "how-it-works-reel", "cy-lefkosia"]) {
    for (const [p, pl, tag] of PLACEMENTS) {
      const search = `?s=meta&h=${slug}&p=${p}&pl=${pl}&fbclid=${FBCLID}`;
      const apple = page.appStoreUrl(slug, "meta");
      const play = page.playUrl(slug, "meta", tag);
      assert.equal(new URLSearchParams(new URL(play).searchParams.get("referrer")).get("utm_content"), tag);
      assert.deepEqual(run(UA.iphoneSafari, 5, search).hrefs[0], run(UA.iphoneSafari, 5, `?s=meta&h=${slug}`).hrefs[0]);
      for (const [ua, touch] of ios) {
        const { loc, hrefs } = run(ua, touch, search);
        assert.deepEqual(hrefs, [apple, play], search);
        assert.deepEqual(loc.replaced, [apple], search);
      }
      for (const [ua, touch] of android) {
        const { loc, hrefs } = run(ua, touch, search);
        assert.deepEqual(hrefs, [apple, play], search);
        assert.deepEqual(loc.replaced, [play], search);
      }
      for (const [ua, touch] of desktop) {
        const { doc, loc, hrefs } = run(ua, touch, search);
        assert.deepEqual(hrefs, [apple, play], search);
        assert.deepEqual(loc.replaced, [], search);
        assert.equal(doc.elements.desktop.hidden, false);
      }
    }
  }
});

test("no utm_content without p and pl, and none on bio, page, hall or unknown links", () => {
  // The paused carom and find-opponent ads have no URL parameters at all.
  for (const search of ["?s=meta&h=ath-tonight&fbclid=IwAR0abc", "?s=meta&h=carom", "?s=meta&h=find-opponent"]) {
    const { hrefs, loc } = run(UA.androidChrome, 5, search);
    assert.ok(!hrefs[1].includes("utm_content"), search);
    assert.ok(!loc.replaced[0].includes("utm_content"), search);
  }
  assert.deepEqual(run(UA.androidChrome, 5, "?s=meta&h=ath-tonight&fbclid=IwAR0abc").loc.replaced, [META_PLAY]);
  const unchanged = [
    ["?s=ig&h=bio&p=ig&pl=Instagram_Feed", IG_PLAY],
    ["?s=fb&h=page&p=fb&pl=Facebook_Mobile_Feed", FB_PLAY],
    ["?h=nax-galaxias&p=fb&pl=Facebook_Mobile_Feed", HALL_PLAY],
    ["?p=fb&pl=Facebook_Mobile_Feed", GENERAL_PLAY],
    ["?s=google&h=nax-galaxias&p=fb&pl=Facebook_Mobile_Feed", HALL_PLAY],
    ["?s=meta&s=meta&h=nax-galaxias&p=fb&pl=Facebook_Mobile_Feed", HALL_PLAY],
    ["?s=META&h=nax-galaxias&p=fb&pl=Facebook_Mobile_Feed", HALL_PLAY]
  ];
  for (const [search, play] of unchanged) {
    for (const [ua, touch] of [[UA.androidChrome, 5], [UA.facebookAndroid, 5], [UA.windowsChrome, 0]]) {
      assert.equal(run(ua, touch, search).hrefs[1], play, search);
    }
    assert.deepEqual(run(UA.androidChrome, 5, search).loc.replaced, [play], search);
  }
});

test("fbclid and every other parameter stay off both store links", () => {
  const extras = `&fbclid=${FBCLID}&utm_source=evil&utm_content=evil&gclid=G123evil&ad_id=120250102144070467` +
    "&campaign_id=999evil&_ga=1.2.3evil&user=evil";
  const search = "?s=meta&h=halls&p=ig&pl=Instagram_Reels" + extras;
  for (const [ua, touch] of [[UA.iphoneSafari, 5], [UA.instagramIos, 5], [UA.instagramAndroid, 5],
    [UA.androidChrome, 5], [UA.windowsChrome, 0]]) {
    const { loc, hrefs } = run(ua, touch, search);
    assert.deepEqual(hrefs, [page.appStoreUrl("halls", "meta"), META_REELS_PLAY]);
    for (const url of [...hrefs, ...loc.replaced]) {
      for (const leak of ["fbclid", "IwZX", "evil", "gclid", "120250102144070467", "_ga", "aem"]) {
        assert.ok(!url.includes(leak), `${url} carries ${leak}`);
      }
    }
  }
  // A pl that tries to add its own tags is dropped, and the referrer keeps one of each.
  for (const pl of ["Instagram_Reels&utm_source=evil", "Instagram_Reels%26utm_source%3Devil", "x&utm_campaign=evil"]) {
    const play = run(UA.androidChrome, 5, `?s=meta&h=halls&p=ig&pl=${encodeURIComponent(pl)}`).loc.replaced[0];
    const referrer = new URLSearchParams(new URL(play).searchParams.get("referrer"));
    assert.deepEqual([...referrer.entries()], [["utm_source", "meta"], ["utm_medium", "paid"],
      ["utm_campaign", "halls"], ["utm_content", "ig"]], pl);
  }
});

test("the builders refuse a bad placement, or a placement on a link that is not Meta's", () => {
  for (const bad of ["Instagram_Reels", "ig reels", "ig-reels", "", "_", "a".repeat(41), "fb_feed%26x", 1, {}]) {
    assert.throws(() => page.playUrl("halls", "meta", bad), /invalid placement/, String(bad));
  }
  for (const [hall, source] of [["bio", "ig"], ["page", "fb"], ["nax-galaxias", null], [null, undefined]]) {
    assert.throws(() => page.playUrl(hall, source, "fb_feed"), /a placement needs s=meta/, String(source));
  }
  assert.throws(() => page.playUrl("halls", "META", "fb_feed"), /invalid source/);
});

test("the page is noindex, previews well and loads no script but its own", () => {
  assert.match(html, /<html lang="el">/);
  assert.match(html, /<meta name="robots" content="noindex">/);
  assert.match(html, /<meta name="referrer" content="no-referrer">/);
  for (const property of ["og:title", "og:description", "og:image", "og:url"]) {
    assert.match(html, new RegExp(`<meta property="${property}" content="[^"]+">`), property);
  }
  assert.match(html, /<meta property="og:url" content="https:\/\/getrackup\.com\/go\/">/);
  assert.match(html, /<meta property="og:image" content="https:\/\/getrackup\.com\/assets\/og-card-2026-11-12\.png">/);
  assert.match(html, /<meta name="twitter:card" content="summary_large_image">/);
  const image = html.match(/property="og:image" content="https:\/\/getrackup\.com\/([^"]+)"/)[1];
  assert.ok(fs.existsSync(path.join(ROOT, image)), `og:image ${image} is not in the repo`);
  const scripts = [...html.matchAll(/<script\b[^>]*>/g)].map((m) => m[0]);
  // The halls first: deferred scripts run in order, and go.js names a hall from them.
  assert.deepEqual(scripts, ['<script src="../m/halls.js" defer>', '<script src="go.js" defer>']);
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

test("on Android a listed hall's poster opens the app on that hall, with the poster's Play link as the fallback", () => {
  for (const name of ANDROID_BROWSERS) {
    const { doc, loc, hrefs } = run(UA[name], 5, "?h=nax-galaxias", HALLS);
    const el = doc.elements;
    assert.deepEqual(loc.replaced, [HALL_INTENT], name);
    assert.deepEqual(hrefs, [page.appStoreUrl("nax-galaxias"), HALL_PLAY]);
    // Chrome may refuse to open an app without a tap, so the page keeps the hall and a button.
    assert.equal(el["open-app"].attributes.href, HALL_INTENT);
    assert.equal(el["hall-open"].hidden, false);
    assert.equal(el["hall-opening"].hidden, false, "Opening RackUp, while it does");
    assert.equal(el["hall-get"].hidden, true);
    assert.equal(el.opening.hidden, true, "it opens RackUp, not the app store");
    assert.equal(el.desktop.hidden, true);
    assert.equal(el["app-store"].hidden, true, "an Android phone sees only Google Play");
    assert.equal(el["google-play"].hidden, false);
    assert.equal(el["stores-note"].hidden, true);
  }
  assert.equal(page.venueIntentUrl("nax-galaxias"), HALL_INTENT);
});

test("in an app's own browser the page jumps nowhere, and shows the hall, its open button and Google Play", () => {
  for (const [search, intent, play] of [["?h=nax-galaxias", HALL_INTENT, HALL_PLAY], ["?h=ath-king8&s=card", CARD_INTENT, CARD_PLAY]]) {
    for (const name of ANDROID_WEBVIEWS) {
      const { doc, loc, hrefs } = run(UA[name], 5, search, HALLS);
      const el = doc.elements;
      assert.deepEqual(loc.replaced, [], `${name} ${search}: an app link here can end on an error page`);
      assert.equal(el["open-app"].attributes.href, intent, name);
      assert.equal(hrefs[1], play, name);
      assert.equal(el["hall-open"].hidden, false, name);
      assert.equal(el["google-play"].hidden, false, name);
      assert.equal(el["app-store"].hidden, true, name);
      assert.equal(el["hall-opening"].hidden, true, `${name}: nothing opens by itself here`);
      assert.equal(el["hall-get"].hidden, false, name);
      assert.equal(el.opening.hidden, true, name);
    }
  }
});

test("only an Android app's own browser counts as one", () => {
  for (const name of ANDROID_WEBVIEWS) assert.equal(page.isWebView(UA[name]), true, name);
  for (const name of [...ANDROID_BROWSERS, "iphoneSafari", "iphoneChrome", "instagramIos", "facebookIos",
    "ipadDesktopMode", "macSafari", "windowsChrome"]) {
    assert.equal(page.isWebView(UA[name]), false, name);
  }
  for (const ua of [undefined, null, "", "wv", "Mozilla/5.0 (Linux; Android 14; wv-like) Chrome"]) {
    assert.equal(page.isWebView(ua), false, String(ua));
  }
});

test("the fallback decodes once to the poster's or the card's Play link, referrer and all", () => {
  const fallback = (intent) => decodeURIComponent(intent.match(/;S\.browser_fallback_url=([^;]*);end$/)[1]);
  assert.equal(fallback(HALL_INTENT), HALL_PLAY);
  assert.equal(fallback(CARD_INTENT), CARD_PLAY);
  const referrer = (url) => new URL(url).searchParams.get("referrer");
  assert.equal(referrer(fallback(HALL_INTENT)), "utm_source=hall&utm_medium=qr&utm_campaign=nax-galaxias");
  assert.equal(referrer(fallback(CARD_INTENT)), "utm_source=card&utm_medium=qr&utm_campaign=ath-king8");
});

test("the hall and its city come from the directory, never from the link", () => {
  const search = "?h=nax-galaxias&name=" + encodeURIComponent("Call 6900000000") + "&n=Fake&v=venue-ath-king8";
  const el = run(UA.androidChrome, 5, search, HALLS).doc.elements;
  assert.equal(el["hall-name"].textContent, "Galaxias Billiards");
  assert.equal(el["hall-name"].attributes.href, "../mpiliardo/naxos/#venue-nax-galaxias");
  assert.equal(el["hall-city"].textContent, ", Νάξος");
  assert.equal(el["hall-en"].textContent, "Galaxias Billiards, Naxos");
  for (const id of HALL_IDS) assert.ok(!/6900000000|Fake|King/.test(el[id].textContent), id);
  assert.doesNotMatch(read("go/go.js"), /innerHTML|outerHTML|insertAdjacentHTML|document\.write/);
});

test("every listed hall's poster opens that hall, named and linked to its place in the directory", () => {
  for (const [id, [name, , cityEn, slug]] of Object.entries(HALLS)) {
    const hall = id.replace(/^venue-/, "");
    const { doc, loc } = run(UA.androidChrome, 5, `?h=${hall}`, HALLS);
    assert.deepEqual(loc.replaced, [page.venueIntentUrl(hall)], id);
    assert.ok(loc.replaced[0].startsWith(`intent://venue/${id}#Intent;scheme=rackup;package=com.rackup.app;`), id);
    assert.equal(doc.elements["hall-name"].textContent, name, id);
    assert.equal(doc.elements["hall-en"].textContent, `${name}, ${cityEn}`, id);
    assert.equal(doc.elements["hall-name"].attributes.href, `../mpiliardo/${slug}/#${id}`, id);
    assert.ok(read(`mpiliardo/${slug}/index.html`).includes(`id="${id}"`), `${id} is not anchored on its page`);
  }
});

test("the Rankings card's QR, s=card, tags card and qr, ct card-<slug>, and opens the hall like a poster", () => {
  assert.equal(page.playUrl("ath-king8", "card"), CARD_PLAY);
  assert.equal(page.buildAppStoreUrl("ath-king8", "12aB34", "card"), CARD_APP_STORE);
  assert.equal(page.venueIntentUrl("ath-king8", "card"), CARD_INTENT);
  for (const name of ANDROID_BROWSERS) {
    const { doc, loc, hrefs } = run(UA[name], 5, "?h=ath-king8&s=card", HALLS);
    assert.deepEqual(loc.replaced, [CARD_INTENT], name);
    assert.deepEqual(hrefs, [page.appStoreUrl("ath-king8", "card"), CARD_PLAY]);
    assert.equal(doc.elements["open-app"].attributes.href, CARD_INTENT);
    assert.equal(doc.elements["hall-open"].hidden, false);
  }
  // A card whose hall is not listed is tagged the same way and goes to Play, as any other link does.
  assert.deepEqual(run(UA.androidChrome, 5, "?h=ath-tonight&s=card", HALLS).loc.replaced,
    [page.playUrl("ath-tonight", "card")]);
  assert.equal(new URL(page.playUrl(null, "card")).searchParams.get("referrer"),
    "utm_source=card&utm_medium=qr&utm_campaign=general");
});

test("iPhones and computers are unchanged for a listed hall: the App Store at once, or both buttons", () => {
  for (const [search, hall, source] of [["?h=nax-galaxias", "nax-galaxias", null], ["?h=ath-king8&s=card", "ath-king8", "card"]]) {
    for (const [ua, touch] of [[UA.iphoneSafari, 5], [UA.ipadDesktopMode, 5], [UA.instagramIos, 5]]) {
      const listed = run(ua, touch, search, HALLS);
      assert.deepEqual(listed.loc.replaced, [page.appStoreUrl(hall, source)], search);
      assert.deepEqual(listed.hrefs, run(ua, touch, search).hrefs, search);
      assert.equal(listed.doc.elements["hall-open"].hidden, true);
      assert.equal(listed.doc.elements.opening.hidden, false);
    }
    for (const [ua, touch] of [[UA.macSafari, 0], [UA.windowsChrome, 0]]) {
      const { doc, loc, hrefs } = run(ua, touch, search, HALLS);
      assert.deepEqual(loc.replaced, [], search);
      assert.deepEqual(hrefs, [page.appStoreUrl(hall, source), page.playUrl(hall, source)]);
      assert.equal(doc.elements.desktop.hidden, false);
      assert.equal(doc.elements["hall-open"].hidden, true);
      assert.equal(doc.elements["app-store"].hidden, false);
    }
  }
});

test("an ad or bio link, an unlisted or repeated h, or no hall list keeps Android's Play redirect", () => {
  const cases = [
    ["?s=meta&h=nax-galaxias", HALLS, page.playUrl("nax-galaxias", "meta")],
    ["?s=ig&h=nax-galaxias", HALLS, page.playUrl("nax-galaxias", "ig")],
    ["?s=fb&h=nax-galaxias", HALLS, page.playUrl("nax-galaxias", "fb")],
    ["?s=meta&h=nax-galaxias&p=ig&pl=Instagram_Reels", HALLS, page.playUrl("nax-galaxias", "meta", "ig_reels")],
    ["?h=ath-tonight", HALLS, page.playUrl("ath-tonight")],
    ["?h=nax-galaxias&h=ath-king8", HALLS, GENERAL_PLAY],
    ["?h=" + encodeURIComponent("nax-galaxias#Intent;end"), HALLS, GENERAL_PLAY],
    ["", HALLS, GENERAL_PLAY],
    ["?h=nax-galaxias", undefined, HALL_PLAY],
    ["?h=nax-galaxias", {}, HALL_PLAY],
    ["?h=nax-galaxias", null, HALL_PLAY]
  ];
  for (const [search, halls, play] of cases) {
    for (const ua of [UA.androidChrome, UA.facebookAndroid]) {
      const { doc, loc } = run(ua, 5, search, halls);
      assert.deepEqual(loc.replaced, [play], search);
      assert.equal(doc.elements["hall-open"].hidden, true, search);
      assert.equal(doc.elements["open-app"].attributes.href, undefined, search);
      assert.equal(doc.elements["app-store"].hidden, false, search);
    }
  }
});

test("an unknown or repeated s is no s at all, so a listed hall still opens", () => {
  for (const extra of ["s=google", "s=", "s", "s=meta&s=ig", "s=card&s=card", "S=card", "s=__proto__"]) {
    assert.deepEqual(run(UA.androidChrome, 5, `?h=nax-galaxias&${extra}`, HALLS).loc.replaced, [HALL_INTENT], extra);
  }
});

test("the hall builder refuses anything but a valid hall from a poster or a card", () => {
  for (const bad of [null, undefined, "", "NAX", "nax galaxias", "a".repeat(31), "nax;end", "nax#Intent"]) {
    assert.throws(() => page.venueIntentUrl(bad), /invalid hall slug/, String(bad));
  }
  for (const source of ["meta", "ig", "fb"]) {
    assert.throws(() => page.venueIntentUrl("nax-galaxias", source), /only a poster or a card opens a hall/, source);
  }
  assert.throws(() => page.venueIntentUrl("nax-galaxias", "google"), /invalid source/);
});

test("every listed hall keeps its card- and f- prefix within Apple's 30 characters", () => {
  for (const id of Object.keys(HALLS)) {
    const hall = id.replace(/^venue-/, "");
    assert.equal(page.campaignToken(hall, "card"), `card-${hall}`, id);
    assert.equal(page.campaignToken(hall, "f"), `f-${hall}`, id);
  }
});

test("taggedAppStoreUrl tags another page's installs with its prefix, by the same storefront and rule", () => {
  const pt = page.PROVIDER_TOKEN;
  const store = (front, ct) => `https://apps.apple.com/${front}/app/apple-store/id6800614202?pt=${pt}&ct=${ct}&mt=8`;
  assert.equal(page.taggedAppStoreUrl("ath-king8", "f"), store("gr", "f-ath-king8"));
  assert.equal(page.taggedAppStoreUrl("cy-lim-century", "f"), store("cy", "f-cy-lim-century"));
  assert.equal(page.taggedAppStoreUrl(null, "f"), store("gr", "f-general"));
  assert.equal(page.taggedAppStoreUrl("a".repeat(29), "f"), store("gr", "a".repeat(29)));
  for (const bad of ["", "F", "f-x", "f&ct=evil", "f1", "f ", null, undefined, 1]) {
    assert.throws(() => page.taggedAppStoreUrl("ath-king8", bad), /invalid ct prefix/, String(bad));
  }
  assert.throws(() => page.taggedAppStoreUrl("ath king8", "f"), /invalid hall slug/);
});

// go.js as a browser runs it: a classic script, no module, the page's globals around it.
function loadInBrowser(ids, search, halls) {
  const elements = {};
  for (const id of ids) {
    elements[id] = {
      hidden: id === "desktop" || id === "hall-open", attributes: {}, textContent: "",
      setAttribute(k, v) { this.attributes[k] = v; }
    };
  }
  const loc = fakeLocation(search);
  const win = {
    document: { getElementById: (id) => elements[id] || null },
    navigator: { userAgent: UA.androidChrome, maxTouchPoints: 5 },
    location: loc, URLSearchParams, RACKUP_HALLS: halls
  };
  vm.runInNewContext(read("go/go.js"), win);
  return { win, loc, elements };
}

test("in a browser go.js runs the go page, and on any other page only lends its builders", () => {
  const GO_PAGE = ["app-store", "google-play", "opening", "desktop", ...HALL_IDS];
  const go = loadInBrowser(GO_PAGE, "?h=nax-galaxias", HALLS);
  assert.deepEqual(go.loc.replaced, [HALL_INTENT]);
  assert.equal(go.elements["hall-open"].hidden, false);
  // The invite page loads go.js for its store links and has no #opening: nothing moves there.
  const other = loadInBrowser(["app-store", "google-play"], "?h=nax-galaxias", HALLS);
  assert.deepEqual(other.loc.replaced, []);
  assert.deepEqual(other.elements["app-store"].attributes, {});
  assert.equal(other.win.RACKUP_GO.taggedAppStoreUrl("ath-king8", "f"), page.taggedAppStoreUrl("ath-king8", "f"));
  assert.equal(other.win.RACKUP_GO.platformOf(UA.iphoneSafari, 5), "ios");
  // Without m/halls.js the go page redirects as it did before it knew any hall.
  assert.deepEqual(loadInBrowser(GO_PAGE, "?h=nax-galaxias").loc.replaced, [HALL_PLAY]);
});

test("the hall block starts hidden and says what the approved page says, around a button the script fills", () => {
  assert.ok(html.includes('<div id="hall-open" hidden>'), "#hall-open must start hidden");
  const block = html.split('<div id="hall-open" hidden>')[1].split('<div class="stores"')[0];
  const part = (id, hidden) => block.match(new RegExp(`<div id="${id}"${hidden ? " hidden" : ""}>([\\s\\S]*?)</div>`));
  const opening = part("hall-opening", false);
  assert.ok(opening, "#hall-opening must start visible");
  assert.match(opening[1], /<h1>Ανοίγει το RackUp…<\/h1>/);
  assert.match(opening[1], /<p class="tag" lang="en">Opening RackUp…<\/p>/);
  // An app's own browser jumps nowhere, so its heading says what the page offers instead.
  const get = part("hall-get", true);
  assert.ok(get, "#hall-get must start hidden");
  assert.match(get[1], /<h1>Κατέβασε το RackUp<\/h1>/);
  assert.match(get[1], /<p class="tag" lang="en">Get RackUp<\/p>/);
  assert.match(block, /<span>Άνοιξε την αίθουσα στο RackUp<small lang="en">Open the hall in RackUp<\/small><\/span>/);
  assert.match(block, /Αν δεν έχεις την εφαρμογή, ανοίγει το Google Play\./);
  assert.match(block, /<span lang="en">No app yet\? Google Play opens instead\.<\/span>/);
  assert.match(html, /<a id="open-app"(?![^>]*href)[^>]*>/, "open-app must have no href until the script sets one");
  for (const id of HALL_IDS) assert.equal((html.match(new RegExp(`id="${id}"`, "g")) || []).length, 1, id);
});
