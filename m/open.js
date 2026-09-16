// Share page logic for m/index.html. The pure functions are exported so
// tools/match_page.test.js can run them under node; the DOM part runs only in a browser.
(function () {
  "use strict";

  var PACKAGE = "com.rackup.app";
  var PLAY_URL = "https://play.google.com/store/apps/details?id=com.rackup.app" +
    "&referrer=utm_source%3Dshare%26utm_medium%3Dmatch_link";
  // The id lands in an href, so only characters that cannot end or escape it pass.
  var MATCH_ID = /^[A-Za-z0-9_-]{1,128}$/;

  function isValidMatchId(id) {
    return typeof id === "string" && MATCH_ID.test(id);
  }

  function matchIdFrom(search) {
    var id = new URLSearchParams(search || "").get("id");
    return isValidMatchId(id) ? id : null;
  }

  function isAndroid(userAgent) {
    return /Android/i.test(userAgent || "");
  }

  // Chrome opens rackup://match/<id> in the app, or the fallback when it is not installed.
  function intentUrl(id) {
    if (!isValidMatchId(id)) throw new Error("invalid match id");
    return "intent://match/" + id + "#Intent;scheme=rackup;package=" + PACKAGE +
      ";S.browser_fallback_url=" + encodeURIComponent(PLAY_URL) + ";end";
  }

  function wire(doc, userAgent, search) {
    var id = matchIdFrom(search);
    if (id === null) {
      doc.getElementById("bad-link").hidden = false;
    } else if (isAndroid(userAgent)) {
      doc.getElementById("open-app").setAttribute("href", intentUrl(id));
      doc.getElementById("android").hidden = false;
    }
  }

  var api = {
    PLAY_URL: PLAY_URL,
    isValidMatchId: isValidMatchId,
    matchIdFrom: matchIdFrom,
    isAndroid: isAndroid,
    intentUrl: intentUrl,
    wire: wire
  };
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else if (typeof document !== "undefined") {
    wire(document, navigator.userAgent, location.search);
  }
})();
