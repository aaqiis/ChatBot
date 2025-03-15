from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from cuaca import chat
from umum import get_response
from logger_config import logger

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return render_template('hal1.html')

@app.route('/cuaca')
def chatbot_cuaca():
    return render_template('cuaca.html')

@app.route('/umum')
def chatbot_umum():
    return render_template('umum.html')

@app.route('/get_cuaca', methods=['POST'])
def get_cuaca():
    try:
        user_input = request.form['user_input']  # Ambil input dengan kunci yang sesuai
        model = request.form.get('model', 'gemini').lower()  # Default ke 'gemini'

        if not user_input:
            return jsonify({"error": "Pesan tidak boleh kosong."}), 400

        response = chat(user_input, model=model)  # Panggil fungsi chat
        return jsonify(response)  # Respons JSON
    except Exception as e:
        return jsonify({"error": "Terjadi kesalahan pada server.", "details": str(e)}), 500


@app.route('/get_umum', methods=['POST'])
def get_umum():
    try:
        user_input = request.form['user_input']
        model = request.form.get("model", "gemini")  # Default ke Gemini jika model tidak dipilih
        
          
        if not user_input:
            return jsonify({"error": "Input kosong"}), 400
        
        logger.info(f"Model yang dipilih dari frontend: {model}")  # 🔍 Debugging

        response = get_response(user_input, model=model) 
        return jsonify({"response": response, "model": model})  # 🔹 Respons JSON yang benar
    except Exception as e:
        return {'response': 'Terjadi kesalahan pada server'},500

if __name__ == '__main__':
    app.run(debug=True)
