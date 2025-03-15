# Modul untuk memproses teks input pengguna sebelum dikirim ke sistem
import re
import json
import requests
from datetime import datetime
from logger_config import logger
from config import gemini_model
from config import DEEPSEEK_API_KEY, GPT_API_KEY


def process_prompt_gemini(bmkg_data, user_input):
    current_time = datetime.now()
    current_hour = current_time.hour
    current_minute = current_time.minute
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
    Setiap di akhir jawaban tambahkan kata untuk mengakhiri pesan dan terima kasih telah bertanya, lalu sebutkan silahkan bertanya terkait cuaca daerah Jawa Timur kembali! (pisahlah paragrafnya)     
    """
    logger.info("Mengirim prompt ke model AI.")
    # response = model.generate_content(prompt)
    response = gemini_model.generate_content(prompt)
    text = response.candidates[0].content.parts[0].text.strip()

    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

    return text

def process_prompt_deepseek(bmkg_data, user_message):
    # Konfigurasi API
    OPENROUTER_API_KEY = DEEPSEEK_API_KEY  # Ganti dengan API Key Anda
   

    # Prompt untuk DeepSeek
    prompt = f"""
    Data cuaca dari BMKG:
    {bmkg_data}

    Pertanyaan pengguna:
    {user_message}

    Jawablah pertanyaan pengguna dengan jelas, singkat, dan berikan saran yang sesuai.
    """
    
    try:
        # Kirim permintaan ke API DeepSeek via OpenRouter
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "deepseek/deepseek-r1:free",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
            })
        )
        
        # Pastikan permintaan berhasil
        response.raise_for_status()
        
        # Parsing respons JSON
        data = response.json()
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "Tidak ada respons.")
        return answer

    except requests.exceptions.RequestException as e:
        logger.error(f"Gagal menghubungi OpenRouter API (DeepSeek): {e}")
        return f"Error: {str(e)}"
    except KeyError as e:
        logger.error(f"Kesalahan parsing respons OpenRouter API (DeepSeek): {e}")
        return "Kesalahan dalam memproses respons dari OpenRouter API."

def process_prompt_gpt(bmkg_data, user_input):
    url = "https://chatgpt-42.p.rapidapi.com/gpt4"
    prompt = f"""
    Data cuaca dari BMKG:
    {bmkg_data}

    Pertanyaan pengguna:
    {user_input}

    Jawablah pertanyaan pengguna dengan jelas, singkat, dan berikan saran yang sesuai.
    """
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "web_access": False
    }
    headers = {
        "x-rapidapi-key": GPT_API_KEY,
        "x-rapidapi-host": "chatgpt-42.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Mengirim permintaan ke GPT API dengan prompt: {prompt}")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Memicu exception jika ada kesalahan HTTP
        data = response.json()

        # Pastikan respons memiliki format yang diharapkan
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "Tidak ada respons.")
        logger.info(f"Respons dari GPT API: {answer}")
        return answer

    except requests.exceptions.RequestException as e:
        logger.error(f"Gagal menghubungi GPT API: {e}")
        return f"Error: {str(e)}"
    except KeyError as e:
        logger.error(f"Kesalahan parsing respons GPT API: {e}")
        return "Kesalahan dalam memproses respons dari GPT API."