from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Permite CORS para Shopify

MELHOR_ENVIO_TOKEN = os.getenv("MELHOR_ENVIO_TOKEN")

@app.route('/')
def home():
    return "API de Frete Online"

@app.route('/calcular-frete', methods=['POST'])
def calcular_frete():
    try:
        dados = request.json
        if not all(k in dados for k in ['cep_origem', 'cep_destino', 'peso', 'valor']):
            return jsonify({"erro": "Dados incompletos"}), 400

        payload = [{
            "from": {"postal_code": dados['cep_origem']},
            "to": {"postal_code": dados['cep_destino']},
            "package": {
                "weight": dados['peso'],
                "width": dados.get('largura', 15),
                "height": dados.get('altura', 10),
                "length": dados.get('comprimento', 20)
            },
            "options": {
                "insurance_value": dados['valor']
            },
            "services": []
        }]

        headers = {
            "Authorization": f"Bearer {MELHOR_ENVIO_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.post(
            "https://www.melhorenvio.com.br/api/v2/me/shipment/calculate",
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            return jsonify({"erro": "Erro na API", "status": response.status_code}), 500

        resultado = response.json()

        fretes = []
        for item in resultado.get('data', []):
            if item.get("error"):
                continue
            fretes.append({
                "nome": item["name"],
                "valor": item["price"],
                "prazo": item["delivery_time"]
            })

        # Armazena como se fosse arquivo local (temporário)
        with open("fretes.json", "w", encoding="utf-8") as f:
            json.dump({"fretes": fretes}, f, ensure_ascii=False, indent=2)

        return jsonify({"fretes": fretes})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/consultar-frete', methods=['GET'])
def consultar_frete():
    try:
        with open("fretes.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
        return jsonify(dados)
    except:
        return jsonify({"fretes": []})

if __name__ == '__main__':
    app.run()