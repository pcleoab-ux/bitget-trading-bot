import time
import pandas as pd
from datetime import datetime
from bitget_client import BitgetClient
from analise import analisar_completo
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
    df = df.iloc[::-1].reset_index(drop=True)
    return df

def tem_posicao_btc():
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
        log("Ordem executada com sucesso")
    else:
        log(f"Erro na ordem: {result}")

def mostrar_analise(resultado):
    log("=" * 50)
    log(f"Preço: {resultado['preco']:.2f}")
    log(f"RSI: {resultado['rsi']} | EMA12: {resultado['ema12']} | EMA26: {resultado['ema26']}")
    log(f"Score Compra: {resultado['score_compra']} | Score Venda: {resultado['score_venda']}")

    if resultado["motivos_compra"]:
        log("Motivos Compra:")
        for m in resultado["motivos_compra"]:
            log(f"  + {m}")
    if resultado["motivos_venda"]:
        log("Motivos Venda:")
        for m in resultado["motivos_venda"]:
            log(f"  - {m}")

    if resultado["sinal"]:
        log(f">>> SINAL: {resultado['sinal'].upper()}")
    else:
        log(">>> Sem sinal forte")
    log("=" * 50)

def loop():
    log("Bot Bitget iniciado | BTCUSDT Spot | Análise Completa")
    log(f"Timeframe: {TIMEFRAME}")
    log("Indicadores: RSI + EMA + MACD + Bollinger + Volume")
    log("Pressione Ctrl+C para parar")

    try:
        while True:
            df = obter_candles(100)
            if df is None:
                time.sleep(INTERVALO_SEGUNDOS)
                continue

            resultado = analisar_completo(df)
            mostrar_analise(resultado)

            if resultado["sinal"] == "buy" and not tem_posicao_btc():
                log("Executando COMPRA")
                executar_ordem("buy")
            elif resultado["sinal"] == "sell" and tem_posicao_btc():
                log("Executando VENDA")
                executar_ordem("sell")

            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        log("Bot parado")

if __name__ == "__main__":
    loop()
