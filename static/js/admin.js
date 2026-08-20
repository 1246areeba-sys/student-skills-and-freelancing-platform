/* SkillBridge — admin.js
   Admin sidebar toggle (mobile), backdrop, and close-on-navigate. */
(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        var sidebar = document.querySelector(".admin-sidebar");
        var toggle = document.getElementById("adminSidebarToggle");
        var backdrop = document.getElementById("adminSidebarBackdrop");

        function openSidebar() {
            if (sidebar) sidebar.classList.add("open");
            if (backdrop) backdrop.classList.add("show");
        }
        function closeSidebar() {
            if (sidebar) sidebar.classList.remove("open");
            if (backdrop) backdrop.classList.remove("show");
        }

        if (toggle) {
            toggle.addEventListener("click", function () {
                if (sidebar && sidebar.classList.contains("open")) closeSidebar();
                else openSidebar();
            });
        }
        if (backdrop) {
            backdrop.addEventListener("click", closeSidebar);
        }

        // Close the off-canvas sidebar after tapping a nav link (mobile)
        if (sidebar) {
            sidebar.querySelectorAll(".admin-link").forEach(function (link) {
                link.addEventListener("click", closeSidebar);
            });
        }

        // Close on Escape
        document.addEventListener("keydown", function (e) {
            if (e.key === "Escape") closeSidebar();
        });
    });
})();
