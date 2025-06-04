from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        data = request.get_json()
        citta = data.get('citta')
        giorni = data.get('giorni')
        prompt = f"Crea un itinerario turistico di {giorni} giorni a {citta}, solo in lingua italiana."

        try:
            #res = requests.post('http://localhost:11434/api/generate', json={
            res = requests.post('http://ollama:11434/api/generate', json={
                "model": "gemma3:1b",
                "prompt": prompt,
                "stream": False
            }, timeout=600)
            risposta = res.json().get('response', 'Nessuna risposta ricevuta.')
        except Exception as e:
            risposta = f"Errore: {str(e)}"

        return jsonify({"risposta": risposta})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)