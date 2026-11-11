"""
Dashboard do Bot Bitget com controles e bot automático.
Rode: python interface.py
Abra: http://localhost:5000
"""
from flask import Flask, render_template_string, jsonify, request
from bitget_client import BitgetClient
from analise import analisar_multi_timeframe, obter_tendencia_maior
from config import *
import pandas as pd
import subprocess
import os
import signal

app = Flask(__name__)
client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)

# Processo do bot
bot_process = None

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard Bot Bitget</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="20">
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #0d1117; color: #c9d1d9; margin: 0; padding: 20px; }
        h1 { color: #58a6ff; margin-bottom: 5px; }
        .subtitle { color: #8b949e; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 15px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
        .card h2 { margin: 0 0 12px 0; font-size: 13px; color: #8b949e; text-transform: uppercase; }
        .big { font-size: 24px; font-weight: bold; }
        .green { color: #3fb950; }
        .red { color: #f85149; }
        .blue { color: #58a6ff; }
        .yellow { color: #d29922; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #21262d; }
        th { color: #8b949e; }
        .btn { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 10px 14px; cursor: pointer; border-radius: 6px; margin: 4px; font-size: 13px; }
        .btn:hover { background: #30363d; }
        .btn-red { background: #da3633; border-color: #da3633; color: white; }
        .btn-red:hover { background: #b62324; }
        .btn-green { background: #238636; border-color: #238636; color: white; }
        .btn-green:hover { background: #2ea043; }
        .btn-blue { background: #1f6feb; border-color: #1f6feb; color: white; }
        .btn-blue:hover { background: #388bfd; }
        .signal { font-size: 20px; font-weight: bold; padding: 10px; border-radius: 6px; text-align: center; }
        .signal-buy { background: #238636; color: white; }
        .signal-sell { background: #da3633; color: white; }
        .signal-none { background: #21262d; color: #8b949e; }
        .status { padding: 8px 12px; border-radius: 6px; display: inline-block; font-weight: bold; }
        .status-on { background: #238636; color: white; }
        .status-off { background: #484f58; color: #c9d1d9; }
        .log { background: #0d1117; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 11px; max-height: 180px; overflow-y: auto; }
        .acoes { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
    </style>
</head>
<body>
    <h1>Dashboard Bot Bitget</h1>
    <p class="subtitle">BTCUSDT Spot</p>

    <div class="grid">
        <div class="card">
            <h2>Saldo</h2>
            <p class="big">{{ saldo_usdt }} <span style="font-size:14px">USDT</span></p>
            <p>{{ saldo_btc }} BTC</p>
            <p style="color:#8b949e">Total: ~${{ valor_total }}</p>
        </div>
        <div class="card">
            <h2>Preço</h2>
            <p class="big blue">${{ preco }}</p>
            <p>Sup: {{ suporte }}</p>
            <p>Res: {{ resistencia }}</p>
        </div>
        <div class="card">
            <h2>Análise</h2>
            <p>Tendência: <strong class="{{ 'green' if tendencia == 'alta' else 'red' if tendencia == 'baixa' else '' }}">{{ tendencia.upper() }}</strong></p>
            <p>ADX: {{ adx }} | ATR: {{ atr }}%</p>
            <p>Score: <span class="green">{{ score_c }}</span> / <span class="red">{{ score_v }}</span></p>
        </div>
        <div class="card">
            <h2>Sinal</h2>
            <div class="signal {{ 'signal-buy' if sinal == 'buy' else 'signal-sell' if sinal == 'sell' else 'signal-none' }}">
                {{ sinal.upper() if sinal else 'SEM SINAL' }}
            </div>
        </div>
    </div>

    <div class="card" style="margin-top:15px">
        <h2>Bot Automático</h2>
        <div class="acoes">
            <span class="status {{ 'status-on' if bot_rodando else 'status-off' }}">
                {{ 'RODANDO' if bot_rodando else 'PARADO' }}
            </span>
            {% if not bot_rodando %}
            <button class="btn btn-green" onclick="iniciarBot()">Iniciar Bot</button>
            {% else %}
            <button class="btn btn-red" onclick="pararBot()">Parar Bot</button>
            {% endif %}
        </div>
        <p style="color:#8b949e; font-size:12px; margin-top:8px">
            O bot compra e vende sozinho conforme a análise.
        </p>
    </div>

    <div class="card" style="margin-top:15px">
        <h2>Controles Manuais</h2>
        <div class="acoes">
            <button class="btn btn-green" onclick="comprarManual()">Comprar BTC</button>
            <button class="btn btn-red" onclick="venderTudo()">Vender todo BTC</button>
            <button class="btn" onclick="location.reload()">Atualizar</button>
        </div>
    </div>

    <div class="card" style="margin-top:15px">
        <h2>Ordens Abertas</h2>
        {% if ordens %}
        <table>
            <tr><th>ID</th><th>Lado</th><th>Tipo</th><th>Preço</th><th>Qtd</th><th></th></tr>
            {% for o in ordens %}
            <tr>
                <td>{{ o.orderId[:8] }}...</td>
                <td class="{{ 'green' if o.side == 'buy' else 'red' }}">{{ o.side.upper() }}</td>
                <td>{{ o.orderType }}</td>
                <td>{{ o.price }}</td>
                <td>{{ o.size }}</td>
                <td><button class="btn btn-red" onclick="cancelar('{{ o.orderId }}')">Cancelar</button></td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p>Nenhuma ordem aberta</p>
        {% endif %}
    </div>

    <div class="card" style="margin-top:15px">
        <h2>Log do Bot</h2>
        <div class="log">
            {% for linha in log_linhas %}
            {{ linha }}<br>
            {% endfor %}
        </div>
    </div>

    <script>
        function cancelar(id) {
            if (confirm('Cancelar?')) fetch('/cancelar?id=' + id).then(() => location.reload());
        }
        function venderTudo() {
            if (confirm('Vender todo o BTC?')) {
                fetch('/vender_tudo').then(r => r.json()).then(d => {
                    alert(d.msg);
                    location.reload();
                });
            }
        }
        function comprarManual() {
            if (confirm('Comprar BTC com 85% do USDT?')) {
                fetch('/comprar').then(r => r.json()).then(d => {
                    alert(d.msg);
                    location.reload();
                });
            }
        }
        function iniciarBot() {
            if (confirm('Iniciar o bot automático?')) {
                fetch('/iniciar_bot').then(r => r.json()).then(d => {
                    alert(d.msg);
                    location.reload();
                });
            }
        }
        function pararBot() {
            if (confirm('Parar o bot?')) {
                fetch('/parar_bot').then(r => r.json()).then(d => {
                    alert(d.msg);
                    location.reload();
                });
            }
        }
    </script>
</body>
</html>
"""

def obter_candles(timeframe, limit=100):
    try:
        resp = client.get_candles(SYMBOL, timeframe, limit)
        if resp.get("code") != "00000":
            return None
        data = resp.get("data", [])
        if not data:
            return None
        df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close", "volume", "quote_volume", "extra"])
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        return df.iloc[::-1].reset_index(drop=True)
    except:
        return None

def ler_log():
    try:
        with open(LOG_ARQUIVO, "r", encoding="utf-8") as f:
            linhas = f.readlines()
        return [l.strip() for l in linhas[-12:]]
    except:
        return ["Nenhum log."]

def get_saldos():
    usdt = 0.0
    btc = 0.0
    try:
        resp = client.get_account()
        if resp.get("code") == "00000":
            for asset in resp.get("data", []):
                coin = asset.get("coin", "")
                available = float(asset.get("available", 0))
                if coin == "USDT":
                    usdt = available
                elif coin == "BTC":
                    btc = available
    except:
        pass
    return usdt, btc

def bot_esta_rodando():
    global bot_process
    if bot_process is None:
        return False
    return bot_process.poll() is None

@app.route("/")
def index():
    saldo_usdt, saldo_btc = get_saldos()
    preco = 0.0
    ordens = []
    tendencia = "neutro"
    adx = 0
    atr = 0
    score_c = 0
    score_v = 0
    score_min = 5
    sinal = None
    suporte = 0
    resistencia = 0

    try:
        ticker = client.get_ticker(SYMBOL)
        if ticker.get("code") == "00000":
            preco = float(ticker.get("data", [{}])[0].get("lastPr", 0))

        ordens_resp = client.request("GET", "/api/v2/spot/trade/unfilled-orders", params={"symbol": SYMBOL})
        if ordens_resp.get("code") == "00000":
            ordens = ordens_resp.get("data", [])

        dados = {}
        for tf in TIMEFRAMES:
            df = obter_candles(tf)
            if df is not None:
                dados[tf] = df

        df_4h = obter_candles("4h", 100)
        df_1d = obter_candles("1day", 100)
        tendencia = obter_tendencia_maior(df_4h, df_1d)

        if len(dados) >= 2:
            resultado = analisar_multi_timeframe(dados, tendencia)
            adx = resultado.get("adx", 0)
            atr = resultado.get("atr_pct", 0)
            score_c = resultado.get("score_compra", 0)
            score_v = resultado.get("score_venda", 0)
            score_min = resultado.get("score_minimo", 5)
            sinal = resultado.get("sinal")
            suporte = resultado.get("suporte", 0)
            resistencia = resultado.get("resistencia", 0)
    except Exception as e:
        print(f"Erro: {e}")

    valor_total = saldo_usdt + (saldo_btc * preco if preco else 0)

    return render_template_string(
        HTML,
        saldo_usdt=f"{saldo_usdt:.2f}",
        saldo_btc=f"{saldo_btc:.8f}",
        preco=f"{preco:,.2f}",
        valor_total=f"{valor_total:.2f}",
        ordens=ordens,
        tendencia=tendencia,
        adx=adx,
        atr=atr,
        score_c=score_c,
        score_v=score_v,
        score_min=score_min,
        sinal=sinal,
        suporte=suporte,
        resistencia=resistencia,
        log_linhas=ler_log(),
        bot_rodando=bot_esta_rodando()
    )

@app.route("/iniciar_bot")
def iniciar_bot():
    global bot_process
    if bot_esta_rodando():
        return jsonify({"ok": False, "msg": "Bot já está rodando"})
    try:
        bot_process = subprocess.Popen(
            ["python", "bot.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0
        )
        return jsonify({"ok": True, "msg": "Bot iniciado"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})

@app.route("/parar_bot")
def parar_bot():
    global bot_process
    if not bot_esta_rodando():
        return jsonify({"ok": False, "msg": "Bot não está rodando"})
    try:
        if os.name == "nt":
            bot_process.terminate()
        else:
            bot_process.send_signal(signal.SIGTERM)
        bot_process = None
        return jsonify({"ok": True, "msg": "Bot parado"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})

@app.route("/cancelar")
def cancelar():
    order_id = request.args.get("id")
    if order_id:
        client.request("POST", "/api/v2/spot/trade/cancel-order", body={"symbol": SYMBOL, "orderId": order_id})
    return jsonify({"ok": True, "msg": "Cancelado"})

@app.route("/vender_tudo")
def vender_tudo():
    try:
        _, saldo_btc = get_saldos()
        if saldo_btc >= 0.0001:
            tamanho = round(saldo_btc * 0.995, 6)
            r = client.place_order(SYMBOL, "sell", tamanho)
            if r.get("code") == "00000":
                return jsonify({"ok": True, "msg": f"Vendeu {tamanho} BTC"})
            else:
                return jsonify({"ok": False, "msg": r.get("msg", "Erro")})
        elif saldo_btc > 0:
            return jsonify({"ok": False, "msg": f"BTC muito baixo ({saldo_btc:.8f})"})
        return jsonify({"ok": False, "msg": "Sem BTC"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})

@app.route("/comprar")
def comprar():
    try:
        saldo_usdt, _ = get_saldos()
        valor = round(min(saldo_usdt * 0.85, saldo_usdt - 0.5), 2)
        if valor > 1.0:
            r = client.place_order(SYMBOL, "buy", valor)
            if r.get("code") == "00000":
                return jsonify({"ok": True, "msg": f"Comprou {valor} USDT"})
            else:
                return jsonify({"ok": False, "msg": r.get("msg", "Erro")})
        return jsonify({"ok": False, "msg": "USDT insuficiente"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})

if __name__ == "__main__":
    print("Dashboard: http://localhost:5000")
    app.run(port=5000, debug=False)
