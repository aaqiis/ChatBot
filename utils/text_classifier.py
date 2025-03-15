# Modul untuk menangani keywords yang dapat ditanyakan pada informasi umum
from fuzzywuzzy import fuzz

# Fungsi untuk memeriksa apakah pesan terkait fenomena alam atau cuaca
def is_weather_related(message):
    keywords = [
        "cuaca","cahaya", "hujan", "panas", "dingin", "suhu", "angin", "topan", "gempa", "tsunami",
        "meteorologi", "iklim", "musim", "awan", "hujan deras", "badai", "petir", "kabut",
        "fenomena alam", "tornado", "salju", "el nino", "la nina", "pelangi", "BMKG",
        "termometer", "barometer", "kelembaban", "tekanan udara", "curah hujan",
        "siklon", "antisiklon", "gelombang panas", "gelombang dingin", "radiasi matahari",
        "aurora", "kabut asap", "haze", "cuaca ekstrem", "debu atmosfer", "magnitudo",
        "epicentrum", "seismograf", "klimatologi", "stratosfer", "ozon", "efek rumah kaca",
        "pola angin", "monsun", "zenith", "uv", "pasang surut", "anomali cuaca","taman alat"
        "anemometer", "barometer", "higrometer", "termometer", "radar cuaca",
        "seismograf", "teleskop matahari", "weather balloon", "spektrofotometer ozon",
        "disdrometer", "lidar atmosfer", "rain gauge", "satelit cuaca",
        "weather buoy", "heliograf", "sensor gempa", "alat pemantau tsunami",
        "spektrometer inframerah", "ceilometer", "AWS (Automatic Weather Station)",
        "doppler radar", "GPS meteorologi", "radiometer", "alat ukur radiasi matahari",
        "Theodolit", "radar","radiosonde","pibal","Penakar hujan","Panci penguapan","Pyranomete",
        "Sangkar meteorologi","intensitymeter", "akselerograf", "psychrometer", "campbell stokes",
        "automatic weather station", "digital barometer", "hygrometer standar",
        "gelas penakar hujan standar", "cup counter", "aktinograf", "jam", "UTC"
    ]
    message = message.lower()
    for keyword in keywords:
        if fuzz.partial_ratio(message, keyword) > 60:
            return True
    return False
