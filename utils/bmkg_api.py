# Modul berfungsi untuk mengambil data dari API BMKG
import requests
from logger_config import logger
from config import BMKG_API_ENDPOINT
import re

def preprocess_bmkg_url(url):
    """Menghapus https:// hanya untuk logging, bukan dari request API."""
    if not isinstance(url, str):
        return url  # Jika bukan string, biarkan tetap

    # Simpan versi asli URL untuk request (tidak diubah)
    clean_url = url

    # Hapus protokol hanya untuk logging atau tampilan di AI
    log_url = re.sub(r"https?://(www\.)?", "", url)

    return clean_url, log_url


def getDataBmkg(bmkg_url):
    try:
        logger.info(f"Mengirim permintaan ke BMKG: {bmkg_url}")
        response = requests.get(bmkg_url, headers={"User-Agent": "MyApplication/1.0"})
        response.raise_for_status()
        return clean_bmkg_data(response.json())
    except requests.exceptions.RequestException as e:
        logger.error(f"Gagal menghubungi API BMKG: {e}")
        return None
    except ValueError as e:
        logger.error(f"Kesalahan parsing JSON: {e}")
        return None
    
    
def clean_bmkg_data(data):
    if not data:
        return None

    # 1. Bersihkan lokasi di level global jika ada
    if "lokasi" in data and isinstance(data["lokasi"], dict):
        data["lokasi"].pop("lon", None)
        data["lokasi"].pop("lat", None)
        data["lokasi"].pop("timezone", None)
    
    for entry in data.get("data", []):
        # Membersihkan data cuaca
        for forecast in entry.get("cuaca", []):
            for item in forecast:
                item.pop("image", None)
                item.pop("url", None)
                item.pop("tcc", None)
                item.pop("weather", None)
                item.pop("time_index", None)
                item.pop("utc_datetime", None)
                item.pop("analysis_date", None)
                item.pop("weather_desc_en", None)
                item.pop("datetime", None)
                item.pop("vs", None)

        # Membersihkan data lokasi (harus tetap dalam loop utama!)
        if "lokasi" in entry and isinstance(entry["lokasi"], dict):
            entry["lokasi"].pop("lon", None)
            entry["lokasi"].pop("lat", None)
            entry["lokasi"].pop("timezone", None)

    return data

def build_bmkg_url(level, code):
    """
    Membuat URL BMKG dengan parameter yang sesuai berdasarkan level wilayah.

    Parameters:
        level (str): Level wilayah (adm1, adm2, adm3, adm4).
        code (str): Kode wilayah.
    Returns:
        str: URL yang sesuai untuk permintaan API BMKG.
    """
    # Map level ke parameter API yang benar
    level_mapping = {
        "adm1": "adm1",  
        "adm2": "adm2",  
        "adm3": "adm3",  
        "adm4": "adm4",  
    }
    parameter = level_mapping.get(level)
    return f"{BMKG_API_ENDPOINT}?{parameter}={code}"

