"""
Dashboard do Bot Bitget com controles.
Rode: python interface.py
Abra: http://localhost:5000
"""
from flask import Flask, render_template_string, jsonify, request
from bitget_client import BitgetClient
from analise import analisar_multi_timeframe, obter_tendencia_maior
from config import *
import pandas as pd

app = Flask(__name__)
client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)

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
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }
        .card h2 { margin: 0 0 12px 0; font-size: 13px; color: #8b949e; text-transform: uppercase; }
        .big { font-size: 26px; font-weight: bold; }
        .green { color: #3fb950; }
        .red { color: #f85149; }
        .blue { color: #58a6ff; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #21262d; }
        th { color: #8b949e; }
        .btn { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; padding: 10px 16px; cursor: pointer; border-radius: 6px; margin: 4px; font-size: 14px; }
        .btn:hover { background: #30363d; }
        .btn-red { background: #da3633; border-color: #da3633; color: white; }
        .btn-red:hover { background: #b62324; }
        .btn-green { background: #238636; border-color: #238636; color: white; }
        .btn-green:hover { background: #2ea043; }
        .btn-blue { background: #1f6feb; border-color: #1f6feb; color: white; }
        .btn-blue:hover { background: #388bfd; }
        .signal { font-size: 22px; font-weight: bold; padding: 12px; border-radius: 6px; text-align: center; }
        .signal-buy { background: #238636; color: white; }
        .signal-sell { background: #da3633; color: white; }
        .signal-none { background: #21262d; color: #8b949e; }
        .log { background: #0d1117; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 11px; max-height: 180px; overflow-y: auto; }
        .acoes { display: flex; flex-wrap: wrap; gap: 8px; }
    </style>
</head>
<body>
    <h1>Dashboard Bot Bitget</h1>
    <p class="subtitle">BTCUSDT Spot | Atualiza a cada 20s</p>

    <div class="grid">
        <div class="card">
            <h2>Saldo</h2>
            <p class="big">{{ saldo_usdt }} <span style="font-size:14px">USDT</span></p>
            <p>{{ saldo_btc }} BTC</p>
            <p style="color:#8b949e">Valor total: ~${{ valor_total }}</p>
        </div>
        <div class="card">
            <h2>Preço BTC</h2>
            <p class="big blue">${{ preco }}</p>
            <p>Suporte: {{ suporte }}</p>
            <p>Resistência: {{ resistencia }}</p>
        </div>
        <div class="card">
            <h2>Análise</h2>
            <p>Tendência: <strong class="{{ 'green' if tendencia == 'alta' else 'red' if tendencia == 'baixa' else '' }}">{{ tendencia.upper() }}</strong></p>
            <p>ADX: {{ adx }} | ATR: {{ atr }}%</p>
            <p>Score C: <span class="green">{{ score_c }}</span> | V: <span class="red">{{ score_v }}</span> | Mín: {{ score_min }}</p>
            <p>TFs: {{ tfs_c }} compra | {{ tfs_v }} venda</p>
        </div>
        <div class="card">
            <h2>Sinal Atual</h2>
            <div class="signal {{ 'signal-buy' if sinal == 'buy' else 'signal-sell' if sinal == 'sell' else 'signal-none' }}">
                {{ sinal.upper() if sinal else 'SEM SINAL' }}
            </div>
        </div>
    </div>

    <div class="card" style="margin-top:15px">
        <h2>Ações</h2>
        <div class="acoes">
            {% if sinal == 'buy' and saldo_usdt > 2 %}
            <button class="btn btn-green" onclick="comprar()">Comprar BTC agora</button>
            {% endif %}
            {% if saldo_btc > 0.00001 %}
            <button class="btn btn-red" onclick="venderTudo()">Vender todo BTC</button>
            {% endif %}
            <button class="btn" onclick="location.reload()">Atualizar</button>
        </div>
        <p style="color:#8b949e; font-size:12px; margin-top:10px">
            {% if sinal == 'buy' %}Sinal de compra ativo. Clique para executar.{% endif %}
            {% if sinal == 'sell' %}Sinal de venda ativo.{% endif %}
            {% if not sinal %}Aguardando sinal forte para operar.{% endif %}
        </p>
    </div>

    <div class="card" style="margin-top:15px">
        <h2>Ordens Abertas</h2>
        {% if ordens %}
        <table>
            <tr><th>ID</th><th>Lado</th><th>Tipo</th><th>Preço</th><th>Qtd</th><th></th></tr>
            {% for o in ordens %}
            <tr>
                <td>{{ o.orderId[:10] }}...</td>
                <td class="{{ 'green' if o.side == 'buy' else 'red' }}">{{ o.side.upper() }}</td>
                <td>{{ o.orderType }}</td>
                <td>{{ o.price }}</td>
                <td>{{ o.size }}</td>
                <td><button class="btn btn-red" onclick="cancelar('{{ o.orderId }}')">X</button></td>
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
        <p style="color:#8b949e; font-size:11px; margin-top:8px">Para o bot operar sozinho, rode <code>python bot.py</code> em outro terminal.</p>
    </div>

    <script>
        function cancelar(id) {
            if (confirm('Cancelar ordem?')) fetch('/cancelar?id=' + id).then(() => location.reload());
        }
        function venderTudo() {
            if (confirm('Vender todo o BTC agora?')) fetch('/vender_tudo').then(() => location.reload());
        }
        function comprar() {
            if (confirm('Comprar BTC agora com ~85% do saldo?')) fetch('/comprar').then(() => location.reload());
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
        return ["Nenhum log ainda. Rode python bot.py para o bot operar."]

@app.route("/")
def index():
    saldo_usdt = 0
    saldo_btc = 0
    preco = 0
    ordens = []
    tendencia = "neutro"
    adx = 0
    atr = 0
    score_c = 0
    score_v = 0
    score_min = 5
    sinal = None
    tfs_c = 0
    tfs_v = 0
    suporte = 0
    resistencia = 0

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
            tfs_c = resultado.get("timeframes_compra", 0)
            tfs_v = resultado.get("timeframes_venda", 0)
            suporte = resultado.get("suporte", 0)
            resistencia = resultado.get("resistencia", 0)
    except Exception as e:
        print(f"Erro: {e}")

    valor_total = saldo_usdt + (saldo_btc * preco if preco else 0)

    return render_template_string(
        HTML,
        saldo_usdt=f"{saldo_usdt:.2f}",
        saldo_btc=f"{saldo_btc:.6f}",
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
        tfs_c=tfs_c,
        tfs_v=tfs_v,
        suporte=suporte,
        resistencia=resistencia,
        log_linhas=ler_log()
    )

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

@app.route("/comprar")
def comprar():
    try:
        resp = client.get_account()
        saldo_usdt = 0
        if resp.get("code") == "00000":
            for asset in resp.get("data", []):
                if asset.get("coin") == "USDT":
                    saldo_usdt = float(asset.get("available", 0))
        valor = round(min(saldo_usdt * 0.85, saldo_usdt - 0.5), 2)
        if valor > 1.5:
            client.place_order(SYMBOL, "buy", valor)
    except:
        pass
    return jsonify({"ok": True})

if __name__ == "__main__":
    print("Dashboard: http://localhost:5000")
    app.run(port=5000, debug=False)
