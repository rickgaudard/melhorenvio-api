from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
import time
import threading

app = Flask(__name__)
CORS(app)  # Libera acesso de qualquer origem

TOKEN = os.getenv("MELHOR_ENVIO_TOKEN")

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {TOKEN}'
}

FRETES_FILE = "fretes.json"
COLETA_FILE = "coleta.json"
LIMPEZA_INTERVALO = 300  # 5 minutos


def limpar_arquivos():
    while True:
        time.sleep(LIMPEZA_INTERVALO)
        for file in [FRETES_FILE, COLETA_FILE]:
            if os.path.exists(file):
                with open(file, "w", encoding="utf-8") as f:
                    json.dump({}, f)
        print("🧹 Arquivos de cache limpos.")


@app.route('/calcular-frete', methods=['POST'])
def calcular_frete():
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados ausentes"}), 400

        cep_origem = dados.get("cep_origem")
        cep_destino = dados.get("cep_destino")
        peso = dados.get("peso")
        valor = dados.get("valor", 10.0)

        largura = dados.get("largura", 15)
        altura = dados.get("altura", 10)
        comprimento = dados.get("comprimento", 20)

        if not cep_origem or not cep_destino or not peso:
            return jsonify({"erro": "Dados obrigatórios ausentes"}), 400

        payload = {
            "from": {"postal_code": cep_origem},
            "to": {"postal_code": cep_destino},
            "products": [{
                "weight": peso,
                "width": largura,
                "height": altura,
                "length": comprimento,
                "insurance_value": 0
            }],
            "options": {
                "insurance_value": 0
            }
        }

        with open(COLETA_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        response = requests.post(
            "https://www.melhorenvio.com.br/api/v2/me/shipment/calculate",
            headers=HEADERS,
            data=json.dumps(payload)
        )

        if response.status_code != 200:
            return jsonify({
                "erro": "Falha na API do Melhor Envio",
                "status_code": response.status_code,
                "resposta": response.text
            }), 500

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


@app.route('/fretes.json', methods=['GET'])
def consultar_frete():
    try:
        if not os.path.exists(FRETES_FILE):
            return jsonify({"fretes": []})

        with open(FRETES_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)

        return jsonify(dados)

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


@app.route('/')
def home():
    return "API de Frete Render + Shopify Online com Cache Limpo a cada 5 minutos"


if __name__ == '__main__':
    threading.Thread(target=limpar_arquivos, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)