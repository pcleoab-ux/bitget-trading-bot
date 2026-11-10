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

    df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close", "volume", "quote_volume"])
    df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
    df = df.iloc[::-1].reset_index(drop=True)  # mais antigo primeiro
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

    if rsi < RSI_OVERSOLD and preco > ma:
        return "buy"
    elif rsi > RSI_OVERBOUGHT and preco < ma:
        return "sell"
    return None

def posicoes_abertas():
    resp = client.get_positions(PRODUCT_TYPE)
    if resp.get("code") != "00000":
        return []
    positions = resp.get("data", [])
    return [p for p in positions if p.get("symbol") == SYMBOL and float(p.get("total", 0)) > 0]

def calcular_tamanho():
    if not USAR_RISCO_PERCENTUAL:
        return LOTE_FIXO

    account = client.get_account(SYMBOL, PRODUCT_TYPE)
    if account.get("code") != "00000":
        return LOTE_FIXO

    # simplificado - ajuste conforme resposta real da API
    balance = float(account.get("data", {}).get("available", 0))
    if balance <= 0:
        return LOTE_FIXO

    # cálculo básico de tamanho
    ticker = client.get_ticker(SYMBOL)
    price = float(ticker.get("data", [{}])[0].get("lastPr", 1))
    risco_valor = balance * (RISCO_PERCENTUAL / 100)
    tamanho = (risco_valor * LEVERAGE) / price
    return round(max(0.001, tamanho), 3)

def executar_ordem(side):
    size = calcular_tamanho()
    log(f"Enviando ordem {side.upper()} | Tamanho: {size}")
    result = client.place_order(SYMBOL, side, size, product_type=PRODUCT_TYPE)
    if result.get("code") == "00000":
        log(f"Ordem executada: {result}")
    else:
        log(f"Erro na ordem: {result}")

def loop():
    log("Bot Bitget iniciado")
    log(f"Símbolo: {SYMBOL} | Timeframe: {TIMEFRAME}")
    log("Pressione Ctrl+C para parar")

    try:
        while True:
            if len(posicoes_abertas()) >= MAX_POSICOES:
                log("Posição já aberta. Aguardando...")
            else:
                sinal = analisar()
                if sinal:
                    log(f"Sinal: {sinal.upper()}")
                    executar_ordem(sinal)
                else:
                    log("Sem sinal")

            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        log("Bot parado")

if __name__ == "__main__":
    loop()
