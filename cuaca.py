# Modul utama menangani request informasi cuaca
from utils.location import getName, get_wilayah_code, find_regency_code, format_adm_code
from utils.bmkg_api import getDataBmkg, build_bmkg_url, clean_bmkg_data
from utils.text_processing import process_prompt_gemini, process_prompt_deepseek, process_prompt_gpt
from logger_config import logger
from flask import jsonify,request

    
def chat(user_input, model="gemini"):
    try:
        data = request.get_json()
        user_message = data.get('message')
        model = data.get('model', 'gemini').lower()
        
        if model not in ["gemini", "deepseek", "gpt"]:
            logger.warning("Model tidak dikenali.")
            return {"error": "Model tidak dikenali. Pilih 'gemini', 'deepseek', atau 'gpt'."}
        
        if not user_input:
            logger.warning("Pesan tidak boleh kosong.")
            return jsonify({"error": "Pesan tidak boleh kosong."}), 400
        
        # Mengambil hierarki wilayah dari pesan pengguna
        wilayah_hierarchy = getName(user_input)
        if not wilayah_hierarchy:
            return jsonify({"error": "Wilayah tidak ditemukan dalam pesan Anda."}), 400

        wilayah_level = None
        wilayah_code = None
        

        if wilayah_hierarchy["desa"]:
            wilayah_level = "adm4"
            req_area = getName(user_input)
            logger.info(f"Wilayah yang diminta: {req_area}, file_type: villages")
            wilayah_code = get_wilayah_code("static/data/villages.json", wilayah_hierarchy, "villages")
            logger.info(f"Kode wilayah yang ditemukan: {wilayah_code}")
            bmkg_url = build_bmkg_url(wilayah_level, format_adm_code(wilayah_code))
            bmkg_data = getDataBmkg(bmkg_url)
            
        elif wilayah_hierarchy["kecamatan"]:
            wilayah_level = "adm3"
            req_area = getName(user_input)
            logger.info(f"Wilayah yang diminta: {req_area}, file_type: districts")
            wilayah_code = get_wilayah_code("static/data/districts.json", wilayah_hierarchy, "districts")
            logger.info(f"Kode wilayah yang ditemukan: {wilayah_code}")
            bmkg_url = build_bmkg_url(wilayah_level, format_adm_code(wilayah_code))
            bmkg_data = getDataBmkg(bmkg_url)
        
        elif wilayah_hierarchy["kabupaten"]:
            wilayah_level = "adm2"
            req_area = getName(user_input)
            logger.info(f"Wilayah yang diminta: {req_area}, file_type: regencies")
            wilayah_code = get_wilayah_code("static/data/regencies.json", wilayah_hierarchy, "regencies")
            logger.info(f"Kode wilayah yang ditemukan: {wilayah_code}")
            bmkg_url = build_bmkg_url(wilayah_level, format_adm_code(wilayah_code))
            bmkg_data = getDataBmkg(bmkg_url)
            
        else:
            return jsonify({"error": "Harap sebutkan dan cantumkan kata desa, kecamatan, atau kabupaten dalam pesan Anda."}), 400

        if not wilayah_code:
            return jsonify({"error": "Wilayah tidak ditemukan dalam database."}), 404
        
        if not bmkg_data:
            return jsonify({"error": "Gagal mengambil data dari BMKG."}), 500
        
        logger.info(f"✅ Model AI yang digunakan: {model}")

        # Panggil model berdasarkan pilihan pengguna
        if model == "gemini":
            answer = process_prompt_gemini(bmkg_data, user_input)
        elif model == "deepseek":
            answer = process_prompt_deepseek(bmkg_data, user_input)
        elif model == "gpt":
            answer = process_prompt_gpt(bmkg_data, user_input)
        else:
            logger.warning("Model tidak dikenali.")
            return jsonify({"error": "Model tidak dikenali."}), 400

        # Kembalikan respons
        return jsonify({"response": answer, "model": model})

    except Exception as e:
        logger.error(f"Terjadi kesalahan: {e}")
        return jsonify({"error": str(e)}), 500

def process_request(json_file, user_input):
    wilayah = getName(user_input)
    wilayah_code = get_wilayah_code(json_file, wilayah)

    if wilayah_code is None:
        logger.error("Kode wilayah tidak valid. Tidak ditemukan dalam file JSON.")
        return {"error": "Kode wilayah tidak ditemukan."}

    return {"wilayah_code": wilayah_code}
    