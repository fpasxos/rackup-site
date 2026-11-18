// Share page logic for m/index.html. The pure functions are exported so
// tools/match_page.test.js can run them under node; the DOM part runs only in a browser.
(function () {
  "use strict";

  var PACKAGE = "com.rackup.app";
  var PLAY_BASE = "https://play.google.com/store/apps/details?id=com.rackup.app&referrer=";
  var SHARE_TAGS = "utm_source=share&utm_medium=match_link";
  // The page's own Play link, for a bad link: no game to carry.
  var PLAY_URL = PLAY_BASE + encodeURIComponent(SHARE_TAGS);
  // The id lands in an href, so only characters that cannot end or escape it pass; 64 at most, as
  // the app's incomingId takes, and never a name Firestore reserves (__x__).
  var MATCH_ID = /^[A-Za-z0-9_-]{1,64}$/;

  // From app 2.4.8 the link also carries g, r, t and v (MatchLinkDetails in the app repo).
  // The page prints only its own words for them, and a hall only if the directory lists it.
  var GAMES = {
    EIGHT_BALL: { label: "8-Ball", carom: false },
    NINE_BALL: { label: "9-Ball", carom: false },
    TEN_BALL: { label: "10-Ball", carom: false },
    THREE_CUSHION: { label: "3-Cushion", carom: true },
    ONE_CUSHION: { label: "1-Cushion", carom: true }
  };
  var RACE = /^[1-9][0-9]{0,2}$/;
  var STAMP = /^([0-9]{4})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})$/;
  var WEEKDAYS = {
    el: ["Κυριακή", "Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο"],
    en: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
  };
  var MONTHS = {
    el: ["Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου", "Ιουνίου",
      "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου"],
    en: ["January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"]
  };
  var DIRECTORY = { el: "../mpiliardo/", en: "../en/billiards/" };

  function isValidMatchId(id) {
    return typeof id === "string" && MATCH_ID.test(id) && !(id.slice(0, 2) === "__" && id.slice(-2) === "__");
  }

  // Exactly one id: a repeated key is ambiguous, as on /go/ and /f/.
  function matchIdFrom(search) {
    var ids = new URLSearchParams(search || "").getAll("id");
    return ids.length === 1 && isValidMatchId(ids[0]) ? ids[0] : null;
  }

  function isAndroid(userAgent) {
    return /Android/i.test(userAgent || "");
  }

  function isIos(userAgent) {
    return /iPhone|iPad|iPod/i.test(userAgent || "");
  }

  // A visitor on a phone sees the one store for it; a desktop keeps both.
  function showStoreFor(doc, userAgent) {
    var android = isAndroid(userAgent);
    if (!android && !isIos(userAgent)) return;
    doc.getElementById(android ? "app-store" : "google-play").hidden = true;
    doc.getElementById("stores-note").hidden = true;
    doc.getElementById(android ? "note-android" : "note-ios").hidden = false;
  }

  // The game's id rides in the install tags: app 2.4.9 reads them once after a fresh install and opens it.
  function playUrl(id) {
    if (!isValidMatchId(id)) throw new Error("invalid match id");
    return PLAY_BASE + encodeURIComponent(SHARE_TAGS + "&rackup_match=" + id);
  }

  // Chrome opens rackup://match/<id> in the app, or the fallback when it is not installed.
  function intentUrl(id) {
    return "intent://match/" + id + "#Intent;scheme=rackup;package=" + PACKAGE +
      ";S.browser_fallback_url=" + encodeURIComponent(playUrl(id)) + ";end";
  }

  // An Android app's own browser may answer an app link with an error page: buttons only there (go/go.js).
  function isWebView(userAgent) {
    return /; wv\)/.test(userAgent || "");
  }

  // A real day and time at the hall, or null: 20261131 and 25:00 are not.
  function startFrom(stamp) {
    var m = STAMP.exec(stamp || "");
    if (!m) return null;
    var year = +m[1], month = +m[2], day = +m[3], hour = +m[4], minute = +m[5];
    var date = new Date(Date.UTC(year, month - 1, day));
    if (year < 2000 || date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day || hour > 23 || minute > 59) return null;
    return { year: year, month: month, day: day, hour: hour, minute: minute, weekday: date.getUTCDay() };
  }

  // The game, its start and its hall as the link carries them, or null unless all three are sound.
  function detailsFrom(search, halls) {
    var params = new URLSearchParams(search || "");
    var code = params.get("g");
    var game = Object.prototype.hasOwnProperty.call(GAMES, code) ? GAMES[code] : null;
    var start = startFrom(params.get("t"));
    var id = params.get("v");
    var hall = halls && isValidMatchId(id) && Object.prototype.hasOwnProperty.call(halls, id) ? halls[id] : null;
    if (!game || !start || !hall) return null;
    var race = params.get("r");
    return {
      game: game,
      race: RACE.test(race || "") ? +race : null,
      start: start,
      hall: { id: id, name: hall[0], city: { el: hall[1], en: hall[2] }, slug: hall[3] }
    };
  }

  // "9-Ball · Race to 5", "3-Cushion · To 30 points": the app's own words in each language.
  function gameText(details, lang) {
    if (details.race === null) return details.game.label;
    var format = details.game.carom
      ? (lang === "el" ? "Στους " + details.race + " πόντους" : "To " + details.race + " points")
      : (lang === "el" ? "Race στα " + details.race : "Race to " + details.race);
    return details.game.label + " · " + format;
  }

  function pad(n) {
    return (n < 10 ? "0" : "") + n;
  }

  // «Σάββατο 15 Νοεμβρίου, 21:00», "Saturday 15 November, 21:00": the time at the hall.
  function whenText(start, lang) {
    return WEEKDAYS[lang][start.weekday] + " " + start.day + " " + MONTHS[lang][start.month - 1] + ", " +
      pad(start.hour) + ":" + pad(start.minute);
  }

  function hallLink(hall, lang) {
    return DIRECTORY[lang] + hall.slug + "/#" + hall.id;
  }

  // Text only, into elements the page already has, so nothing in a link becomes markup.
  function showDetails(doc, details) {
    doc.getElementById("game-what").textContent = gameText(details, "el");
    doc.getElementById("game-what-en").textContent = gameText(details, "en");
    doc.getElementById("game-when").textContent = whenText(details.start, "el");
    doc.getElementById("game-when-en").textContent = whenText(details.start, "en");
    var hall = doc.getElementById("game-hall");
    hall.textContent = details.hall.name;
    hall.setAttribute("href", hallLink(details.hall, "el"));
    doc.getElementById("game-city").textContent = ", " + details.hall.city.el;
    doc.getElementById("game-where-en").textContent = details.hall.name + ", " + details.hall.city.en;
    doc.getElementById("game").hidden = false;
    doc.getElementById("game-note").hidden = false;
  }

  // Android's Chrome jumps to the app at once and keeps the button in case it wants a tap; an app's
  // own browser gets only the buttons. Nothing moves on an iPhone or a computer.
  function wire(doc, userAgent, search, halls, jump) {
    showStoreFor(doc, userAgent);
    var id = matchIdFrom(search);
    if (id === null) {
      doc.getElementById("bad-link").hidden = false;
      return;
    }
    var details = detailsFrom(search, halls);
    if (details !== null) showDetails(doc, details);
    doc.getElementById("google-play").setAttribute("href", playUrl(id));
    if (isAndroid(userAgent)) {
      var intent = intentUrl(id);
      doc.getElementById("open-app").setAttribute("href", intent);
      doc.getElementById("android").hidden = false;
      if (jump && !isWebView(userAgent)) jump(intent);
    }
  }

  var api = {
    PLAY_URL: PLAY_URL,
    GAMES: GAMES,
    isValidMatchId: isValidMatchId,
    matchIdFrom: matchIdFrom,
    isAndroid: isAndroid,
    isIos: isIos,
    isWebView: isWebView,
    playUrl: playUrl,
    intentUrl: intentUrl,
    startFrom: startFrom,
    detailsFrom: detailsFrom,
    gameText: gameText,
    whenText: whenText,
    hallLink: hallLink,
    wire: wire
  };
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  } else if (typeof document !== "undefined") {
    wire(document, navigator.userAgent, location.search, window.RACKUP_HALLS || {}, function (url) {
      location.replace(url);
    });
  }
})();
