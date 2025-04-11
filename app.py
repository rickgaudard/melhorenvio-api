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
    valor = data.get('valor', 0)

    largura = data.get('largura', DIMENSOES_PADRAO["largura"])
    altura = data.get('altura', DIMENSOES_PADRAO["altura"])
    comprimento = data.get('comprimento', DIMENSOES_PADRAO["comprimento"])

    if not all([cep_origem, cep_destino, peso]):
        return jsonify({"erro": "Dados incompletos"}), 400

    payload = [{
        "from": {"postal_code": cep_origem},
        "to": {"postal_code": cep_destino},
        "package": {
            "weight": float(peso),
            "width": int(largura),
            "height": int(altura),
            "length": int(comprimento)
        },
        "options": {
            "insurance_value": float(valor)
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
    except requests.exceptions.HTTPError as http_err:
        return jsonify({"erro": "Erro HTTP", "detalhes": str(http_err), "resposta": response.text}), 500
    except Exception as e:
        return jsonify({"erro": "Erro ao conectar com a API", "detalhes": str(e)}), 500

@app.route('/')
def home():
    return "API de Frete está online."

@app.route('/debug-token')
def debug_token():
    token = os.getenv("MELHOR_ENVIO_TOKEN")
    if token:
        return jsonify({"status": "Token carregado com sucesso", "token_inicio": token[:10] + "..."}), 200
    else:
        return jsonify({"erro": "Token não foi carregado"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)