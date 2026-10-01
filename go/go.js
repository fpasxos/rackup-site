// Store redirect for go/index.html, the page printed QR codes point at. The pure functions
// are exported so tools/go_page.test.js can run them under node; the DOM part runs only in a browser.
(function () {
  "use strict";

  var APP_STORE_ID = "6800614202";
  // The pt value from App Store Connect, App Analytics, Campaigns. Empty means untagged links.
  var PROVIDER_TOKEN = "";
  var GENERAL = "general";
  // A hall slug as hall_links.py derives it, at most 30 characters for Apple's ct.
  var HALL = /^[a-z0-9]+(-[a-z0-9]+)*$/;
  var HALL_MAX = 30;
  var TOKEN = /^[A-Za-z0-9]+$/;
  // Ads and bios add s, so their installs are not filed as hall QR scans; h is then the campaign.
  // The key also prefixes Apple's ct. Any other s, or a repeated one, is ignored.
  var SOURCES = {
    meta: { source: "meta", medium: "paid" },
    ig: { source: "instagram", medium: "social" },
    fb: { source: "facebook", medium: "social" }
  };

  function isValidHall(hall) {
    return typeof hall === "string" && hall.length <= HALL_MAX && HALL.test(hall);
  }

  // A repeated h is ambiguous, so it counts as the general code like any other bad value.
  function hallFrom(search) {
    var all = new URLSearchParams(search || "").getAll("h");
    return all.length === 1 && isValidHall(all[0]) ? all[0] : null;
  }

  function checkHall(hall) {
    if (hall !== null && !isValidHall(hall)) throw new Error("invalid hall slug");
  }

  // hasOwnProperty, so s=constructor or s=__proto__ is not a source.
  function isValidSource(source) {
    return typeof source === "string" && Object.prototype.hasOwnProperty.call(SOURCES, source);
  }

  function sourceFrom(search) {
    var all = new URLSearchParams(search || "").getAll("s");
    return all.length === 1 && isValidSource(all[0]) ? all[0] : null;
  }

  // null or undefined means no source: the hall QR links, unchanged.
  function checkSource(source) {
    if (source != null && !isValidSource(source)) throw new Error("invalid source");
  }

  // Without a source, the app repo's store-assets/hall-links/hall_links.py builds the same Play
  // and tagged App Store URLs. Links with a source are built only here.
  function playUrl(hall, source) {
    checkHall(hall);
    checkSource(source);
    var tag = source == null ? null : SOURCES[source];
    var utmSource = tag ? tag.source : hall === null ? "share" : "hall";
    var medium = tag ? tag.medium : "qr";
    return "https://play.google.com/store/apps/details?id=com.rackup.app&referrer=utm_source%3D" +
      utmSource + "%26utm_medium%3D" + medium + "%26utm_campaign%3D" + (hall === null ? GENERAL : hall);
  }

  // Apple allows a ct of 30 characters (HALL_MAX). When the source prefix would pass that, ct is
  // the bare slug, so the install still lands in the campaign, only without its source.
  function campaignToken(hall, source) {
    var campaign = hall === null ? GENERAL : hall;
    var tagged = source == null ? campaign : source + "-" + campaign;
    return tagged.length <= HALL_MAX ? tagged : campaign;
  }

  // RackUp is only in the Greek store, so the plain link needs /gr/ or it 404s on the web.
  function buildAppStoreUrl(hall, token, source) {
    checkHall(hall);
    checkSource(source);
    if (!token) return "https://apps.apple.com/gr/app/id" + APP_STORE_ID;
    if (!TOKEN.test(token)) throw new Error("invalid provider token");
    return "https://apps.apple.com/app/apple-store/id" + APP_STORE_ID + "?pt=" + token +
      "&ct=" + campaignToken(hall, source) + "&mt=8";
  }

  function appStoreUrl(hall, source) {
    return buildAppStoreUrl(hall, PROVIDER_TOKEN, source);
  }

  // iPadOS Safari asks for desktop sites by default and then claims to be a Mac with a touch screen.
  function platformOf(userAgent, maxTouchPoints) {
    var ua = userAgent || "";
    if (/iPhone|iPad|iPod/.test(ua)) return "ios";
    if (/Macintosh/.test(ua) && maxTouchPoints > 1) return "ios";
    if (/Android/i.test(ua)) return "android";
    return "other";
  }

  // The buttons always carry the tagged links, so the page still works if a store fails to open.
  function wire(doc, nav, loc) {
    var hall = hallFrom(loc.search);
    var source = sourceFrom(loc.search);
    var apple = appStoreUrl(hall, source);
    var play = playUrl(hall, source);
    doc.getElementById("app-store").setAttribute("href", apple);
    doc.getElementById("google-play").setAttribute("href", play);
    var platform = platformOf(nav.userAgent, nav.maxTouchPoints);
    if (platform === "ios") {
      loc.replace(apple);
    } else if (platform === "android") {
      loc.replace(play);
    } else {
      // Nothing opens here, so "Opening the app store" gives way to "Get RackUp".
      doc.getElementById("opening").hidden = true;
      doc.getElementById("desktop").hidden = false;
    }
  }

  var api = {
    PROVIDER_TOKEN: PROVIDER_TOKEN,
    isValidHall: isValidHall,
    hallFrom: hallFrom,
    isValidSource: isValidSource,
    sourceFrom: sourceFrom,
    playUrl: playUrl,
    campaignToken: campaignToken,
    buildAppStoreUrl: buildAppStoreUrl,
    appStoreUrl: appStoreUrl,
    platformOf: platformOf,
    wire: wire
  };
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else if (typeof document !== "undefined") {
    wire(document, navigator, location);
  }
})();
