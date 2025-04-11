import requests
import random
import time
import json
from flask import Flask, request, jsonify
import threading
import os

app = Flask(__name__)

TOKEN = os.getenv("MELHOR_ENVIO_TOKEN")  # Recomendado usar variável de ambiente

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {TOKEN}'
}

CEPS_BRASIL = [f"{random.randint(1000000, 9999999):08d}" for _ in range(100000)]

def gerar_dados_aleatorios():
    return {
        "from": {
            "postal_code": random.choice(CEPS_BRASIL)
        },
        "to": {
            "postal_code": random.choice(CEPS_BRASIL)
        },
        "products": [
            {
                "weight": round(random.uniform(0.1, 30.0), 2),
                "width": round(random.uniform(11, 70), 2),
                "height": round(random.uniform(2, 60), 2),
                "length": round(random.uniform(16, 100), 2),
                "insurance_value": round(random.uniform(10, 2000), 2)
            }
        ]
    }

def consultar_frete(dados):
    try:
        response = requests.post(
            "https://www.melhorenvio.com.br/api/v2/me/shipment/calculate",
            headers=HEADERS,
            data=json.dumps(dados)
        )
        if response.status_code != 200:
            return {"erro_http": True, "codigo": response.status_code, "resposta": response.text}

        result = response.json()
        if "data" not in result:
            return {"erro_json": True, "resposta": result}

        opcoes = []
        for r in result["data"]:
            if r.get("error"):
                opcoes.append({
                    "transportadora": r.get("name", "Desconhecida"),
                    "erro": True,
                    "motivo": r["error"]
                })
            else:
                opcoes.append({
                    "transportadora": r.get("name", "Desconhecida"),
                    "preco": r.get("price"),
                    "prazo_entrega": r.get("delivery_time"),
                    "error": False
                })

        return {
            "entrada": dados,
            "fretes": opcoes
        }

    except Exception as e:
        return {"erro_exception": True, "motivo": str(e)}

def salvar_resultado(dados_resultado, arquivo="fretes.json"):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados_resultado, f, ensure_ascii=False, indent=2)

@app.route('/calcular-frete', methods=['POST'])
def calcular_frete():
    dados = request.json

    cep_origem = dados.get("cep_origem", random.choice(CEPS_BRASIL))
    cep_destino = dados.get("cep_destino", random.choice(CEPS_BRASIL))
    peso = dados.get("peso", round(random.uniform(0.1, 30.0), 2))
    largura = dados.get("largura", round(random.uniform(11, 70), 2))
    altura = dados.get("altura", round(random.uniform(2, 60), 2))
    comprimento = dados.get("comprimento", round(random.uniform(16, 100), 2))
    valor = dados.get("valor", round(random.uniform(10, 2000), 2))

    payload = {
        "from": {"postal_code": cep_origem},
        "to": {"postal_code": cep_destino},
        "products": [{
            "weight": peso,
            "width": largura,
            "height": altura,
            "length": comprimento,
            "insurance_value": valor
        }]
    }

    resultado = consultar_frete(payload)
    salvar_resultado(resultado, "fretes.json")

    # Limpa o arquivo após 5 segundos
    threading.Timer(5, lambda: open("fretes.json", "w").write("{}")).start()

    return jsonify(resultado)

@app.route('/')
def home():
    return "API de Frete com coleta automática e suporte à Shopify"

def iniciar_coletor_em_thread():
    def loop_infinito():
        while True:
            dados = gerar_dados_aleatorios()
            resultado = consultar_frete(dados)
            salvar_resultado(resultado, "fretes_coletados.json")
            time.sleep(10)
    thread = threading.Thread(target=loop_infinito)
    thread.daemon = True
    thread.start()

def limpar_coletados_periodicamente():
    def loop_limpeza():
        while True:
            time.sleep(300)  # 5 minutos
            open("fretes_coletados.json", "w").write("{}")
    thread = threading.Thread(target=loop_limpeza)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    iniciar_coletor_em_thread()
    limpar_coletados_periodicamente()
    app.run(host='0.0.0.0', port=5000)