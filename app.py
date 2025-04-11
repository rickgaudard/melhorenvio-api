from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import json

app = Flask(__name__)
CORS(app)

MELHOR_ENVIO_TOKEN = os.getenv("MELHOR_ENVIO_TOKEN")

@app.route('/')
def index():
    return "🟢 API Melhor Envio está ativa."

@app.route('/calcular-frete', methods=['POST'])
def calcular_frete():
    try:
        data = request.get_json()

        cep_origem = data['cep_origem']
        cep_destino = data['cep_destino']
        peso = data['peso']
        valor = data['valor']
        largura = data.get('largura', 15)
        altura = data.get('altura', 10)
        comprimento = data.get('comprimento', 20)

        payload = [{
            "from": {"postal_code": cep_origem},
            "to": {"postal_code": cep_destino},
            "package": {
                "weight": peso,
                "width": largura,
                "height": altura,
                "length": comprimento
            },
            "options": {
                "insurance_value": valor
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
            return jsonify({"erro": "Erro ao consultar frete"}), 500

        resultado = response.json()
        fretes = []

        for item in resultado.get("data", []):
            if item.get("error"):
                continue
            fretes.append({
                "nome": item["name"],
                "valor": item["price"],
                "prazo": item["delivery_time"]
            })

        with open("fretes.json", "w", encoding="utf-8") as f:
            json.dump({"fretes": fretes}, f, ensure_ascii=False)

        return jsonify({"status": "ok"})

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/consultar-frete', methods=['GET'])
def consultar_frete():
    try:
        with open("fretes.json", "r", encoding="utf-8") as f:
            conteudo = json.load(f)
        os.remove("fretes.json")
        return jsonify(conteudo)
    except FileNotFoundError:
        return jsonify({"fretes": []})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    app.run()