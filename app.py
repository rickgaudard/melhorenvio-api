from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
import time

app = Flask(__name__)
CORS(app)  # Libera acesso de qualquer origem, inclusive Shopify

TOKEN = os.getenv("MELHOR_ENVIO_TOKEN")

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {TOKEN}'
}

FRETES_FILE = "fretes.json"

@app.route('/calcular-frete', methods=['POST'])
def calcular_frete():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Dados ausentes"}), 400

        response = requests.post(
            "https://www.melhorenvio.com.br/api/v2/me/shipment/calculate",
            headers=HEADERS,
            data=json.dumps(dados)
        )

        if response.status_code != 200:
            return jsonify({"erro": "Falha na API do Melhor Envio", "status_code": response.status_code}), 500

        resultado = response.json()

        if "data" not in resultado:
            return jsonify({"erro": "Resposta inválida da API"}), 500

        fretes = []
        for r in resultado["data"]:
            if r.get("error"):
                continue
            fretes.append({
                "nome": r.get("name"),
                "valor": r.get("price"),
                "prazo": r.get("delivery_time"),
                "empresa": r.get("company", {}).get("name")
            })

        with open(FRETES_FILE, "w", encoding="utf-8") as f:
            json.dump({"fretes": fretes}, f, ensure_ascii=False, indent=2)

        return jsonify({"fretes": fretes})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route('/consultar-frete', methods=['GET'])
def consultar_frete():
    try:
        if not os.path.exists(FRETES_FILE):
            return jsonify({"fretes": []})

        with open(FRETES_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)

        # Limpa o arquivo após envio
        with open(FRETES_FILE, "w", encoding="utf-8") as f:
            json.dump({"fretes": []}, f)

        return jsonify(dados)

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route('/')
def home():
    return "API de Frete Render + Shopify Online"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)