(function () {
  "use strict";
  var preview = document.getElementById("mode-preview");
  if (!preview) return;
  document.documentElement.classList.add("js");
  var options = Array.from(document.querySelectorAll(".mode-option"));
  var description = document.getElementById("mode-description");
  var caption = document.getElementById("preview-caption");
  options.forEach(function (option) {
    option.addEventListener("click", function () {
      options.forEach(function (item) { item.setAttribute("aria-pressed", String(item === option)); });
      var mode = option.dataset.mode;
      preview.dataset.mode = mode;
      document.getElementById("preview-score").hidden = mode === "blocks";
      document.getElementById("preview-blocks").hidden = mode === "notation";
      description.textContent = option.dataset.description;
      caption.textContent = option.dataset.caption;
    });
  });
  var key = document.getElementById("follow-key");
  var status = document.getElementById("follow-status");
  var restart = document.getElementById("restart-demo");
  var notes = Array.from(document.querySelectorAll(".follow-track span"));
  var step = 0;
  var pitches = ["C", "D", "E", "F", "G"];
  function update() {
    var finished = step === pitches.length;
    notes.forEach(function (note, index) {
      note.classList.toggle("is-current", index === step);
      note.classList.toggle("is-done", index < step);
    });
    status.textContent = finished ? status.dataset.done : status.dataset.waiting.replace("{note}", pitches[step]);
    key.textContent = finished ? key.dataset.done : key.dataset.press.replace("{note}", pitches[step]);
    key.disabled = finished;
    restart.classList.toggle("is-visible", finished);
    if (finished) restart.focus({ preventScroll: true });
  }
  key.addEventListener("click", function () { if (step < pitches.length) { step++; update(); } });
  restart.addEventListener("click", function () { step = 0; update(); key.focus({ preventScroll: true }); });
  update();
})();
