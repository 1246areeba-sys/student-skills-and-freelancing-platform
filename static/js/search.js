/* SkillBridge — search.js
   Live filter for marketplace pages + instant search suggestions. */
(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        // Auto-submit filter form on select change
        document.querySelectorAll(".filter-form select").forEach(function (sel) {
            sel.addEventListener("change", function () { sel.closest("form").submit(); });
        });

        // Debounced live search input -> submit form
        var searchInput = document.querySelector(".filter-form input[name='q']");
        if (searchInput) {
            var timer;
            searchInput.addEventListener("input", function () {
                clearTimeout(timer);
                timer = setTimeout(function () {
                    searchInput.closest("form").submit();
                }, 600);
            });
        }

        // Global search on home page
        var globalSearch = document.getElementById("globalSearch");
        if (globalSearch) {
            globalSearch.addEventListener("submit", function (e) {
                var q = globalSearch.querySelector("input").value.trim();
                if (!q) { e.preventDefault(); }
            });
        }
    });
})();
