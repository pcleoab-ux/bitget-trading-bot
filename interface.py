"""
Interface web simples para o bot Bitget.
Rode: python interface.py
Abre em: http://localhost:5000
"""
from flask import Flask, render_template_string, jsonify, request
import threading
import time
from datetime import datetime
from bitget_client import BitgetClient
from config import *

app = Flask(__name__)
client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Bot Bitget</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="10">
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: #eee; padding: 20px; }
        .card { background: #2a2a2a; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .btn { background: #e74c3c; color: white; border: none; padding: 8px 16px; cursor: pointer; border-radius: 4px; }
        .btn:hover { background: #c0392b; }
        .btn-green { background: #27ae60; }
        .btn-green:hover { background: #1e8449; }
        table { width: 100%; border-collapse: collapse; }
        td, th { padding: 8px; text-align: left; border-bottom: 1px solid #444; }
        .green { color: #2ecc71; }
        .red { color: #e74c3c; }
    </style>
</head>
<body>
    <h1>Bot Bitget - BTCUSDT</h1>
    
    <div class="card">
        <h2>Saldo</h2>
        <p>USDT: <strong>{{ saldo_usdt }}</strong></p>
        <p>BTC: <strong>{{ saldo_btc }}</strong></p>
        <p>Preço BTC: <strong>{{ preco }}</strong></p>
    </div>

    <div class="card">
        <h2>Ordens Abertas</h2>
        {% if ordens %}
        <table>
            <tr><th>ID</th><th>Lado</th><th>Tipo</th><th>Preço</th><th>Qtd</th><th>Ação</th></tr>
            {% for o in ordens %}
            <tr>
                <td>{{ o.orderId[:8] }}...</td>
                <td class="{{ 'green' if o.side == 'buy' else 'red' }}">{{ o.side.upper() }}</td>
                <td>{{ o.orderType }}</td>
                <td>{{ o.price }}</td>
                <td>{{ o.size }}</td>
                <td><button class="btn" onclick="cancelar('{{ o.orderId }}')">Cancelar</button></td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p>Nenhuma ordem aberta</p>
        {% endif %}
    </div>

    <div class="card">
        <h2>Ações</h2>
        <button class="btn" onclick="venderTudo()">Vender todo BTC</button>
        <button class="btn btn-green" onclick="location.reload()">Atualizar</button>
    </div>

    <script>
        function cancelar(orderId) {
            if (confirm('Cancelar esta ordem?')) {
                fetch('/cancelar?id=' + orderId).then(() => location.reload());
            }
        }
        function venderTudo() {
            if (confirm('Vender todo o BTC?')) {
                fetch('/vender_tudo').then(() => location.reload());
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    saldo_usdt = 0
    saldo_btc = 0
    preco = 0
    ordens = []

    try:
        resp = client.get_account()
        if resp.get("code") == "00000":
            for asset in resp.get("data", []):
                if asset.get("coin") == "USDT":
                    saldo_usdt = float(asset.get("available", 0))
                elif asset.get("coin") == "BTC":
                    saldo_btc = float(asset.get("available", 0))

        ticker = client.get_ticker(SYMBOL)
        if ticker.get("code") == "00000":
            preco = float(ticker.get("data", [{}])[0].get("lastPr", 0))

        ordens_resp = client.request("GET", "/api/v2/spot/trade/unfilled-orders", params={"symbol": SYMBOL})
        if ordens_resp.get("code") == "00000":
            ordens = ordens_resp.get("data", [])
    except Exception as e:
        print(f"Erro: {e}")

    return render_template_string(HTML, saldo_usdt=f"{saldo_usdt:.2f}", saldo_btc=f"{saldo_btc:.6f}", preco=f"{preco:.2f}", ordens=ordens)

@app.route("/cancelar")
def cancelar():
    order_id = request.args.get("id")
    if order_id:
        client.request("POST", "/api/v2/spot/trade/cancel-order", body={"symbol": SYMBOL, "orderId": order_id})
    return jsonify({"ok": True})

@app.route("/vender_tudo")
def vender_tudo():
    try:
        resp = client.get_account()
        saldo_btc = 0
        if resp.get("code") == "00000":
            for asset in resp.get("data", []):
                if asset.get("coin") == "BTC":
                    saldo_btc = float(asset.get("available", 0))
        if saldo_btc > 0.00001:
            client.place_order(SYMBOL, "sell", round(saldo_btc * 0.998, 6))
    except:
        pass
    return jsonify({"ok": True})

if __name__ == "__main__":
    print("Abra no navegador: http://localhost:5000")
    app.run(port=5000, debug=False)
