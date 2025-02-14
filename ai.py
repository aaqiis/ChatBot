from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import requests
import re
import json
import difflib
from config import GEMINI_API_KEY, BMKG_API_ENDPOINT
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)
CORS(app)

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
    
    # Dini hari: 00:00 - 04:59
    if 0 <= hour < 5:
        return "Selamat dini hari" if language == 'id' else "Good early morning"
    
    # Pagi: 05:00 - 09:59
    elif 5 <= hour < 10:
        return "Selamat pagi" if language == 'id' else "Good morning"
    
    # Siang: 10:00 - 13:59
    elif 10 <= hour < 14:
        return "Selamat siang" if language == 'id' else "Good afternoon"
    
    # Sore: 14:00 - 16:59
    elif 14 <= hour < 17:
        return "Selamat sore" if language == 'id' else "Good evening"
    
    # Malam: 17:00 - 23:59
    else:
        return "Selamat malam" if language == 'id' else "Good night"

# Fungsi untuk memperbaiki kesalahan ketik
def correct_typo(city_name, city_list):
    closest_match = difflib.get_close_matches(city_name, city_list, n=1, cutoff=0.7)
    return closest_match[0] if closest_match else city_name

# Fungsi untuk mengekstrak nama kota dari input teks
def extract_city_name(input_text, city_list):
    for city in city_list:
        if re.search(rf'\b{city}\b', input_text, re.IGNORECASE):
            return city
    return None

# Fungsi untuk mendapatkan kode wilayah dari input teks
def get_code(input_text):
    # Membaca CSV tanpa header
    df = pd.read_csv("https://raw.githubusercontent.com/kodewilayah/permendagri-72-2019/main/dist/base.csv", header=None)
    
    # Ambil daftar nama kota dari kolom yang ke-1 (indeks 1) tanpa nilai NaN
    city_list = df[1].dropna().unique()
    
    # Ekstrak nama kota dari input
    city_name = extract_city_name(input_text, city_list)
    if not city_name:
        return None, "Nama kota tidak ditemukan dalam input."
    
    # Perbaiki kesalahan ketik jika diperlukan
    corrected_city_name = correct_typo(city_name, city_list)
    if corrected_city_name != city_name:
        print(f"Perbaikan kesalahan ketik: {city_name} -> {corrected_city_name}")
        city_name = corrected_city_name
    
    # Filter baris di mana kolom ke-1 mengandung nama kota
    matching_row = df[df[1].str.contains(city_name, case=False, na=False)]
    
    if not matching_row.empty:
        # Jika ada kecocokan, ambil nilai dari kolom ke-0 (kode yang dimaksud)
        return matching_row.iloc[0][0], None
    
    # Return None if no match is found
    return None, "Kode wilayah tidak ditemukan untuk nama kota ini."

@app.route('/chat/<user_message>', methods=['GET'])
def chat(user_message):
    try:
        if not user_message:
            return jsonify({"error": "Pesan tidak boleh kosong."}), 400
        
    # Pengecekan sapaan
        is_greet, lang = is_greeting(user_message)
        if is_greet:
            greeting = get_time_based_greeting(lang)
            return jsonify({"response": f"{greeting}, ada yang bisa saya bantu terkait cuaca suatu daerah?" if lang == 'id'
                             else f"{greeting}, Is there anything I can help you with regarding the weather?"})

        # Dapatkan kode wilayah dari input
        code, error = get_code(user_message)
        if error: 
            return jsonify({"error": error}), 404

        # Hitung jumlah segmen dalam kode wilayah
        code_length = len(code.split('.'))
        
        # Tentukan tingkat administrasi
        if code_length == 4:
            adm = "adm4"
        elif code_length == 3:
            adm = "adm3"
        elif code_length == 2:
            adm = "adm2"
        else:
            adm = "adm1"

        # Request ke API BMKG
        bmkg_response = requests.get(f"{BMKG_API_ENDPOINT}?{adm}={code}")
        bmkg_response.raise_for_status()  # Pastikan tidak ada error HTTP

        try:
            bmkg_data = bmkg_response.json()  # Parsing JSON dengan aman
        except json.JSONDecodeError:
            return jsonify({"error": "Gagal membaca data dari API BMKG"}), 500

        # Buat prompt untuk model AI
        prompt = f"""
        Data cuaca dari BMKG:
        {bmkg_data}

        Pertanyaan pengguna: 
        {user_message}

       Jawablah pertanyaan pengguna dengan jelas, singkat, sebutkan kecamatan, kabupaten/kota, dan provinsi lokasi yang diminta user berdasarkan data BMKG di atas, serta pastikan jawaban sesuai dengan tanggal dan waktu yang diminta. dan berikan saran kegiatan atau pengingat sesuai kedaan yang terjadi.
        """

#haiQIS
        # Generate response dari model AI
        try:
            response = model.generate_content(prompt)
            answer = response.candidates[0].content.parts[0].text.strip()
        except Exception as e:
            return jsonify({"error": f"Gagal mendapatkan respons dari AI: {str(e)}"}), 500

        return jsonify({"response": answer})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Gagal menghubungi API BMKG: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Terjadi kesalahan: {str(e)}"}), 500

if __name__ == '__main__': 
    app.run(debug=True)


    # HALOOOO