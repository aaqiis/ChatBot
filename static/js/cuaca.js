document.addEventListener("DOMContentLoaded", () => {
    // Fungsi menentukan greeting berdasarkan waktu
    function getGreeting() {
        const hour = new Date().getHours();
        if (hour < 10) return "Selamat Pagi";
        if (hour < 14) return "Selamat Siang";
        if (hour < 18) return "Selamat Sore";
        return "Selamat Malam";
    }

    function getEmoji(greeting) {
        if (greeting === "Selamat Pagi") return "🌅";
        if (greeting === "Selamat Siang") return "☀️";
        if (greeting === "Selamat Sore") return "🌇";
        return "🌙";
    }

    // Menampilkan greeting otomatis
    const greetingTextElement = document.getElementById("greetingText");
    if (greetingTextElement) {
        const greeting = getGreeting();
        const emoji = getEmoji(greeting);
        greetingTextElement.textContent = `${greeting} ${emoji}`;
    }

    // Tombol untuk menutup chat
    document.getElementById("closeChat").addEventListener("click", function () {
        if (document.referrer) {
            window.history.back();
        } else {
            window.location.href = "hal1.html";
        }
    });

    // Event listener untuk tombol kirim
    document.getElementById("send-btn").addEventListener("click", function (event) {
        event.preventDefault();
        sendMessage();
    });

    // Memproses enter di textarea agar mengirim pesan
    const chatInput = document.getElementById("chat-input");
    chatInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            document.getElementById("send-btn").click();
        }
    });

    // Fungsi mengirim pesan ke server
    async function sendMessage() {
        const userInput = chatInput.value.trim();
        const selectedModel = document.getElementById("modelSelector").value;
        if (!userInput) return;

        const chatMessages = document.getElementById("chatMessages");

        // Menampilkan pesan pengguna
        const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const userMessage = document.createElement("div");
        userMessage.className = "message user-message";
        userMessage.innerHTML = `${userInput} <span style="float: right; font-size: 0.8em; color: gray; margin-left: 8px;">${currentTime}</span>`;
        chatMessages.appendChild(userMessage);

        chatInput.value = "";

        // Menampilkan loading message
        const loadingMessage = document.createElement("div");
        loadingMessage.className = "message bot-message";
        loadingMessage.textContent = "Harap Tunggu...";
        loadingMessage.style.color = "gray";
        chatMessages.appendChild(loadingMessage);

        try {
            const response = await fetch('/get_cuaca', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body:`user_input=${encodeURIComponent(userInput)}&model=${encodeURIComponent(selectedModel)}`,
        });
            const data = await response.json();

            chatMessages.removeChild(loadingMessage);

            const botMessage = document.createElement("div");
            botMessage.className = "message bot-message";

            if (response.ok && data.response) {
                const botTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                botMessage.innerHTML = `${data.response} <span style="float: right; font-size: 0.8em; color: gray; margin-left: 10px;">${botTime}</span>`;
            } else {
                botMessage.textContent = "Tidak ada data cuaca yang tersedia untuk lokasi ini. Silahkan berikan keterangan lokasi lengkap (Desa/Kecamatan/Kabupaten/Kota).";
            }

            chatMessages.appendChild(botMessage);
        } catch (error) {
            chatMessages.removeChild(loadingMessage);
            const errorMessage = document.createElement("div");
            errorMessage.className = "message bot-message";
            errorMessage.textContent = `Error: ${error.message}`;
            chatMessages.appendChild(errorMessage);
        }

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
