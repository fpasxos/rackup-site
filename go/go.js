// Store redirect for go/index.html, the page printed QR codes point at. The pure functions
// are exported so tools/go_page.test.js can run them under node; the DOM part runs only in a browser.
(function () {
  "use strict";

  var APP_STORE_ID = "6800614202";
  // The pt value from App Store Connect, App Analytics, Campaigns. Empty means untagged links.
  var PROVIDER_TOKEN = "129299799";
  var GENERAL = "general";
  // A hall slug as hall_links.py derives it, at most 30 characters for Apple's ct.
  var HALL = /^[a-z0-9]+(-[a-z0-9]+)*$/;
  var HALL_MAX = 30;
  var TOKEN = /^[A-Za-z0-9]+$/;
  // Ads and bios add s, so their installs are not filed as hall QR scans; h is then the campaign.
  // The key also prefixes Apple's ct. Any other s, or a repeated one, is ignored.
  // Only an ad link carries Meta's placement, and only to Play (placementFrom, below).
  var SOURCES = {
    meta: { source: "meta", medium: "paid", placement: true },
    ig: { source: "instagram", medium: "social" },
    fb: { source: "facebook", medium: "social" }
  };
  // Lowercase words joined by single underscores, as Play's utm_content: fb_mobile_feed, ig_reels.
  var PLACEMENT = /^[a-z0-9]+(_[a-z0-9]+)*$/;
  var PLACEMENT_MAX = 40;
  // The platform word Meta's placement starts with, for the p it fills in.
  var PLATFORMS = { fb: "facebook", ig: "instagram", msg: "messenger" };

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

  function takesPlacement(source) {
    return isValidSource(source) && SOURCES[source].placement === true;
  }

  function isValidPlacement(placement) {
    return typeof placement === "string" && placement.length <= PLACEMENT_MAX && PLACEMENT.test(placement);
  }

  // One p or pl, ASCII checked before lowercasing. Anything else is dropped whole, never repaired,
  // so an unexpanded {{placement}} or a pasted value adds nothing.
  function placementPart(search, key) {
    var all = new URLSearchParams(search || "").getAll(key);
    var value = all.length === 1 && /^[A-Za-z0-9_]+$/.test(all[0]) ? all[0].toLowerCase() : null;
    return isValidPlacement(value) ? value : null;
  }

  // Meta's p={{site_source_name}} and pl={{placement}} as one tag: fb with Facebook_Mobile_Feed is
  // fb_mobile_feed, ig with Instagram_Reels is ig_reels. Only these two are read, never fbclid.
  function placementFrom(search) {
    var site = placementPart(search, "p");
    var spot = placementPart(search, "pl");
    var content;
    if (site === null || spot === null) {
      content = spot === null ? site : spot;
    } else if (spot === site || spot.indexOf(site + "_") === 0) {
      content = spot;
    } else {
      var word = Object.prototype.hasOwnProperty.call(PLATFORMS, site) ? PLATFORMS[site] + "_" : null;
      content = site + "_" + (word !== null && spot.indexOf(word) === 0 ? spot.slice(word.length) : spot);
    }
    return isValidPlacement(content) ? content : null;
  }

  // A placement goes only on a Meta ad link, and only in its sanitized form.
  function checkPlacement(placement, source) {
    if (placement == null) return;
    if (!takesPlacement(source)) throw new Error("a placement needs s=meta");
    if (!isValidPlacement(placement)) throw new Error("invalid placement");
  }

  // Without a source, the app repo's store-assets/hall-links/hall_links.py builds the same Play
  // and tagged App Store URLs. Links with a source are built only here.
  function playUrl(hall, source, placement) {
    checkHall(hall);
    checkSource(source);
    checkPlacement(placement, source);
    var tag = source == null ? null : SOURCES[source];
    var utmSource = tag ? tag.source : hall === null ? "share" : "hall";
    var medium = tag ? tag.medium : "qr";
    return "https://play.google.com/store/apps/details?id=com.rackup.app&referrer=utm_source%3D" +
      utmSource + "%26utm_medium%3D" + medium + "%26utm_campaign%3D" + (hall === null ? GENERAL : hall) +
      (placement == null ? "" : "%26utm_content%3D" + placement);
  }

  // Apple allows a ct of 30 characters (HALL_MAX). When the source prefix would pass that, ct is
  // the bare slug, so the install still lands in the campaign, only without its source.
  function campaignToken(hall, source) {
    var campaign = hall === null ? GENERAL : hall;
    var tagged = source == null ? campaign : source + "-" + campaign;
    return tagged.length <= HALL_MAX ? tagged : campaign;
  }

  // Every link names a storefront, or it falls back to the US store and 404s on a computer. A slug
  // that starts with an open country's code and a hyphen (cy-...) opens that country's store; Greek
  // slugs have no prefix. Mirrors data/countries.json in the app repo: a new country is one entry.
  var STOREFRONTS = { cy: "cy" };
  var DEFAULT_STOREFRONT = "gr";

  function storefrontOf(hall) {
    var dash = hall === null ? -1 : hall.indexOf("-");
    var code = dash > 0 ? hall.slice(0, dash) : null;
    return code !== null && Object.prototype.hasOwnProperty.call(STOREFRONTS, code) ? STOREFRONTS[code] : DEFAULT_STOREFRONT;
  }

  function buildAppStoreUrl(hall, token, source) {
    checkHall(hall);
    checkSource(source);
    var store = "https://apps.apple.com/" + storefrontOf(hall) + "/app/";
    if (!token) return store + "id" + APP_STORE_ID;
    if (!TOKEN.test(token)) throw new Error("invalid provider token");
    return store + "apple-store/id" + APP_STORE_ID + "?pt=" + token +
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
  // Apple's ct stays per ad: a placement would split its counts under Apple's threshold of 5.
  function wire(doc, nav, loc) {
    var hall = hallFrom(loc.search);
    var source = sourceFrom(loc.search);
    var placement = takesPlacement(source) ? placementFrom(loc.search) : null;
    var apple = appStoreUrl(hall, source);
    var play = playUrl(hall, source, placement);
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
    PLACEMENT_MAX: PLACEMENT_MAX,
    isValidPlacement: isValidPlacement,
    placementFrom: placementFrom,
    playUrl: playUrl,
    campaignToken: campaignToken,
    STOREFRONTS: STOREFRONTS,
    storefrontOf: storefrontOf,
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
