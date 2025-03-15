from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import requests
import re
import json
import logging
from config import GEMINI_API_KEY, DEEPSEEK_API_KEY, GPT_API_KEY

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
    user_message = user_message.lower()

    user_message = re.sub(
    r"\b(besok|lusa|hari ini|jam|nanti|siang|sore|malam|pagi|saat ini|sebentar lagi|lagi|barusan|baru saja|bentar|sering|jarang|setiap|tiap|terkadang|sekarang|"
    r"apakah|bagaimana|seperti apa|kapan|dimana|mengapa|kenapa|sedang|itu|di|berada|ada|mungkinkah|mungkin|akan|emang|akankah|yakin(kah)?|sudah(kah)?|masih(kah)?|betul(kah)?|"
    r"sering(kah)?|ada(kah)?|bisa(kah)?|tidak(kah)?|bener(an)?|benar|mau|agak|lumayan|terlalu|cukup|hujan|panas|mendung|cerah|berawan|gerimis|dingin|hangat|kabut|badai|"
    r"angin|petir|suhu)\b|\d+|[^\w\s]",
    "",
    user_message
)

    wilayah = {"desa": None, "kecamatan": None, "kabupaten": None}

    # Tangkap format lengkap: "desa/kelurahan X kecamatan Y kabupaten/kota Z"
    match = re.search(
        r"(?:desa|kelurahan)\s+([\w\-]+(?:\s[\w\-]+)*)\s+kecamatan\s+([\w\-]+(?:\s[\w\-]+)*)\s+(?:kabupaten|kota)\s+([\w\-]+(?:\s[\w\-]+)*)",
        user_message
    )
    if match:
        wilayah["desa"] = match.group(1).strip()
        wilayah["kecamatan"] = match.group(2).strip()
        wilayah["kabupaten"] = match.group(3).strip()
        return wilayah

    # Tangkap "desa/kelurahan X kecamatan Y"
    match = re.search(
        r"(?:desa|kelurahan)\s+([\w\-]+(?:\s[\w\-]+)*)\s+kecamatan\s+([\w\-]+(?:\s[\w\-]+)*)",
        user_message
    )
    if match:
        wilayah["desa"] = match.group(1).strip()
        wilayah["kecamatan"] = match.group(2).strip()
        return wilayah

    # Tangkap "desa/kelurahan X kabupaten/kota Z"
    match = re.search(
        r"(?:desa|kelurahan)\s+([\w\-]+(?:\s[\w\-]+)*)\s+(?:kabupaten|kota)\s+([\w\-]+(?:\s[\w\-]+)*)",
        user_message
    )
    if match:
        wilayah["desa"] = match.group(1).strip()
        wilayah["kabupaten"] = match.group(2).strip()
        return wilayah

    # Tangkap "kecamatan Y kabupaten/kota Z"
    match = re.search(
        r"kecamatan\s+([\w\-]+(?:\s[\w\-]+)*)\s+(?:kabupaten|kota)\s+([\w\-]+(?:\s[\w\-]+)*)",
        user_message
    )
    if match:
        wilayah["kecamatan"] = match.group(1).strip()
        wilayah["kabupaten"] = match.group(2).strip()
        return wilayah

    # Tangkap "kabupaten/kota Z"
    match = re.search(r"(kabupaten|kota)\s+([\w\-]+(?:\s[\w\-]+)*)", user_message)
    if match:
        prefiks, nama = match.groups()
        wilayah["kabupaten"] = f"{prefiks.title()} {nama.title()}"
        return wilayah

    # Tangkap "Z" saja tanpa prefiks
    match = re.search(r"([\w\-]+(?:\s[\w\-]+)*)", user_message)
    if match:
        wilayah["kabupaten"] = match.group(1).title()

    logger.info(f"DEBUG - Wilayah yang diparsing: {wilayah}")
    return wilayah




def convertJSON(data, file_type):
    """
    Memproses data JSON sesuai dengan jenis file.

    Parameters:
        data (list): Data dari file JSON.
        file_type (str): Jenis file ('villages', 'districts', 'regencies').

    Returns:
        list: Data yang telah diproses.
    """
    try:
        if file_type == "villages":
            return [{"label": item["label"], "value": item["value"]} for item in data]
        elif file_type == "districts":
            return [{"label": item["label"], "value": item["value"]} for item in data]
        elif file_type == "regencies":
            return [{"label": item["label"], "value": item["value"]} for item in data]
        else:
            return []
    except KeyError as e:
        logger.error(f"Error saat membaca key '{e}' dalam JSON.")
        return []




