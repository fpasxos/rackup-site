// Invite page logic for f/index.html, https://getrackup.com/f/?h=<hall>&c=<code> (app 2.4.9). The pure
// functions are exported so tools/invite_page.test.js can run them under node; the DOM part runs only
// in a browser. It reads h and c and nothing else, and asks no server: m/halls.js names the hall.
(function (root) {
  "use strict";

  // go.js builds the store links and tells the platform: loaded before this file, required under node.
  var go = typeof module === "object" && module.exports ? require("../go/go.js") : root.RACKUP_GO;
  var PACKAGE = "com.rackup.app";
  var PLAY = "https://play.google.com/store/apps/details?id=" + PACKAGE + "&referrer=";
  var DIRECTORY = "../mpiliardo/";
  // The app's invite code: 8 of 31 symbols, with no 0, 1, I, L or O. The app and the server use it too.
  var CODE = /^[2-9A-HJKMNP-Z]{8}$/;
  // Apple's ct for an invite is f-<hall>.
  var CT_PREFIX = "f";

  function isValidCode(code) {
    return typeof code === "string" && CODE.test(code);
  }

  function checkInvite(slug, code) {
    if (!go.isValidHall(slug)) throw new Error("invalid hall slug");
    if (!isValidCode(code)) throw new Error("invalid invite code");
  }

  // One h that names a listed hall and one c, or null: a repeated value is ambiguous.
  function inviteFrom(search, halls) {
    var params = new URLSearchParams(search || "");
    var slugs = params.getAll("h");
    var codes = params.getAll("c");
    if (slugs.length !== 1 || codes.length !== 1 || !isValidCode(codes[0])) return null;
    var row = go.listedHall(halls, slugs[0]);
    if (row === null) return null;
    return {
      code: codes[0],
      slug: slugs[0],
      hall: { id: "venue-" + slugs[0], name: row[0], city: { el: row[1], en: row[2] }, citySlug: row[3] }
    };
  }

  // «7KQ4 M2XP»: two groups of four, as the app shows it.
  function codeText(code) {
    if (!isValidCode(code)) throw new Error("invalid invite code");
    return code.slice(0, 4) + " " + code.slice(4);
  }

  // The referrer the app reads once after an install. With no hall and no code, a bad link's.
  function playUrl(slug, code) {
    var tags = "utm_source%3Dfriend%26utm_medium%3Dinvite%26utm_campaign%3D";
    if (slug === null && code === null) return PLAY + tags + "general";
    if (slug === null) throw new Error("a code needs its hall");
    if (code === null) throw new Error("a hall needs its code");
    checkInvite(slug, code);
    return PLAY + tags + slug + "%26rackup_invite%3D" + code;
  }

  // The link iPhones open: app 2.4.9 registers rackup://, older ones do not.
  function appUrl(slug, code) {
    checkInvite(slug, code);
    return "rackup://invite/" + code + "?h=" + slug;
  }

  // Chrome opens the same link in the app, or Google Play with the invite when it is not installed.
  function intentUrl(slug, code) {
    checkInvite(slug, code);
    return "intent://invite/" + code + "?h=" + slug + "#Intent;scheme=rackup;package=" + PACKAGE +
      ";S.browser_fallback_url=" + encodeURIComponent(playUrl(slug, code)) + ";end";
  }

  function appStoreUrl(slug) {
    return go.taggedAppStoreUrl(slug, CT_PREFIX);
  }

  // Text only, into elements the page already has, so nothing in a link becomes markup.
  function showHall(doc, hall) {
    var name = doc.getElementById("hall-name");
    name.textContent = hall.name;
    name.setAttribute("href", DIRECTORY + hall.citySlug + "/#" + hall.id);
    doc.getElementById("hall-city").textContent = ", " + hall.city.el;
    doc.getElementById("hall-en").textContent = hall.name + ", " + hall.city.en;
    doc.getElementById("hall").hidden = false;
  }

  // Android opens the invite at once, with a button in case Chrome wants a tap. An iPhone needs the
  // code after an install, so nothing moves there; a computer gets the code and both stores.
  function wire(doc, nav, loc, halls) {
    var invite = inviteFrom(loc.search, halls);
    if (invite === null) {
      doc.getElementById("bad-link").hidden = false;
      return;
    }
    showHall(doc, invite.hall);
    doc.getElementById("app-store").setAttribute("href", appStoreUrl(invite.slug));
    doc.getElementById("google-play").setAttribute("href", playUrl(invite.slug, invite.code));
    var platform = go.platformOf(nav.userAgent, nav.maxTouchPoints);
    if (platform === "android") {
      var intent = intentUrl(invite.slug, invite.code);
      doc.getElementById("open-app").setAttribute("href", intent);
      doc.getElementById("android").hidden = false;
      doc.getElementById("app-store").hidden = true;
      loc.replace(intent);
      return;
    }
    doc.getElementById("code").textContent = codeText(invite.code);
    doc.getElementById("code-box").hidden = false;
    if (platform === "ios") {
      doc.getElementById("open-ios").setAttribute("href", appUrl(invite.slug, invite.code));
      doc.getElementById("ios-open").hidden = false;
      doc.getElementById("google-play").hidden = true;
    }
  }

  var api = {
    isValidCode: isValidCode,
    inviteFrom: inviteFrom,
    codeText: codeText,
    playUrl: playUrl,
    appUrl: appUrl,
    intentUrl: intentUrl,
    appStoreUrl: appStoreUrl,
    wire: wire
  };
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else if (typeof document !== "undefined" && go) {
    wire(document, navigator, location, root.RACKUP_HALLS);
  }
})(this);
