# Modul berfungsi untuk mengambil data dari API BMKG
import requests
from logger_config import logger
from config import BMKG_API_ENDPOINT

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

