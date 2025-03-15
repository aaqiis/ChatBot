# Modul yang menangani pertanyaan user menggunakan AI 
import os
import requests
from logger_config import logger
from config import GEMINI_API_KEY
from config import DEEPSEEK_API_KEY

# Endpoint API Gemini
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
DEEPSEEK_API_URL = f"https://openrouter.ai/api/v1/chat/completions"

# Headers
HEADERS = {
    "Content-Type": "application/json"
}

# Fungsi untuk mengirim pesan ke API Gemini
def send_message_to_gemini(message):
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": message}]
            }
        ]
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        response_json = response.json()

        if "candidates" in response_json and response_json["candidates"]:
            answer = response_json["candidates"][0]["content"]["parts"][0]["text"].strip()
            return answer

        return "Maaf, tidak ada jawaban yang tersedia dari AI."

    except requests.exceptions.RequestException as e:
        logger.error(f"Kesalahan saat mengakses API Gemini: {str(e)}")
        return "Gagal memproses permintaan."
    
def deepseek_chat(message): 
    """Fungsi untuk mengirim permintaan ke API DeepSeek"""


    headers = {
    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    "Content-Type": "application/json",
}

    data = {
        "model": "deepseek/deepseek-r1",
        "messages": [
            {"role": "user", "content": message}]
    }
    try: 
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        response.raise_for_status()  # Pastikan request tidak error

        response_data = response.json()

        # Cek apakah responsenya valid
        if "choices" in response_data and response_data["choices"]:
            return response_data["choices"][0]["message"]["content"]

        return "Maaf, tidak ada jawaban yang tersedia dari DeepSeek R1."

    except requests.exceptions.RequestException as e:
        logger.error(f"Kesalahan saat mengakses API DeepSeek R1: {str(e)}")
        return "Gagal memproses permintaan ke DeepSeek R1."