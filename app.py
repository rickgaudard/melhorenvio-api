import requests
import random
import time
import json
from flask import Flask, request, jsonify
import threading
import os
from flask_cors import CORS
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, origins="*", methods=["GET", "POST", "OPTIONS"])

TOKEN = os.getenv("MELHOR_ENVIO_TOKEN")

HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {TOKEN}'
}

CEPS_BRASIL = [f"{random.randint(1000000, 9999999):08d}" for _ in range(100000)]
CAMINHO_ARQUIVO = "/tmp/fretes.json"

ULTIMO_FRETE = None  # fallback final em RAM

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
            print(f"[ERRO HTTP] Código {response.status_code}")
            return {"erro_http": True, "codigo": response.status_code, "resposta": response.text}

        result = response.json()

        if "data" not in result:
            print("[ERRO JSON] Resposta não contém 'data'")
            return {"erro_json": True, "resposta": result}

        opcoes = []
        for r in result["data"]:
            if r.get("error"):
                frete_info = {
                    "transportadora": r.get("name", "Desconhecida"),
                    "erro": True,
                    "motivo": r["error"]
                }
                print(f"[ERRO TRANSPORTADORA] {frete_info['transportadora']}: {frete_info['motivo']}")
            else:
                frete_info = {
                    "transportadora": r.get("name", "Desconhecida"),
                    "preco": r.get("price"),
                    "prazo_entrega": r.get("delivery_time"),
                    "error": False
                }
                print(f"[OK] {frete_info['transportadora']} - R$ {frete_info['preco']} - {frete_info['prazo_entrega']} dias")

            opcoes.append(frete_info)

        return {
            "entrada": dados,
            "fretes": opcoes
        }

    except Exception as e:
        print(f"[EXCEÇÃO] {str(e)}")
        return {"erro_exception": True, "motivo": str(e)}

def salvar_resultado(dados_resultado, arquivo=CAMINHO_ARQUIVO):
    try:
        global ULTIMO_FRETE
        dados_resultado["timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        ULTIMO_FRETE = dados_resultado

        with open(arquivo, "w", encoding="utf-8-sig") as f:
            json.dump(dados_resultado, f, ensure_ascii=False, indent=2)

        # Cópia pública adicional (caso /tmp não sirva para leitura direta)
        with open("fretes.json", "w", encoding="utf-8-sig") as fpub:
            json.dump(dados_resultado, fpub, ensure_ascii=False, indent=2)

        print(f"[✔] Salvo com sucesso em {arquivo} e copiado para fretes.json")

    except Exception as e:
        print(f"[ERRO SALVANDO JSON] {str(e)}")

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
    salvar_resultado(resultado)

    return jsonify(resultado)

@app.route('/tmp/fretes.json', methods=['GET'])
@app.route('/fretes.json', methods=['GET'])  # rota alternativa legível por Shopify
def enviar_fretes_para_shopify():
    try:
        if os.path.exists(CAMINHO_ARQUIVO):
            with open(CAMINHO_ARQUIVO, "r", encoding="utf-8-sig") as f:
                conteudo = f.read()
                print("📄 Conteúdo bruto:", conteudo)
                registro = json.loads(conteudo)

            agora = datetime.utcnow()
            timestamp = registro.get("timestamp")
            if timestamp:
                tempo = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
                if agora - tempo <= timedelta(minutes=5):
                    return jsonify({"fretes": registro.get("fretes", [])})

        # Fallback em RAM
        if ULTIMO_FRETE:
            print("🧠 Usando fallback em memória RAM.")
            return jsonify({"fretes": ULTIMO_FRETE.get("fretes", [])})

        return jsonify({"fretes": []})

    except Exception as e:
        print(f"[ERRO LEITURA JSON] {str(e)}")
        return jsonify({"erro": str(e)}), 500

@app.route('/')
def home():
    return "API de Frete com suporte à Shopify Online."

def iniciar_coletor_em_thread():
    def loop_infinito():
        while True:
            dados = gerar_dados_aleatorios()
            resultado = consultar_frete(dados)
            salvar_resultado(resultado)
            time.sleep(2)
    thread = threading.Thread(target=loop_infinito)
    thread.daemon = True
    thread.start()

if __name__ == '__main__':
    iniciar_coletor_em_thread()
    app.run(host='0.0.0.0', port=5000)