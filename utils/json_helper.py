import json
from logger_config import logger

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


