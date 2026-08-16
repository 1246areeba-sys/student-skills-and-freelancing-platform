/* SkillBridge — main.js
   Global UI behaviors: mobile nav, sidebar toggle, flash auto-dismiss, scroll navbar. */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        // Mobile navigation toggle
        var navToggle = document.getElementById("navToggle");
        var navLinks = document.getElementById("navLinks");
        if (navToggle && navLinks) {
            navToggle.addEventListener("click", function () {
                navLinks.classList.toggle("open");
            });
        }

        // Dashboard sidebar toggle (mobile)
        var sidebarToggle = document.getElementById("sidebarToggle");
        var sidebar = document.getElementById("sidebar");
        var sidebarClose = document.getElementById("sidebarClose");
        function closeSidebar() { if (sidebar) sidebar.classList.remove("open"); }
        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener("click", function () { sidebar.classList.toggle("open"); });
        }
        if (sidebarClose) sidebarClose.addEventListener("click", closeSidebar);

        // Admin sidebar toggle
        var adminToggle = document.querySelector(".admin-sidebar .sidebar-close");
        var adminSidebar = document.querySelector(".admin-sidebar");
        if (adminToggle && adminSidebar) {
            adminToggle.addEventListener("click", function () { adminSidebar.classList.remove("open"); });
        }

        // Auto-dismiss flash messages after 5s
        var alerts = document.querySelectorAll(".alert");
        alerts.forEach(function (el) {
            setTimeout(function () {
                el.style.transition = "opacity 0.4s";
                el.style.opacity = "0";
                setTimeout(function () { el.remove(); }, 400);
            }, 5000);
        });

        // Confirm dialogs for destructive links with data-confirm
        document.querySelectorAll("[data-confirm]").forEach(function (el) {
            el.addEventListener("click", function (e) {
                if (!confirm(el.getAttribute("data-confirm"))) e.preventDefault();
            });
        });

        // Navbar shadow on scroll
        var navbar = document.getElementById("mainNavbar");
        if (navbar) {
            window.addEventListener("scroll", function () {
                if (window.scrollY > 10) navbar.style.boxShadow = "0 4px 20px rgba(0,0,0,0.25)";
                else navbar.style.boxShadow = "0 2px 20px rgba(0,0,0,0.2)";
            });
        }
    });
})();
