// Remembers the user's language choice; redirects the root page to /en/ for non-Polish browsers on first visit.
(function () {
  try {
    var path = location.pathname;
    var isRoot = /^\/(index\.html)?$/.test(path);
    var saved = localStorage.getItem("octavam-lang");
    if (isRoot && !saved && !/^pl/i.test(navigator.language || "pl")) {
      location.replace("/en/" + location.search + location.hash);
    } else if (isRoot && saved === "en") {
      location.replace("/en/" + location.search + location.hash);
    }
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a.lang");
      if (a) localStorage.setItem("octavam-lang", a.getAttribute("hreflang"));
    });
  } catch (_) {}
})();