def format_adm_code(adm_code):
    if len(adm_code) == 10:
        return f"{adm_code[:2]}.{adm_code[2:4]}.{adm_code[4:6]}.{adm_code[6:]}"
    elif len(adm_code) == 6:
        return f"{adm_code[:2]}.{adm_code[2:4]}.{adm_code[4:]}"
    elif len(adm_code) == 4:
        return f"{adm_code[:2]}.{adm_code[2:]}"
    return adm_code


def load_json(file_path):
    """Membaca data dari file JSON."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
    

def normalize_regencies_data(regencies):
    """
    Normalisasi data regencies untuk mendukung pencocokan parsial.
    """
    normalized_data = []
    for regency in regencies:
        if "KOTA" in regency["label"]:
            category = "Kota"
            normalized_label = regency["label"].replace("KOTA ", "").strip()
        else:
            category = "Kabupaten"
            normalized_label = regency["label"].strip()

        normalized_data.append({
            "value": regency["value"],
            "original_label": regency["label"],
            "normalized_label": normalized_label.upper(),
            "type": category
        })
    return normalized_data


def find_regency_code(input_text, regencies):
    """
    Pencocokan wilayah dengan input user.
    """
    input_text = input_text.strip().upper()
    matches = []

    # Cari kecocokan
    for regency in regencies:
        if input_text == regency["normalized_label"]:
            matches.append(regency)

    if len(matches) == 1:
        return matches[0]["value"], matches[0]["original_label"]
    elif len(matches) > 1:
        return None, matches  # Kembalikan daftar untuk disambiguasi
    return None, None

    

def get_wilayah_code(json_file, wilayah, file_type=None):
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # Tentukan file_type berdasarkan input wilayah
        if not file_type:
            if wilayah["kabupaten"]:
                file_type = "regencies"
            elif wilayah["kecamatan"]:
                file_type = "districts"
            elif wilayah["desa"]:
                file_type = "villages"
            else:
                logger.error("Wilayah tidak valid: Tidak ada kabupaten/kota, kecamatan, atau desa/kelurahan.")
                return None

        # Ambil data input
        desa = wilayah.get("desa", "").lower().strip() if wilayah.get("desa") else None
        kecamatan = wilayah.get("kecamatan", "").lower().strip() if wilayah.get("kecamatan") else None
        kabupaten = wilayah.get("kabupaten", "").lower().strip() if wilayah.get("kabupaten") else None

        # Normalisasi kabupaten untuk mencocokkan tanpa prefiks
        if file_type == "regencies":
            kabupaten_normalized = re.sub(r"^(kabupaten|kota)\s+", "", kabupaten).strip()

        # Variabel untuk hasil pencarian
        results = []

        # Logika pencocokan wilayah
        for entry in data:
            label = entry["label"].strip().lower()

            if file_type == "villages":
                # Cocokkan desa, kecamatan, kabupaten
                label_parts = [p.strip().lower() for p in entry["label"].split(",")]
                if len(label_parts) == 3:
                    desa_entry, kecamatan_entry, kabupaten_entry = label_parts
                    if desa == desa_entry and \
                       (not kecamatan or kecamatan == kecamatan_entry) and \
                       (not kabupaten or kabupaten == kabupaten_entry):
                        return entry["value"]

            elif file_type == "districts":
                # Cocokkan kecamatan, kabupaten
                label_parts = [p.strip().lower() for p in entry["label"].split(",")]
                if len(label_parts) == 2:
                    kecamatan_entry, kabupaten_entry = label_parts
                    if kecamatan == kecamatan_entry and \
                       (not kabupaten or kabupaten == kabupaten_entry):
                        return entry["value"]

            elif file_type == "regencies":
                # Tangani kasus dengan prefiks "Kabupaten" atau "Kota"
                if "kabupaten" in kabupaten.lower():
                    # Cari label tanpa kata "Kota"
                    if kabupaten_normalized in label and "kota" not in label:
                        return entry["value"]
                elif "kota" in kabupaten.lower():
                    # Cari label dengan kata "Kota"
                    if kabupaten_normalized in label and "kota" in label:
                        return entry["value"]
                else:
                    # Jika tidak ada prefiks, tambahkan ke hasil
                    if kabupaten_normalized in label:
                        results.append(entry)

        # Menangani hasil akhir
        if len(results) == 1:
            return results[0]["value"]
        elif len(results) > 1:
            logger.error(f"Ambiguitas ditemukan: {results}")
            return None
        else:
            logger.error("Kode wilayah tidak ditemukan.")
            return None

    except Exception as e:
        logger.error(f"Error membaca JSON: {str(e)}")
        return None




# Validasi nilai yang dikembalikan oleh get_wilayah_code
def process_request(json_file, user_message):
    wilayah = getName(user_message)
    wilayah_code = get_wilayah_code(json_file, wilayah)

    if wilayah_code is None:
        logger.error("Kode wilayah tidak valid. Tidak ditemukan dalam file JSON.")
        return {"error": "Kode wilayah tidak ditemukan."}

    return {"wilayah_code": wilayah_code}
    

def cari_lokasi(nama_desa=None, nama_kecamatan=None, nama_kabupaten=None, tipe="desa"):
    """
    Mencari lokasi berdasarkan hierarki administratif.

    Parameters:
        nama_desa (str): Nama desa (opsional, tergantung tipe).
        nama_kecamatan (str): Nama kecamatan (wajib untuk desa).
        nama_kabupaten (str): Nama kabupaten (wajib untuk kecamatan).
        tipe (str): Jenis pencarian ("desa" atau "kecamatan").

    Returns:
        dict/str: Hasil pencarian lokasi atau pesan error jika tidak ditemukan.
    """
    if tipe == "desa" and (not nama_desa or not nama_kecamatan):
        return "Nama desa dan kecamatan harus diisi."
    if tipe == "kecamatan" and (not nama_kecamatan or not nama_kabupaten):
        return "Nama kecamatan dan kabupaten harus diisi."

    data = load_json(f"static/data{'villages' if tipe == 'desa' else 'districts'}.json")

    nama_desa = nama_desa.lower().strip() if nama_desa else None
    nama_kecamatan = nama_kecamatan.lower().strip()
    nama_kabupaten = nama_kabupaten.lower().strip() if nama_kabupaten else None

    hasil = []
    for item in data:
        if tipe == "desa":
            if item["desa"].lower() == nama_desa and item["kecamatan"].lower() == nama_kecamatan:
                if nama_kabupaten and item["kabupaten"].lower() != nama_kabupaten:
                    continue
                hasil.append(item)
        elif tipe == "kecamatan":
            if item["kecamatan"].lower() == nama_kecamatan and item["kabupaten"].lower() == nama_kabupaten:
                hasil.append(item)

    if len(hasil) == 0:
        return "Data tidak ditemukan."
    elif len(hasil) > 1:
        return "Data ambigu. Hasil yang ditemukan: " + str(hasil)
    else:
        return hasil[0]
    
def getDataBmkg(bmkg_url):
    try:
        logger.info(f"Mengirim permintaan ke BMKG: {bmkg_url}")
        response = requests.get(bmkg_url, headers={"User-Agent": "MyApplication/1.0"})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Gagal menghubungi API BMKG: {e}")
        return None
    except ValueError as e:
        logger.error(f"Kesalahan parsing JSON: {e}")
        return None
    
# Fungsi untuk memproses prompt dan mendapatkan respons AI
def process_prompt_gemini(bmkg_data, user_message):
    # Ambil waktu saat ini
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
    Data cuaca dari BMKG:
    {bmkg_data}

    Pertanyaan pengguna:
    {user_message}

    Waktu saat ini adalah {formatted_time} WIB ({time_of_day}).
    Jawablah pertanyaan pengguna dengan jelas, singkat, sebutkan lokasi, serta berikan saran kegiatan atau pengingat sesuai keadaan yang terjadi.
    -Pukul 05.00-12.00 menunjukkan Pagi
    -Pukul 12.00-15.00 menunjukkan Siang
    -Pukul 15.00-18.00 menunjukkan Sore
    -Pukul 19.00-22.00 menunjukkan Malam
    -Pukul 01.00-05.00 menunjukkan Dini Hari
    """
    logger.info("Mengirim prompt ke model AI.")
    response = model.generate_content(prompt)
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


