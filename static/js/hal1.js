document.addEventListener("DOMContentLoaded", () => { 
    const chatButton = document.querySelector(".chatbot-button");
    const chatBox = document.getElementById("chatBox");
    const closeBtn = document.getElementById("closeBtn");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const cards = document.querySelectorAll(".card");
    const links = document.querySelectorAll(".card a");

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

    function createBubbles(event) {
        const card = event.currentTarget;
        for (let i = 0; i < 5; i++) {
            const bubble = document.createElement("div");
            bubble.classList.add("bubble");

            const size = Math.random() * 10 + 5;
            const x = Math.random() * card.clientWidth;
            const y = Math.random() * card.clientHeight;

            bubble.style.width = bubble.style.height = `${size}px`;
            bubble.style.left = `${x}px`;
            bubble.style.top = `${y}px`;

            card.appendChild(bubble);

            bubble.addEventListener("animationend", () => {
                bubble.remove();
            });
        }
    }

    cards.forEach(card => {
        card.addEventListener("mouseenter", createBubbles);
    });

    function createWaveEffect(event) {
        const button = event.currentTarget;
        const wave = document.createElement("span");
        wave.classList.add("wave");

        const rect = button.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        wave.style.left = `${x}px`;
        wave.style.top = `${y}px`;

        button.appendChild(wave);

        setTimeout(() => {
            wave.remove();
        }, 500);
    }

    links.forEach(link => {
        link.addEventListener("click", createWaveEffect);
    });
});
