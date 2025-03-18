# Modul untuk memproses teks input pengguna sebelum dikirim ke sistem
import re
import json
import requests
from datetime import datetime
from logger_config import logger
from config import gemini_model
from config import DEEPSEEK_API_KEY, GPT_API_KEY


def process_prompt_gemini(bmkg_data, user_input):
    try:
        current_time = datetime.now()
        current_hour = current_time.hour
        formatted_time = current_time.strftime("%H:%M")
    
        # Tentukan waktu berdasarkan interval
        if 5 <= current_hour < 12:
            time_of_day = "Pagi"
        elif 12 <= current_hour < 15:
            time_of_day = "Siang"
        elif 15 <= current_hour < 18:
            time_of_day = "Sore"
        elif 19 <= current_hour < 22:
            time_of_day = "Malam"
        else:
            time_of_day = "Dini Hari"
        
            
        prompt = f"""
        {bmkg_data}

        Pertanyaan pengguna:
        {user_input}

        Waktu saat ini adalah {formatted_time} WIB ({time_of_day}).
        Jawablah pertanyaan pengguna dengan jelas, singkat, tanpa huruf bold disemua text. sebutkan lokasi lengkap, serta berikan saran kegiatan atau pengingat sesuai keadaan yang terjadi pada pertanyaan.
        -Pukul 05.00-12.00 menunjukkan Pagi
        -Pukul 12.00-15.00 menunjukkan Siang
        -Pukul 15.00-18.00 menunjukkan Sore
        -Pukul 19.00-22.00 menunjukkan Malam
        -Pukul 01.00-05.00 menunjukkan Dini Hari
        Jika pengguna bertanya lebih dari waktu yang ada dalam data BMKG, jawablah dengan "Mohon maaf data kami hanya menampilkan hingga 3 hari kedepan"
        Jika pengguna bertanya terkait waktu jawablah dengan waktu sesuai permintaannya.
        Jika pertanyaan tidak terkait BMKG atau wilayah tidak ditemukan, balas dengan: "Mohon maaf Sobat, pertanyaan tidak tersedia dalam data kami. Silahkan berikan pertanyaan seputar cuaca di daerah Jawa Timur dan sertakan keterangan lokasi daerah lengkap (Desa/Kecamatan/Kabupaten/Kota)".   
        """
        logger.info("Mengirim prompt ke model AI.")
        # response = model.generate_content(prompt)
        response = gemini_model.generate_content(prompt)
        
        if not response or not hasattr(response, 'candidates') or not response.candidates:
                logger.error("❌ Respons dari Gemini tidak valid atau kosong.")
                return "Mohon maaf, ada kesalahan dalam mendapatkan jawaban dari AI."

        text = response.candidates[0].content.parts[0].text.strip()
        
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
        
        return text

    except Exception as e:
        logger.error(f"❌ ERROR saat memproses prompt Gemini: {e}")
        return "Terjadi kesalahan saat memproses AI."


def process_prompt_deepseek(bmkg_data, user_message):
    try:
        current_time = datetime.now()
        current_hour = current_time.hour
        formatted_time = current_time.strftime("%H:%M")
    
        # Tentukan waktu berdasarkan interval
        if 5 <= current_hour < 12:
            time_of_day = "Pagi"
        elif 12 <= current_hour < 15:
            time_of_day = "Siang"
        elif 15 <= current_hour < 18:
            time_of_day = "Sore"
        elif 19 <= current_hour < 22:
            time_of_day = "Malam"
        else:
            time_of_day = "Dini Hari"
        
        prompt = f"""
        Data cuaca dari BMKG:
        {bmkg_data}

        Pertanyaan pengguna:
        {user_message}

        Waktu saat ini adalah {formatted_time} WIB ({time_of_day}).
        Jawablah pertanyaan pengguna dengan jelas, singkat, tanpa huruf bold disemua text. sebutkan lokasi lengkap, serta berikan saran kegiatan atau pengingat sesuai keadaan yang terjadi pada pertanyaan.
        -Pukul 05.00-10.00 menunjukkan Pagi
        -Pukul 11.00-15.00 menunjukkan Siang
        -Pukul 15.00-18.00 menunjukkan Sore
        -Pukul 19.00-22.00 menunjukkan Malam
        -Pukul 01.00-05.00 menunjukkan Dini Hari
        Jika pengguna bertanya lebih dari  yang ada dalam data BMKG, jawablah dengan "Mohon maaf data kami hanya menampilkan hingga 3 hari kedepan"
        Jika pengguna bertanya terkait waktu jawablah dengan waktu sesuai permintaannya.
        Jika pertanyaan tidak terkait BMKG atau wilayah tidak ditemukan, balas dengan: "Mohon maaf Sobat, pertanyaan tidak tersedia dalam data kami. Silahkan berikan pertanyaan seputar cuaca di daerah Jawa Timur dan sertakan keterangan lokasi daerah lengkap (Desa/Kecamatan/Kabupaten/Kota)".   
        """

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "deepseek/deepseek-r1:free",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
            })
        )

        response.raise_for_status()
        data = response.json()
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "Tidak ada respons.")

        answer = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", answer)

        return answer

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Gagal menghubungi OpenRouter API (DeepSeek): {e}")
        return f"Error: {str(e)}"
    except KeyError as e:
        logger.error(f"❌ Kesalahan parsing respons OpenRouter API (DeepSeek): {e}")
        return "Kesalahan dalam memproses respons dari OpenRouter API."

def process_prompt_gpt(bmkg_data, user_input):
    try:
        url = "https://chatgpt-42.p.rapidapi.com/gpt4"

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
                    Data cuaca dari BMKG:
                    {bmkg_data}

                    Pertanyaan pengguna:
                    {user_input}

                    Jawablah pertanyaan pengguna dengan jelas, singkat, dan berikan saran yang sesuai.
                    """
                }
            ],
            "web_access": False
        }

        headers = {
            "x-rapidapi-key": GPT_API_KEY,  # API Key dari .env
            "x-rapidapi-host": "chatgpt-42.p.rapidapi.com",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  

        data = response.json()
        answer = data.get("message", "Tidak ada respons.")

        logger.info(f"✅ Respons dari GPT API: {answer}")
        return answer

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Gagal menghubungi GPT API: {e}")
        return "Terjadi kesalahan saat menghubungi GPT API."

    except KeyError as e:
        logger.error(f"❌ Kesalahan parsing respons GPT API: {e}")
        return "Kesalahan dalam memproses respons dari GPT API."