def process_prompt_gpt(bmkg_data, user_message):
    url = "https://chatgpt-42.p.rapidapi.com/gpt4"
    prompt = f"""
    Data cuaca dari BMKG:
    {bmkg_data}

    Pertanyaan pengguna:
    {user_message}

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



@app.route('/')
def index():
    return render_template('index2.html')

def build_bmkg_url(level, code):
    
    level_mapping = {
        "adm1": "adm1",  # Provinsi
        "adm2": "adm2",  # Kabupaten/Kota
        "adm3": "adm3",  # Kecamatan
        "adm4": "adm4",  # Desa
    }
    parameter = level_mapping.get(level)
    return f"{BMKG_API_ENDPOINT}?{parameter}={code}"



@app.route('/chat', methods=['GET'])
def chat():
    try:
        # Ambil input dari query string
        user_message = request.args.get('message')
        model = request.args.get('model', 'gemini').lower()

        if not user_message:
            logger.warning("Pesan tidak boleh kosong.")
            return jsonify({"error": "Pesan tidak boleh kosong."}), 400

        if model not in ['gemini', 'deepseek', 'gpt']:
            logger.warning(f"Model tidak valid: {model}")
            return jsonify({"error": "Model tidak valid. Pilih 'gemini', 'deepseek', atau 'gpt'."}), 400

        # Ambil hierarki wilayah dari pesan pengguna
        wilayah_hierarchy = getName(user_message)
        if not wilayah_hierarchy:
            logger.warning("Wilayah tidak ditemukan dalam pesan.")
            return jsonify({"error": "Wilayah tidak ditemukan dalam pesan Anda. Harap berikan format yang jelas."}), 400

        logger.info(f"Wilayah yang diparsing: {wilayah_hierarchy}")

        # Tentukan level wilayah dan kode wilayah
        wilayah_level, wilayah_code = None, None
        bmkg_url = None

        if wilayah_hierarchy["desa"]:
            wilayah_level = "adm4"
            wilayah_code = get_wilayah_code("static/data/villages.json", wilayah_hierarchy, "villages")
        elif wilayah_hierarchy["kecamatan"]:
            wilayah_level = "adm3"
            wilayah_code = get_wilayah_code("static/data/districts.json", wilayah_hierarchy, "districts")
        elif wilayah_hierarchy["kabupaten"]:
            wilayah_level = "adm2"
            wilayah_code = get_wilayah_code("static/data/regencies.json", wilayah_hierarchy, "regencies")
        else:
            return jsonify({"error": "Wilayah tidak valid. Harap sebutkan desa, kecamatan, atau kabupaten."}), 400

        if not wilayah_code:
            logger.warning("Kode wilayah tidak ditemukan.")
            return jsonify({"error": "Wilayah tidak ditemukan dalam database."}), 404

        # Bangun URL BMKG
        bmkg_url = build_bmkg_url(wilayah_level, format_adm_code(wilayah_code))
        logger.info(f"BMKG URL: {bmkg_url}")

        # Ambil data BMKG
        bmkg_data = getDataBmkg(bmkg_url)
        if not bmkg_data:
            logger.error("Gagal mengambil data dari BMKG.")
            return jsonify({"error": "Gagal mengambil data dari BMKG."}), 500

        # Panggil model berdasarkan pilihan pengguna
        if model == "gemini":
            answer = process_prompt_gemini(bmkg_data, user_message)
        elif model == "deepseek":
            answer = process_prompt_deepseek(bmkg_data, user_message)
        elif model == "gpt":
            answer = process_prompt_gpt(bmkg_data, user_message)
        else:
            logger.warning("Model tidak dikenali.")
            return jsonify({"error": "Model tidak dikenali."}), 400

        # Kembalikan respons
        return jsonify({"response": answer, "model": model})

    except Exception as e:
        logger.error(f"Terjadi kesalahan: {e}")
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True)