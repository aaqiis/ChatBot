document.getElementById("closeChat").addEventListener("click", function() {
    if (document.referrer) {
        window.history.back(); 
    } else {
        window.location.href = "hal1.html"; 
    }
});

function updateGreeting() {
    const jamElement = document.getElementById("greeting");
    const greeting = getGreeting();
    const emoji = getEmoji(greeting);
    jamElement.textContent = `${greeting} ${emoji}`;
    const greetingMessage = document.getElementById("greetingMessage");
    greetingMessage.innerHTML = `Halo ${greeting} ${emoji} Sobat BMKG Juanda! 🤗 Apa yang anda ingin ketahui dari BMKG/Fenomena Alam?`;
}

function getGreeting() {
    const hour = new Date().getHours();
    if (hour < 10) return "Selamat Pagi";
    if (hour < 14) return "Selamat Siang";
    if (hour < 18) return "Selamat Sore";
    return "Selamat Malam";
}

function getEmoji(greeting) {
    if (greeting === "Selamat Pagi") return "🌞";
    if (greeting === "Selamat Siang") return "☀️";
    if (greeting === "Selamat Sore") return "☀️";
    return "🌙";
}

// Update greeting setiap 1 menit
setInterval(updateGreeting, 60000);
updateGreeting();

document.getElementById("send-btn").addEventListener("click", sendMessage);
document.getElementById("chat-input").addEventListener("keypress", function(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const inputField = document.getElementById("chat-input");
    const chatMessages = document.getElementById("chatMessages");
    const userInput = inputField.value.trim();
    if (!userInput) return;

    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // Tambahkan pesan pengguna dengan timestamp di dalam bubble
    chatMessages.innerHTML += `
        <div class="message user-message">
            <span class="user-text">${userInput}</span>
            <span class="timestamp">${currentTime}</span>
        </div>
    `;

    inputField.value = "";

    // Tambahkan pesan bot "Harap tunggu..." dengan timestamp di dalam bubble
    chatMessages.innerHTML += `
        <div class="message bot-message">
            <span class="bot-text">Harap tunggu...</span>
            <span class="timestamp">${currentTime}</span>
        </div>
    `;

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    scrollToBottom(); // Auto-scroll setelah menambahkan pesan baru

    const modelSelect = document.getElementById("model-select");

    try {
        const selectedModel = modelSelect.value;
        const formData = new FormData();
        formData.append("user_input", userInput);
        formData.append("model", selectedModel);

        const response = await fetch(`http://127.0.0.1:5000/get_umum`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        let botResponse = data.response || "Maaf, terjadi kesalahan.";

        const waitingMessage = chatMessages.querySelector('.bot-message:last-child');
        if (waitingMessage) waitingMessage.remove();

        const currentTime3 = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // Tambahkan pesan bot yang sudah dijawab dengan timestamp di dalam bubble
        chatMessages.innerHTML += `
            <div class="message bot-message">
                <span class="bot-text">${botResponse}</span>
                <span class="timestamp">${currentTime3}</span>
            </div>
        `;

        scrollToBottom();

    } catch (error) {
        console.error("Error:", error);
        const currentTime4 = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        chatMessages.innerHTML += `
            <div class="message bot-message">
                <span class="bot-text">Terjadi kesalahan saat mengambil data.</span>
                <span class="timestamp">${currentTime4}</span>
            </div>
        `;

        scrollToBottom();
    }
}
