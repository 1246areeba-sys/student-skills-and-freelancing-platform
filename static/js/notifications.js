/* SkillBridge — notifications.js
   Mark-as-read on click, dismiss individual notifications. */
(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        // Clicking a notification "View" link marks it read via the form already.
        // Auto-hide unread highlight after visiting.
        document.querySelectorAll(".notification-item.unread a[href]").forEach(function (link) {
            link.addEventListener("click", function () {
                var item = link.closest(".notification-item");
                if (item) item.classList.remove("unread");
            });
        });
    });
})();
