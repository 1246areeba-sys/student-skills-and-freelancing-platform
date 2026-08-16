/* SkillBridge — admin.js
   Admin sidebar toggle, table row confirmations, inline select auto-submit. */
(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        // Admin sidebar toggle for mobile
        var adminSidebar = document.querySelector(".admin-sidebar");
        // Reuse topbar hamburger if present
        var hamburger = document.querySelector(".admin-topbar .sidebar-toggle");
        if (hamburger && adminSidebar) {
            hamburger.addEventListener("click", function () { adminSidebar.classList.toggle("open"); });
        }

        // Confirm destructive admin actions
        document.querySelectorAll("form[onsubmit]").forEach(function () { /* handled inline */ });

        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(function (a) {
            a.addEventListener("click", function (e) {
                var id = a.getAttribute("href");
                if (id.length > 1) {
                    var target = document.querySelector(id);
                    if (target) { e.preventDefault(); target.scrollIntoView({ behavior: "smooth" }); }
                }
            });
        });
    });
})();
