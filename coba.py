from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import requests
import re
import json
import difflib
import logging
from config import GEMINI_API_KEY, BMKG_API_ENDPOINT
import google.generativeai as genai
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

EXCEL_URL = "https://docs.google.com/spreadsheets/d/1gMFJRqsLbbqYllRwYqFnYLtV4kajYTjj7VcrLz8nR00/export?format=xlsx"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@app.route('/')
def index():
    return render_template('index1.html')

# Fungsi untuk memeriksa apakah pesan adalah sapaan
def is_greeting(user_message):
    greetings = ["halo", "hi", "hai", "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "good morning", "good afternoon", "good evening", "good night"]
    for greeting in greetings:
        if greeting in user_message.lower():
            return True, 'id' if 'selamat' in greeting else 'en'
    return False, None

def get_time_based_greeting(language='id'):
    hour = datetime.now().hour
    
    if 0 <= hour < 5:
        return "Selamat dini hari" if language == 'id' else "Good early morning"
    elif 5 <= hour < 10:
        return "Selamat pagi" if language == 'id' else "Good morning"
    elif 10 <= hour < 14:
        return "Selamat siang" if language == 'id' else "Good afternoon"
    elif 14 <= hour < 17:
        return "Selamat sore" if language == 'id' else "Good evening"
    else:
        return "Selamat malam" if language == 'id' else "Good night"

# Fungsi untuk memperbaiki kesalahan ketik
def correct_typo(city_name, city_list):
    closest_match = difflib.get_close_matches(city_name, city_list, n=1, cutoff=0.7)
    return closest_match[0] if closest_match else city_name

# Fungsi untuk mengekstrak nama wilayah dari input teks
def extract_city_name(input_text, city_list):
    for city in city_list:
        if re.search(rf'\b{city}\b', input_text, re.IGNORECASE):
            return city
    return None

# Fungsi untuk mendapatkan kode wilayah dari file Excel dengan looping antar sheet
def get_code(input_text):
    try:
        logger.info("Membaca data dari file Excel.")
        # Membaca file Excel dari URL
        df_dict = pd.read_excel(EXCEL_URL, sheet_name=None)

        levels = ['Provinsi', 'KotaKabupaten', 'Kecamatan', 'Desa']
        result = {}

        for level in levels:
            if level in df_dict:
                df = df_dict[level]
                df.columns = ["kode", "nama"]
                df.dropna(subset=["nama"], inplace=True)

                city_list = df["nama"].unique()
                print(city_list)
                city_name = extract_city_name(input_text, city_list)
                if city_name:
                    corrected_city_name = correct_typo(city_name, city_list)
                    if corrected_city_name != city_name:
                        logger.info(f"Perbaikan kesalahan ketik: {city_name} -> {corrected_city_name}")
                        city_name = corrected_city_name

                    matching_row = df[df["nama"].str.contains(city_name, case=False, na=False)]
                    if not matching_row.empty:
                        result[level] = {
                            "kode": matching_row.iloc[0]["kode"],
                            "nama": matching_row.iloc[0]["nama"]
                        }
                        break

        if not result:
            logger.warning("Kode wilayah tidak ditemukan untuk nama wilayah ini.")
            return None, "Kode wilayah tidak ditemukan untuk nama wilayah ini."

        # Menggabungkan kode wilayah secara hierarkis
        full_code = ".".join([result[level]["kode"] for level in levels if level in result])
        return full_code, None

    except Exception as e:
        logger.error(f"Gagal membaca data dari file Excel: {str(e)}")
        return None, f"Gagal membaca data dari file Excel: {str(e)}"

# Fungsi untuk membangun parameter URL BMKG
def build_bmkg_url(code):
    segments = code.split('.')
    if len(segments) == 1:
        return f"{BMKG_API_ENDPOINT}?adm1={segments[0]}"
    if len(segments) == 2:
        return f"{BMKG_API_ENDPOINT}?adm1={segments[0]}&adm2={segments[0]}.{segments[1]}"
    if len(segments) == 3:
        return f"{BMKG_API_ENDPOINT}?adm1={segments[0]}&adm2={segments[0]}.{segments[1]}&adm3={segments[0]}.{segments[1]}.{segments[2]}"
    if len(segments) >= 4:
        return f"{BMKG_API_ENDPOINT}?adm1={segments[0]}&adm2={segments[0]}.{segments[1]}&adm3={segments[0]}.{segments[1]}.{segments[2]}&adm4={segments[0]}.{segments[1]}.{segments[2]}.{segments[3]}"
    return None

@app.route('/chat/<user_message>', methods=['GET'])
def chat(user_message):
    try:
        if not user_message:
            logger.warning("Pesan tidak boleh kosong.")
            return jsonify({"error": "Pesan tidak boleh kosong."}), 400
        
        # cek dahulu apakah ada nama yang sama atau tidak jika ada
        # return ke user bahwa harus lengkap, karena ada nama yang sama.
        # /
        # if tidak ada keterangan kabupaten / kota  
        # return jsonify({"error": "Pesan harus mengandung nama area."}), 400
        # kata setelah kabupaten / kota
        # ambil katanya dan area nya
        # gunakan area untuk levelnya misal kabupaten A (caru kode kabupaten a) 
        # cari area lain selain yang disebutkan (kabupaten).
        
        # Pengecekan sapaan
        is_greet, lang = is_greeting(user_message)
        if is_greet:
            greeting = get_time_based_greeting(lang)
            logger.info("Merespons sapaan pengguna.")
            return jsonify({"response": f"{greeting}, ada yang bisa saya bantu terkait cuaca suatu daerah?" if lang == 'id'
                             else f"{greeting}, Is there anything I can help you with regarding the weather?"})

        # Dapatkan kode wilayah dari input
        code, error = get_code(user_message)
        if error: 
            logger.warning(f"Error saat mendapatkan kode wilayah: {error}")
            return jsonify({"error": error}), 404

        # Membentuk URL untuk API BMKG
        bmkg_url = build_bmkg_url(code)
        if not bmkg_url:
            logger.error("Gagal membangun URL API BMKG.")
            return jsonify({"error": "Gagal membangun URL API BMKG."}), 500

        # Mengambil data dari API BMKG
        logger.info(f"Mengirim permintaan ke BMKG: {bmkg_url}")
        response = requests.get(bmkg_url, headers={"User-Agent": "MyApplication/1.0 (compatible; MyApp 3.2; Windows NT 10.0; Win64; x64)"})
        response.raise_for_status()

        try:
            bmkg_data = response.json()
        except json.JSONDecodeError:
            logger.error("Gagal membaca data dari API BMKG.")
            return jsonify({"error": "Gagal membaca data dari API BMKG"}), 500

        # Buat prompt untuk model AI
        prompt = f"""
        Data cuaca dari BMKG:
        {bmkg_data}

        Pertanyaan pengguna: 
        {user_message}

       Jawablah pertanyaan pengguna dengan jelas, singkat, sebutkan kecamatan, kabupaten/kota, dan provinsi lokasi yang diminta user berdasarkan data BMKG di atas, serta pastikan jawaban sesuai dengan tanggal dan waktu yang diminta. dan berikan saran kegiatan atau pengingat sesuai kedaan yang terjadi.
        """

        try:
            logger.info("Mengirim prompt ke model AI.")
            response = model.generate_content(prompt)
            answer = response.candidates[0].content.parts[0].text.strip()
        except Exception as e:
            logger.error(f"Gagal mendapatkan respons dari AI: {str(e)}")
            return jsonify({"error": f"Gagal mendapatkan respons dari AI: {str(e)}"}), 500

        logger.info("Berhasil menghasilkan respons untuk pengguna.")
        return jsonify({"response": answer})

    except requests.exceptions.RequestException as e:
        logger.error(f"Gagal menghubungi API BMKG: {str(e)}")
        return jsonify({"error": f"Gagal menghubungi API BMKG: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Terjadi kesalahan: {str(e)}")
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500

if __name__ == '__main__': 
    app.run(debug=True)
