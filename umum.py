# Modul utama informasi umum
from utils.umum_ai import send_message_to_gemini
from utils.text_classifier import is_weather_related
from logger_config import logger
from utils.umum_ai import deepseek_chat

def get_response(user_message, model="gemini"):
    try:
        # Periksa apakah pertanyaan terkait cuaca atau fenomena alam
        if not is_weather_related(user_message):
            return "Maaf, saya hanya dapat memberikan informasi tentang cuaca dan fenomena alam."

        # Buat prompt untuk API Gemini
        prompt = f"""
        Pengguna meminta informasi tentang cuaca atau fenomena alam:
        {user_message}

        HANYA memberikan informasi terkait cuaca dan fenomena alam dan hal apapun berkaitan dengan BMKG.
        Jika pengguna bertanya di luar topik ini, jangan memberikan jawaban apapun, cukup balas dengan:
        "Maaf, saya hanya dapat memberikan informasi tentang cuaca dan fenomena alam, silahkan beri pertanyaan lain😊."
        Jika pengguna bertanya mengenai perkiraan cuaca di Jawa Timur, balas dengan:
        "Silahkan bertanya pada bagian informasi prakiraan cuaca🤗."
        {user_message}
        Ingat! Jika pertanyaan ini tidak berhubungan dengan cuaca dan fenomena alam, JANGAN menjawab atau memberikan informasi lain.
        Berikan jawaban yang relevan, jelas, singkat dan informatif sesuai dengan permintaan pengguna.
        dan jangan ada bold disemua text.
        """
        
        print(f"[TERMINAL] Prompt sebelum dikirim ke AI:\n{prompt}")  # Menampilkan prompt di terminal

 # Kirim ke model yang dipilih
        if model == "gemini":
            logger.info(f"Menggunakan model Gemini untuk: {user_message}")
            response = send_message_to_gemini(prompt)

        elif model == "deepseek":
            logger.info(f"Menggunakan model DeepSeek untuk: {user_message}")
            response = deepseek_chat(prompt)
        else:
            response = "Model AI tidak dikenali."
        return response

    except Exception as e:
        logger.error(f"Terjadi kesalahan: {str(e)}")
        return "Terjadi kesalahan pada server."