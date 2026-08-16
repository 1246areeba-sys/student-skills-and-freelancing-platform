/* SkillBridge — auth.js
   Password visibility toggle + confirm-password validation. */
(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        // Password show/hide
        document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                var input = document.getElementById(btn.getAttribute("data-toggle-password"));
                if (input) {
                    input.type = input.type === "password" ? "text" : "password";
                }
            });
        });

        // Confirm password match
        var form = document.getElementById("registerForm");
        if (form) {
            form.addEventListener("submit", function (e) {
                var pw = form.querySelector("#password");
                var cpw = form.querySelector("#confirm_password");
                if (pw && cpw && pw.value !== cpw.value) {
                    e.preventDefault();
                    alert("Passwords do not match.");
                }
            });
        }
    });
})();
