(function () {
  "use strict";
  var supported = ["pl", "en", "de", "fr", "uk", "ru"];
  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest("a.lang");
    if (!link) return;
    try { localStorage.setItem("octavam-lang", link.hreflang); } catch (_) {}
  });

  var path = location.pathname;
  if (!/^\/(?:index\.html|privacy\.html)?$/.test(path)) return;
  var selected;
  try { selected = localStorage.getItem("octavam-lang"); } catch (_) {}
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
