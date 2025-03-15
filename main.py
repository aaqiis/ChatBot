from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import requests
import re
import json
import logging
from config import GEMINI_API_KEY
import google.generativeai as genai
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

BMKG_API_ENDPOINT = "https://api.bmkg.go.id/publik/prakiraan-cuaca"

def getName(user_message):
    """
    Mengekstrak nama wilayah dari pesan pengguna berdasarkan kata kunci lokasi.

    Parameters:
        user_message (str): Pesan pengguna yang mengandung informasi lokasi.

    Returns:
        str: Nama wilayah yang diekstrak dari pesan pengguna, atau None jika tidak ditemukan.
    """
    # Daftar kata kunci yang terkait dengan tingkat administratif
    keywords = ["desa", "kelurahan", "kecamatan", "kabupaten", "kota", "provinsi"]

    # Ubah pesan menjadi huruf kecil agar pencarian tidak case-sensitive
    message_lower = user_message.lower()

    for keyword in keywords:
        # Gunakan regex untuk mencari kata kunci diikuti oleh nama wilayah
        match = re.search(rf"{keyword}\s+([a-zA-Z\s]+)", message_lower)
        if match:
            # Kembalikan nama wilayah tanpa kata kunci
            return match.group(1).strip()

    return None

def convertJSON(data):
    processed_data = [
    {"label": item["label"].split(",")[0], "value": item["value"]}
    for item in data
    ]
    return processed_data

def filter_lokasi(data, adm_type, adm_code):
    """
    Memfilter lokasi berdasarkan kode administratif (adm1 untuk kabupaten, adm2 untuk kecamatan).
    
    Parameters:
        data (dict): Data JSON yang berisi informasi lokasi dan cuaca.
        adm_type (str): Jenis administratif ('adm1' untuk kabupaten, 'adm2' untuk kecamatan).
        adm_code (str): Kode administratif yang akan difilter.
    
    Returns:
        list: Daftar lokasi yang sesuai dengan filter.
    """
    filtered_data = []
    
    for entry in data.get("data", []):
        lokasi = entry.get("lokasi", {})
        
        if adm_type == "adm1" and lokasi.get("adm2") == adm_code:
            filtered_data.append(entry)
        elif adm_type == "adm2" and lokasi.get("adm3") == adm_code:
            filtered_data.append(entry)
        
    
    return filtered_data



def format_adm_code(adm_code):
    print(adm_code)
    if len(adm_code) == 10:
        return f"{adm_code[:2]}.{adm_code[2:4]}.{adm_code[4:6]}.{adm_code[6:]}"
    elif len(adm_code) == 6:
        return f"{adm_code[:2]}.{adm_code[2:4]}.{adm_code[4:]}"
    elif len(adm_code) == 4:
        return f"{adm_code[:2]}.{adm_code[2:]}"
    return adm_code


# Fungsi untuk mendapatkan kode wilayah dari file JSON
def get_wilayah_code(json_file, search_text):
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            data = convertJSON(data)
            
        for entry in data:
            if search_text.lower() in entry["label"].lower():
                return entry["value"]
        
        return None  # Jika tidak ditemukan
    except Exception as e:
        return None

@app.route('/')
def index():
    return render_template('index1.html')

# Fungsi untuk membangun URL BMKG
def build_bmkg_url(level, code):
    return f"{BMKG_API_ENDPOINT}?{level}={code}"

@app.route('/chat/<user_message>', methods=['GET']) 
def chat(user_message):
    try:
        if not user_message:
            logger.warning("Pesan tidak boleh kosong.")
            return jsonify({"error": "Pesan tidak boleh kosong."}), 400
        
        wilayah_level = None
        wilayah_code = None
        
        # Cek apakah user menyebut desa, kecamatan, atau kabupaten
        if any(keyword in user_message.lower() for keyword in ["desa", "kelurahan"]):
            wilayah_level = "adm4"
            req_area = getName(user_message)
            wilayah_code = get_wilayah_code("static/villages.json", req_area)
            bmkg_url = build_bmkg_url(wilayah_level, format_adm_code(wilayah_code))
            logger.info(f"Mengirim permintaan ke BMKG: {bmkg_url}")
            response = requests.get(bmkg_url, headers={"User-Agent": "MyApplication/1.0"})
            response.raise_for_status()
            
            try:
                bmkg_data = response.json()
            except json.JSONDecodeError:
                logger.error("Gagal membaca data dari API BMKG.")
                return jsonify({"error": "Gagal membaca data dari API BMKG"}), 500

            
            
        elif "kecamatan" in user_message.lower():
            wilayah_level = "adm2"
            req_area = getName(user_message)
            wilayah_code = get_wilayah_code("static/districts.json", req_area)
            bmkg_url = build_bmkg_url(wilayah_level, ".".join(format_adm_code(wilayah_code).split(".")[:2]))
            logger.info(f"Mengirim permintaan ke BMKG: {bmkg_url}")
            response = requests.get(bmkg_url, headers={"User-Agent": "MyApplication/1.0"})
            response.raise_for_status()
            
            try:
                bmkg_data = response.json()
                bmkg_data = filter_lokasi(bmkg_data,"adm2", format_adm_code(wilayah_code))
            except json.JSONDecodeError:
                logger.error("Gagal membaca data dari API BMKG.")
                return jsonify({"error": "Gagal membaca data dari API BMKG"}), 500

        elif "kabupaten" in user_message.lower() or "kota" in user_message.lower():
            wilayah_level = "adm1"
            req_area = getName(user_message)
            wilayah_code = get_wilayah_code("static/regencies.json", req_area)
            bmkg_url = build_bmkg_url(wilayah_level, ".".join(format_adm_code(wilayah_code).split(".")[:1]))
            logger.info(f"Mengirim permintaan ke BMKG: {bmkg_url}")
            response = requests.get(bmkg_url, headers={"User-Agent": "MyApplication/1.0"})
            response.raise_for_status()
            
            try:
                bmkg_data = response.json()
                bmkg_data = filter_lokasi(bmkg_data,"adm1", format_adm_code(wilayah_code))
            except json.JSONDecodeError:
                logger.error("Gagal membaca data dari API BMKG.")
                return jsonify({"error": "Gagal membaca data dari API BMKG"}), 500

        else:
            return jsonify({"error": "Harap sebutkan desa, kecamatan, atau kabupaten dalam pesan Anda."}), 400
        
        if not wilayah_code:
            return jsonify({"error": "Wilayah tidak ditemukan dalam database."}), 404

        
       
        # Buat prompt untuk AI
        prompt = f"""
        Data cuaca dari BMKG:
        {bmkg_data}

        Pertanyaan pengguna: 
        {user_message}

        Jawablah pertanyaan pengguna dengan jelas, singkat, sebutkan lokasi berdasarkan data BMKG di atas, serta berikan saran kegiatan atau pengingat sesuai keadaan yang terjadi.
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
