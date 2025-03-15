document.getElementById("closeChat").addEventListener("click", function() {
    if (document.referrer) {
        window.history.back(); 
    } else {
        window.location.href = "hal1.html"; 
    }
    });

    function updateJam() {
        const jamElement = document.getElementById("greeting");
        const tanggalSekarang = new Date();
        const jamSekarang = tanggalSekarang.getHours().toString().padStart(2, "0");
        const menitSekarang = tanggalSekarang.getMinutes().toString().padStart(2, "0");
        const greeting = getGreeting();
        const emoji = getEmoji(greeting);
        jamElement.textContent = `${greeting} ${emoji}`;
        const greetingMessage = document.getElementById("greetingMessage");
        greetingMessage.innerHTML = `Halo ${greeting} ${emoji} Sobat BMKG Juanda! 🤗 Apa yang anda ingin ketahui dari BMKG/Fenomena Alam?`;
        // Tambahkan event listener lagi
        document.getElementById("send-btn").addEventListener("click", sendMessage);
        document.getElementById("chat-input").addEventListener("keypress", function(event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });
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

    setInterval(updateJam, 1000);
    updateJam();

    document.getElementById("greeting").textContent = getGreeting();
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
chatMessages.innerHTML += `
    <div class="message user-message">
        ${userInput} <span style="font-size: 0.8em; color: gray; margin-left: 8px; margin-top: 10px;">${currentTime}</span>
    </div>
`;

inputField.value = "";

const currentTime2 = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
chatMessages.innerHTML += `
    <div class="message bot-message" style="color: #808080; font-size: 12px;">
        Harap tunggu... <span style="font-size: 0.8em; color: gray; margin-left: 8px; margin-top: 10px;">${currentTime2}</span>
    </div>
`;


const modelSelect = document.getElementById("model-select"); // Ambil elemen dropdown model

try {
    const selectedModel = modelSelect.value; // Pastikan ini dideklarasikan
    const formData = new FormData();
    formData.append("user_input", userInput);
    formData.append("model", selectedModel); // Kirim model ke backend

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
    waitingMessage.remove();

    const currentTime3 = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
     // Tentukan label model yang digunakan
     let modelLabel = "[🤖 AI]";
     if (selectedModel === "gemini") {
         modelLabel = "[Gemini 🤖]";
     } else if (selectedModel === "deepseek") {
         modelLabel = "[DeepSeek 🔍]";
     }
 
    
    chatMessages.innerHTML += `
        <div class="message bot-message">
            ${botResponse} ${modelLabel} 
            <span style="font-size: 0.8em; color: gray; float: right;">${currentTime3}</span>
        </div>
    `;

    chatMessages.scrollTop = chatMessages.scrollHeight;

} catch (error) {
    console.error("Error:", error);
    const currentTime4 = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    chatMessages.innerHTML += `
        <div class="message bot-message">
            Terjadi kesalahan saat mengambil data. <span style="font-size: 0.8em; color: gray; float: right;">${currentTime4}</span>
        </div>
    `;
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
}