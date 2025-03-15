# Modul untuk mengenali/Mencari lokasi wilayah yang disebutkan user
import re
import json
from logger_config import logger
from utils.json_helper import load_json
from fuzzywuzzy import fuzz, process
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

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

    data = load_json(f"static/{'villages' if tipe == 'desa' else 'districts'}.json")

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


def format_adm_code(adm_code):
    if len(adm_code) == 10:
        return f"{adm_code[:2]}.{adm_code[2:4]}.{adm_code[4:6]}.{adm_code[6:]}"
    elif len(adm_code) == 6:
        return f"{adm_code[:2]}.{adm_code[2:4]}.{adm_code[4:]}"
    elif len(adm_code) == 4:
        return f"{adm_code[:2]}.{adm_code[2:]}"
    return adm_code


def process_request(json_file, user_input):
    wilayah = getName(user_input)
    wilayah_code = get_wilayah_code(json_file, wilayah)

    if wilayah_code is None:
        logger.error("Kode wilayah tidak valid. Tidak ditemukan dalam file JSON.")
        return {"error": "Kode wilayah tidak ditemukan."}

    return {"wilayah_code": wilayah_code}