(function () {
  "use strict";
  var supported = ["pl", "en", "de", "fr", "uk", "ru"];
  document.addEventListener("change", function (event) {
    var select = event.target;
    if (!select.matches || !select.matches(".language-select")) return;
    var option = select.options[select.selectedIndex];
    if (!option || supported.indexOf(option.lang) === -1) return;
    var parameters = new URLSearchParams(location.search);
    parameters.delete("lang");
    try { localStorage.setItem("octavam-lang", option.lang); }
    catch (_) { parameters.set("lang", option.lang); }
    var search = parameters.toString();
    var destination = option.value + (search ? "?" + search : "") + location.hash;
    if (location.pathname + location.search + location.hash !== destination) {
      location.assign(destination);
    }
  });

  var path = location.pathname;
  if (!/^\/(?:index\.html|privacy\.html)?$/.test(path)) return;
  var selected = new URLSearchParams(location.search).get("lang");
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
