import requests

url = "https://chatgpt-42.p.rapidapi.com/gpt4"

user_input = input("Masukkan pertanyaan:")

payload = {

	"messages": [
		{
			"role": "user",
			"content": user_input
		}
	],
	"web_access": False
}

headers = {
	"x-rapidapi-key": "2e870da41fmsh47869402f1872a4p1c12dejsncd2e0cb83cf8",
	"x-rapidapi-host": "chatgpt-42.p.rapidapi.com",
	"Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(response.json())