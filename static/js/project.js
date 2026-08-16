/* SkillBridge — project.js
   Assessment option selection, workspace milestone interactions, resume live preview. */
(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        // Assessment: single-choice option selection
        document.querySelectorAll(".assessment-option").forEach(function (opt) {
            opt.addEventListener("click", function () {
                var group = opt.getAttribute("data-group");
                document.querySelectorAll('.assessment-option[data-group="' + group + '"]').forEach(function (o) {
                    o.classList.remove("selected");
                });
                opt.classList.add("selected");
                var input = opt.querySelector("input[type='radio']");
                if (input) input.checked = true;
            });
        });

        // Resume builder live preview toggle
        var previewToggle = document.getElementById("previewToggle");
        if (previewToggle) {
            previewToggle.addEventListener("click", function () {
                var preview = document.getElementById("resumePreview");
                if (preview) preview.scrollIntoView({ behavior: "smooth" });
            });
        }

        // Confirm before submitting work / approving
        document.querySelectorAll("form[data-confirm]").forEach(function (f) {
            f.addEventListener("submit", function (e) {
                if (!confirm(f.getAttribute("data-confirm"))) e.preventDefault();
            });
        });
    });
})();
