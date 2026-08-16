/* SkillBridge — chat.js
   Auto-scroll chat to bottom, Enter-to-send, attachment preview. */
(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        var thread = document.getElementById("chatThread");
        if (thread) {
            thread.scrollTop = thread.scrollHeight;
        }

        var form = document.querySelector(".chat-form");
        if (form) {
            var input = form.querySelector("input[name='message']");
            form.addEventListener("submit", function () {
                // Allow normal submit; clear input after a tick
                if (input) setTimeout(function () { input.value = ""; }, 50);
            });
            // Enter to send (Shift+Enter for newline not needed here)
            if (input) {
                input.addEventListener("keydown", function (e) {
                    if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        form.requestSubmit ? form.requestSubmit() : form.submit();
                    }
                });
            }
        }
    });
})();
