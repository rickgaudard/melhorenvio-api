from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json

app = Flask(__name__)
CORS(app)

MELHOR_ENVIO_TOKEN = os.getenv("MELHOR_ENVIO_TOKEN")

DIMENSOES_PADRAO = {"largura": 15, "altura": 10, "comprimento": 20}

@app.route('/calcular-frete', methods=['POST'])
def calcular_frete():
    data = request.json
    cep_origem = data.get('cep_origem')
    cep_destino = data.get('cep_destino')
    peso = data.get('peso')
    valor = data.get('valor')

    largura = data.get('largura', DIMENSOES_PADRAO["largura"])
    altura = data.get('altura', DIMENSOES_PADRAO["altura"])
    comprimento = data.get('comprimento', DIMENSOES_PADRAO["comprimento"])

    if not cep_origem or not cep_destino or not peso or not valor:
        return jsonify({"erro": "Dados incompletos"}), 400

    payload = [{
        "from": {"postal_code": cep_origem},
        "to": {"postal_code": cep_destino},
        "products": [{
            "weight": float(peso),
            "width": int(largura),
            "height": int(altura),
            "length": int(comprimento),
            "insurance_value": float(valor)
        }]
    }]

    headers = {
        "Authorization": f"Bearer {MELHOR_ENVIO_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(
            "https://www.melhorenvio.com.br/api/v2/me/shipment/calculate",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        dados_frete = response.json()

        fretes_formatados = []
        for frete in dados_frete:
            if 'error' in frete:
                continue
            fretes_formatados.append({
                "nome": frete["name"],
                "valor": frete["price"],
                "prazo": frete["delivery_time"],
                "transportadora": frete["company"]["name"]
            })

        with open("fretes.json", "w", encoding="utf-8") as f:
            json.dump(fretes_formatados, f, ensure_ascii=False)

        return jsonify({"status": "OK"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route('/consultar-frete', methods=['GET'])
def consultar_frete():
    try:
        with open("fretes.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
        return jsonify({"fretes": dados})
    except FileNotFoundError:
        return jsonify({"erro": "Nenhum frete consultado ainda."}), 404