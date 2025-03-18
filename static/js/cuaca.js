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
        const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // Tambahkan pesan user
        const userMessage = document.createElement("div");
        userMessage.className = "message user-message";
        userMessage.innerHTML = `
            <div style="text-align: left;">${userInput}</div>
            <div style="text-align: right; font-size: 0.8em; color: black; margin-top: 4px;">${currentTime}</div>
        `;
        chatMessages.appendChild(userMessage);
        chatInput.value = "";

        // Tambahkan indikator loading
        const loadingMessage = document.createElement("div");
        loadingMessage.className = "message bot-message";
        loadingMessage.textContent = "Harap Tunggu...";
        chatMessages.appendChild(loadingMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll ke bawah
    
        try {
            const response = await fetch('/get_cuaca', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_input: userInput, model: selectedModel })
            });

            const data = await response.json();
            chatMessages.removeChild(loadingMessage);

            const botMessage = document.createElement("div");
            botMessage.className = "message bot-message";

            if (response.ok && data.response) {
                botMessage.innerHTML = `
                    <div style="text-align: left;">${data.response}</div>
                    <div style="text-align: right; font-size: 0.8em; color: black; margin-top: 4px;">${currentTime}</div>
                `;
                chatMessages.appendChild(botMessage);

                // Tambahkan pesan bot baru "Terima kasih telah bertanya..." hanya jika tidak ada error
                const thanksMessage = document.createElement("div");
                thanksMessage.className = "message bot-message";
                thanksMessage.innerHTML = `
                    <div style="text-align: left;">Terima kasih telah mengajukan pertanyaan. Jika Anda ingin bertanya kembali, silakan ajukan pertanyaan lain terkait cuaca di wilayah Jawa Timur. Jika ingin keluar, Anda dapat mengklik tombol di pojok kanan atas.</div>
                    <div style="text-align: right; font-size: 0.8em; color: black; margin-top: 4px;">${currentTime}</div>
                `;
                chatMessages.appendChild(thanksMessage);

            } else {
                let errorMessageText = "Terjadi kesalahan dalam memproses permintaan. Pastikan format pertanyaan Anda benar.";
                if (data.error_type === "invalid_query") {
                    errorMessageText = "Maaf, saya tidak mengerti pertanyaan Anda. Mohon periksa kembali kata-katanya!";
                } else if (data.error_type === "location_not_found") {
                    errorMessageText = "Lokasi yang Anda masukkan tidak ditemukan. Silakan coba dengan nama lokasi yang lebih spesifik.";
                } else if (data.error_type === "server_error") {
                    errorMessageText = "Terjadi kesalahan saat mengambil data cuaca. Silakan coba lagi nanti.";
                }

                botMessage.innerHTML = `
                    <div style="text-align: left;">${errorMessageText}</div>
                    <div style="text-align: right; font-size: 0.8em; color: black; margin-top: 4px;">${currentTime}</div>
                `;
                chatMessages.appendChild(botMessage);
            }

            chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll ke pesan terakhir

        } catch (error) {
            chatMessages.removeChild(loadingMessage);
            const errorMessage = document.createElement("div");
            errorMessage.className = "message bot-message";
            errorMessage.innerHTML = `
                <div style="text-align: left;">Terjadi kesalahan dalam mengambil data. Mohon coba lagi nanti!</div>
                <div style="text-align: right; font-size: 0.8em; color: black; margin-top: 4px;">${currentTime}</div>
            `;
            chatMessages.appendChild(errorMessage);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
});
