document.addEventListener("DOMContentLoaded", () => {
    const chatButton = document.querySelector(".chatbot-button");
    const chatBox = document.getElementById("chatBox");
    const closeBtn = document.getElementById("closeBtn");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");

    function toggleChat() {
        if (chatBox) {
            chatBox.style.display = (chatBox.style.display === "none" || chatBox.style.display === "") ? "flex" : "none";
        }
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", toggleChat);
    }

    if (chatButton) {
        chatButton.addEventListener("click", toggleChat);
    }

    if (chatInput && sendBtn) {
        chatInput.addEventListener("keydown", function(event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendBtn.click();
            }
        });

        sendBtn.addEventListener("click", function(event) {
            event.preventDefault();
            sendMessage();
        });
    }

    function updateClock() {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, "0");
        const minutes = now.getMinutes().toString().padStart(2, "0");
        const timeString = `${hours}:${minutes}`;
        
        const dateOptions = { weekday: "long", day: "numeric", month: "long", year: "numeric" };
        const dateString = now.toLocaleDateString("id-ID", dateOptions);

        const clockElement = document.getElementById("clock");
        const dateElement = document.getElementById("date");

        if (clockElement && dateElement) {
            clockElement.textContent = timeString;
            dateElement.textContent = dateString;
        }
    }

    setInterval(updateClock, 1000);
    updateClock();
});
