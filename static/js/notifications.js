/* SkillBridge — notifications.js
   Live polling: keeps the navbar badge in sync and shows a toast when a
   new notification arrives, so users receive notifications without refreshing. */
(function () {
    "use strict";

    var POLL_INTERVAL = 15000; // 15 seconds
    var lastId = 0;

    function iconFor(type) {
        switch (type) {
            case "message": return "fa-comment";
            case "proposal": return "fa-paper-plane";
            case "hire": return "fa-handshake";
            case "payment": return "fa-dollar-sign";
            case "review": return "fa-star";
            case "project": return "fa-briefcase";
            case "assessment": return "fa-clipboard-check";
            default: return "fa-bell";
        }
    }

    function updateBadge(count) {
        var bell = document.querySelector('a[href*="/notifications/"].nav-bell, a.nav-bell[title="Notifications"]');
        if (!bell) return;
        var existing = bell.querySelector(".badge");
        if (count > 0) {
            if (!existing) {
                existing = document.createElement("span");
                existing.className = "badge";
                bell.appendChild(existing);
            }
            existing.textContent = count;
        } else if (existing) {
            existing.remove();
        }
    }

    function showToast(n) {
        var container = document.getElementById("toast-container");
        if (!container) {
            container = document.createElement("div");
            container.id = "toast-container";
            container.className = "toast-container";
            document.body.appendChild(container);
        }
        var toast = document.createElement("a");
        toast.className = "toast-notification";
        if (n.link) toast.href = n.link;
        toast.innerHTML =
            '<i class="fa-solid ' + iconFor(n.type) + '"></i>' +
            '<div class="toast-body"><strong>' + (n.title || "Notification") + "</strong>" +
            '<span>' + (n.message || "") + "</span></div>";
        container.appendChild(toast);
        // Trigger enter animation
        requestAnimationFrame(function () { toast.classList.add("show"); });
        setTimeout(function () {
            toast.classList.remove("show");
            setTimeout(function () { toast.remove(); }, 400);
        }, 6000);
        toast.addEventListener("click", function () {
            setTimeout(function () { toast.remove(); }, 200);
        });
    }

    function poll() {
        fetch("/notifications/api/latest?since_id=" + lastId, {
            headers: { "X-Requested-With": "XMLHttpRequest" },
            credentials: "same-origin",
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                updateBadge(data.unread || 0);
                (data.new || []).forEach(function (n) {
                    if (n.id > lastId) lastId = n.id;
                    showToast(n);
                });
                if (data.latest && data.latest.length) {
                    var maxId = data.latest[0].id;
                    if (maxId > lastId) lastId = maxId;
                }
            })
            .catch(function () { /* ignore network errors */ });
    }

    document.addEventListener("DOMContentLoaded", function () {
        // Seed lastId from any existing notifications in the DOM (if present)
        var items = document.querySelectorAll(".notification-item");
        items.forEach(function (el) {
            var m = /notification-item-(\d+)/.exec(el.className);
            if (m) lastId = Math.max(lastId, parseInt(m[1], 10));
        });
        // Also read initial badge value if present
        var badge = document.querySelector('a[title="Notifications"] .badge');
        if (badge) updateBadge(parseInt(badge.textContent, 10) || 0);

        poll();
        setInterval(poll, POLL_INTERVAL);
    });
})();
