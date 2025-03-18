# import os
# from dotenv import load_dotenv

# load_dotenv()

# BMKG_API_ENDPOINT = os.getenv("BMKG_API_ENDPOINT")
# OLLAMA_MODEL = "deepseek-r1:1.5b"

#GEMINI
# import os

# GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
# BMKG_API_ENDPOINT = os.environ["BMKG_API_ENDPOINT"]

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load variabel dari .env
load_dotenv()


# Ambil API key dari environment atau .env, gunakan None jika tidak ada
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BMKG_API_ENDPOINT = os.getenv("BMKG_API_ENDPOINT")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GPT_API_KEY = os.getenv("GPT_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY tidak ditemukan! Pastikan sudah diatur di .env")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

