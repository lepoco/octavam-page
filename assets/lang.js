(function () {
  "use strict";
  var supported = ["pl", "en", "de", "fr", "uk", "ru"];
  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest("a.language-link");
    if (!link || supported.indexOf(link.hreflang) === -1) return;
    var parameters = new URLSearchParams(location.search);
    parameters.set("lang", link.hreflang);
    var destination = new URL(link.href);
    destination.search = parameters.toString();
    destination.hash = location.hash;
    link.href = destination.href;
    try { localStorage.setItem("octavam-lang", link.hreflang); } catch (_) {}
  });

  var selected = new URLSearchParams(location.search).get("lang");
  if (supported.indexOf(selected) !== -1) {
    try { localStorage.setItem("octavam-lang", selected); } catch (_) {}
  }
  var path = location.pathname;
  if (!/^\/(?:index\.html|privacy\.html)?$/.test(path)) return;
  if (supported.indexOf(selected) === -1) {
    try { selected = localStorage.getItem("octavam-lang"); } catch (_) {}
  }
  if (supported.indexOf(selected) === -1) {
    selected = "pl";
    var preferences = navigator.languages || [navigator.language || "pl"];
    for (var i = 0; i < preferences.length; i++) {
      var language = preferences[i].toLowerCase().split(/[-_]/)[0];
      if (supported.indexOf(language) !== -1) { selected = language; break; }
    }
  }
  if (selected !== "pl") {
    var page = path === "/privacy.html" ? "privacy.html" : "";
    location.replace("/" + selected + "/" + page + location.search + location.hash);
  }
})();
