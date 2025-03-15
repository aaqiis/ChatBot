# # gemini_api.py
import requests
from config import GEMINI_API_KEY, GEMINI_API_HOST, GEMINI_API_URL

def send_message_to_gemini(message):
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": message}]
            }
        ]
    }
    headers = {
        "x-rapidapi-key": GEMINI_API_KEY,
        "x-rapidapi-host": GEMINI_API_HOST,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
        response.raise_for_status()  
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Gagal memproses permintaan: {e}"}
