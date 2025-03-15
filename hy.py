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

EXCEL_URL = "https://docs.google.com/spreadsheets/d/1Lb3JC13xYVh9BsKLO_mt1g6t4EoHKzpd/export?format=xlsx"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def get_wilayah_code(json_file, search_text):
    try:
        # Membaca file JSON
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Looping untuk mencari kecocokan
        for entry in data:
            if search_text.lower() in entry["label"].lower():
                return entry["value"]
        
        return None  # Jika tidak ditemukan

    except Exception as e:
        return f"Error: {str(e)}"
    
@app.route('/')
def index():
    return render_template('index1.html')

# Fungsi untuk memeriksa apakah pesan adalah sapaan
def is_greeting(user_message):
    greetings = ["halo", "hi", "hai", "hy" "selamat pagi", "selamat siang", "selamat sore", "selamat malam", "good morning", "good afternoon", "good evening", "good night"]
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
def correct_typo(name, name_list):
    closest_match = difflib.get_close_matches(name, name_list, n=1, cutoff=0.7)
    return closest_match[0] if closest_match else name

# Fungsi untuk mengekstrak nama wilayah dari input teks
def extract_location_name(input_text, name_list):
    for name in name_list:
        if re.search(rf'\b{name}\b', input_text, re.IGNORECASE):
            return name
    return None

# Fungsi untuk mendapatkan kode wilayah berdasarkan prioritas hierarki
def get_hierarchical_code(input_text):
    try:
        logger.info("Membaca data dari file Excel.")
        df_dict = pd.read_excel(EXCEL_URL, sheet_name=None)

        levels = ['Provinsi', 'KotaKabupaten', 'Kecamatan', 'Desa']
        result = {}

        if 'KotaKabupaten' not in df_dict:
            return None, "Data Kota/Kabupaten tidak tersedia."

        kota_kabupaten_df = df_dict['KotaKabupaten']
        kota_kabupaten_df.columns = ["kode", "nama"]
        kota_kabupaten_df.dropna(subset=["nama"], inplace=True)
        kota_kabupaten_df["nama"] = kota_kabupaten_df["nama"].astype(str)
        

        # Wajib mencantumkan nama kabupaten/kota
        kota_kabupaten_list = kota_kabupaten_df["nama"].unique()
        print (kota_kabupaten_list)
        kota_kabupaten_name = extract_location_name(input_text, kota_kabupaten_list)
        if not kota_kabupaten_name:
            return None, "Pesan harus mencantumkan nama kabupaten/kota."

        corrected_kota_kabupaten_name = correct_typo(kota_kabupaten_name, kota_kabupaten_list)
        if corrected_kota_kabupaten_name != kota_kabupaten_name:
            logger.info(f"Perbaikan kesalahan ketik: {kota_kabupaten_name} -> {corrected_kota_kabupaten_name}")
            kota_kabupaten_name = corrected_kota_kabupaten_name

        matching_kota_kabupaten = kota_kabupaten_df[kota_kabupaten_df["nama"].str.contains(kota_kabupaten_name, case=False, na=False)]
        if matching_kota_kabupaten.empty:
            return None, "Kode untuk kabupaten/kota tidak ditemukan."

        result['KotaKabupaten'] = {
            "kode": matching_kota_kabupaten.iloc[0]["kode"],
            "nama": matching_kota_kabupaten.iloc[0]["nama"]
        }

        # Opsional: Kecamatan
        if 'Kecamatan' in df_dict:
            kecamatan_df = df_dict['Kecamatan']
            kecamatan_df.columns = ["kode", "nama"]
            kecamatan_df.dropna(subset=["nama"], inplace=True)
            kecamatan_df["nama"] = kecamatan_df["nama"].astype(str)
            

            kecamatan_list = kecamatan_df["nama"].unique()
            kecamatan_name = extract_location_name(input_text, kecamatan_list)
            if kecamatan_name:
                corrected_kecamatan_name = correct_typo(kecamatan_name, kecamatan_list)
                if corrected_kecamatan_name != kecamatan_name:
                    logger.info(f"Perbaikan kesalahan ketik: {kecamatan_name} -> {corrected_kecamatan_name}")
                    kecamatan_name = corrected_kecamatan_name
                    
                matching_kecamatan = kecamatan_df[kecamatan_df["nama"].str.contains(kecamatan_name, case=False, na=False)]
            if not matching_kecamatan.empty:
                # Verifikasi apakah kecamatan ini sesuai dengan kabupaten
                kabupaten_code = result['KotaKabupaten']['kode']
                if matching_kecamatan.iloc[0]["kode"].startswith(kabupaten_code):
                    result['Kecamatan'] = {
                        "kode": matching_kecamatan.iloc[0]["kode"],
                        "nama": matching_kecamatan.iloc[0]["nama"]
                    }

        # Opsional: Desa
        if 'Desa' in df_dict:
            desa_df = df_dict['Desa']
            desa_df.columns = ["kode", "nama"]
            desa_df.dropna(subset=["nama"], inplace=True)
            desa_df["nama"] = desa_df["nama"].astype(str)
            

            desa_list = desa_df["nama"].unique()
            desa_name = extract_location_name(input_text, desa_list)
            if desa_name:
                corrected_desa_name = correct_typo(desa_name, desa_list)
                if corrected_desa_name != desa_name:
                    logger.info(f"Perbaikan kesalahan ketik: {desa_name} -> {corrected_desa_name}")
                    desa_name = corrected_desa_name

                matching_desa = desa_df[desa_df["nama"].str.contains(desa_name, case=False, na=False)]
        if not matching_desa.empty:
            # Verifikasi hubungan desa dengan kecamatan
            kecamatan_code = result.get('Kecamatan', {}).get('kode', '')
            if matching_desa.iloc[0]["kode"].startswith(kecamatan_code):
                result['Desa'] = {
                    "kode": matching_desa.iloc[0]["kode"],
                    "nama": matching_desa.iloc[0]["nama"]
                }

        
        # Menentukan kode provinsi
        result['Provinsi'] = {
            "kode": "35",
            "nama": "Jawa Timur"
        }
        if not result:
            logger.warning("Kode wilayah tidak ditemukan untuk nama wilayah ini.")
            return None, "Kode wilayah tidak ditemukan untuk nama wilayah ini."

        # Menggabungkan kode wilayah secara hierarkis
        full_code = ".".join([result[level]["kode"] for level in levels if level in result])
        return full_code, None

    except Exception as e:
        logger.error(f"Gagal membaca data dari file Excel: {str(e)}")
        return None, f"Gagal membaca data dari file Excel: {str(e)}"

# Fungsi untuk membangun URL BMKG
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
        
        # Pengecekan sapaan
        is_greet, lang = is_greeting(user_message)
        if is_greet:
            greeting = get_time_based_greeting(lang)
            logger.info("Merespons sapaan pengguna.")
            return jsonify({"response": f"{greeting}, ada yang bisa saya bantu terkait cuaca suatu daerah?" if lang == 'id'
                             else f"{greeting}, Is there anything I can help you with regarding the weather?"})


        # Dapatkan kode wilayah dari input
        code, error = get_hierarchical_code(user_message)
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
