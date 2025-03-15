import logging

# Konfigurasi logger global
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Buat logger utama yang bisa dipakai di semua file
logger = logging.getLogger("chatbot_bmkg")
