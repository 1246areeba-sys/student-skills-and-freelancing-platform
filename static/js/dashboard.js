/* SkillBridge — dashboard.js
   Sidebar navigation active state + mobile sidebar handling. */
(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        // Close sidebar when clicking outside on mobile
        document.addEventListener("click", function (e) {
            var sidebar = document.getElementById("sidebar");
            var toggle = document.getElementById("sidebarToggle");
            if (!sidebar || !toggle) return;
            if (window.innerWidth <= 768 &&
                sidebar.classList.contains("open") &&
                !sidebar.contains(e.target) &&
                !toggle.contains(e.target)) {
                sidebar.classList.remove("open");
            }
        });
    });
})();
