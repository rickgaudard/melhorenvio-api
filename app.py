from flask import Flask, request, jsonify
import requests, json, os

app = Flask(__name__)

TOKEN = os.getenv("MELHOR_ENVIO_TOKEN")

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {TOKEN}'
}

@app.route("/calcular-frete", methods=["POST"])
def calcular_frete():
    try:
        dados = request.json

        response = requests.post(
            "https://www.melhorenvio.com.br/api/v2/me/shipment/calculate",
            headers=HEADERS,
            data=json.dumps(dados)
        )

        if response.status_code != 200:
            return jsonify({"erro_http": True, "codigo": response.status_code, "resposta": response.text}), 500

        resultado = response.json()

        if "data" not in resultado:
            return jsonify({"erro_json": True, "resposta": resultado}), 500

        # Gravar resultado em um "cache"
        with open("fretes.json", "w", encoding="utf-8") as f:
            json.dump(resultado["data"], f, ensure_ascii=False, indent=2)

        return jsonify({"fretes": resultado["data"]})

    except Exception as e:
        return jsonify({"erro_exception": True, "motivo": str(e)}), 500

@app.route("/consultar-frete", methods=["GET"])
def consultar_cache():
    try:
        with open("fretes.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        os.remove("fretes.json")  # Apaga o cache logo após retorno
        return jsonify({"fretes": data})
    except:
        return jsonify({"fretes": []})

@app.route("/")
def home():
    return "API de Frete - Shopify + Melhor Envio"

if __name__ == '__main__':
    app.run()