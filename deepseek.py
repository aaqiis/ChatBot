import requests

api = open("D:\ChatBot\API_deepseek.txt").read()
URL = "https://openrouter.ai/api/v1/chat/completions"



headers = {
    "Authorization": f"Bearer {api}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://localhost"


}

#  Meminta input dari pengguna
user_input = "apa itu cuaca"

data = {
    "model": "deepseek/deepseek-r1:free",
    "messages": [{"role": "user", "content": user_input}]
}

response = requests.post(URL, headers=headers, json=data)

if response.status_code == 200:
    response_data = response.json()
    print("\nCHAT:\n", response_data["choices"][0]["message"]["content"])
else:
    print("Error", response.status_code, "-",response.text)