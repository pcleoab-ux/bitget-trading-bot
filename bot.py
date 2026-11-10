import time
import pandas as pd
from datetime import datetime
from bitget_client import BitgetClient
from config import *

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)

def obter_candles(limit=100):
    resp = client.get_candles(SYMBOL, TIMEFRAME, limit)
    if resp.get("code") != "00000":
        log(f"Erro candles: {resp}")
        return None

    data = resp.get("data", [])
    if not data:
        return None

    # Spot candles: [ts, open, high, low, close, volume, quoteVolume]
    df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close", "volume", "quote_volume"])
    df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
    df = df.iloc[::-1].reset_index(drop=True)
    return df

def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analisar():
    df = obter_candles(MA_PERIOD + RSI_PERIOD + 10)
    if df is None or len(df) < MA_PERIOD:
        return None

    df["rsi"] = calcular_rsi(df["close"], RSI_PERIOD)
    df["ma"] = df["close"].rolling(MA_PERIOD).mean()

    ultimo = df.iloc[-1]
    rsi = ultimo["rsi"]
    preco = ultimo["close"]
    ma = ultimo["ma"]

    log(f"Preço: {preco:.2f} | RSI: {rsi:.1f} | MA: {ma:.2f}")

    if rsi < RSI_OVERSOLD and preco > ma:
        return "buy"
    elif rsi > RSI_OVERBOUGHT and preco < ma:
        return "sell"
    return None

def tem_posicao_btc():
    """Verifica se já tem BTC na carteira Spot"""
    resp = client.get_account()
    if resp.get("code") != "00000":
        return False
    for asset in resp.get("data", []):
        if asset.get("coin") == "BTC" and float(asset.get("available", 0)) > 0.0001:
            return True
    return False

def calcular_tamanho():
    if not USAR_RISCO_PERCENTUAL:
        return LOTE_FIXO

    account = client.get_account()
    if account.get("code") != "00000":
        return LOTE_FIXO

    usdt_balance = 0
    for asset in account.get("data", []):
        if asset.get("coin") == "USDT":
            usdt_balance = float(asset.get("available", 0))
            break

    if usdt_balance <= 0:
        return LOTE_FIXO

    ticker = client.get_ticker(SYMBOL)
    price = float(ticker.get("data", [{}])[0].get("lastPr", 1))
    risco_valor = usdt_balance * (RISCO_PERCENTUAL / 100)
    tamanho = risco_valor / price
    return round(max(0.0001, tamanho), 4)

def executar_ordem(side):
    size = calcular_tamanho()
    log(f"Enviando ordem {side.upper()} | Tamanho: {size} BTC")
    result = client.place_order(SYMBOL, side, size)
    if result.get("code") == "00000":
        log(f"Ordem executada com sucesso")
    else:
        log(f"Erro na ordem: {result}")

def loop():
    log("Bot Bitget iniciado | BTCUSDT Spot")
    log(f"Timeframe: {TIMEFRAME}")
    log("Pressione Ctrl+C para parar")

    try:
        while True:
            if tem_posicao_btc():
                log("Já possui BTC. Aguardando sinal de venda ou novo ciclo...")
            else:
                sinal = analisar()
                if sinal == "buy":
                    log("Sinal de COMPRA")
                    executar_ordem("buy")
                elif sinal == "sell":
                    log("Sinal de VENDA (sem posição aberta)")
                else:
                    log("Sem sinal")

            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        log("Bot parado")

if __name__ == "__main__":
    loop()
