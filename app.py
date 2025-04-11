from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

MELHOR_ENVIO_TOKEN = os.getenv("MELHOR_ENVIO_TOKEN")

DIMENSOES_PADRAO = {
    "largura": 15,
    "altura": 10,
    "comprimento": 20
}

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

    if not cep_origem or not cep_destino or not peso:
        return jsonify({"erro": "Dados incompletos"}), 400

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

    try:
        response = requests.post(
            "https://www.melhorenvio.com.br/api/v2/me/shipment/calculate",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/')
def home():
    return "API de Frete está online."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
