import time
import pandas as pd
from datetime import datetime
from bitget_client import BitgetClient
from analise import analisar_multi_timeframe
from config import *

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)

# Controle de posição para Stop Loss
posicao_aberta = None  # {"preco_entrada": float, "tamanho": float}

def obter_candles(timeframe, limit=100):
    resp = client.get_candles(SYMBOL, timeframe, limit)
    if resp.get("code") != "00000":
        return None
    data = resp.get("data", [])
    if not data:
        return None
    df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close", "volume", "quote_volume"])
    df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
    return df.iloc[::-1].reset_index(drop=True)

def obter_preco_atual():
    resp = client.get_ticker(SYMBOL)
    if resp.get("code") != "00000":
        return None
    return float(resp.get("data", [{}])[0].get("lastPr", 0))

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
    usdt = 0
    for asset in account.get("data", []):
        if asset.get("coin") == "USDT":
            usdt = float(asset.get("available", 0))
            break
    if usdt <= 0:
        return LOTE_FIXO
    preco = obter_preco_atual() or 1
    return round(max(0.0001, (usdt * RISCO_PERCENTUAL / 100) / preco), 4)

def executar_ordem(side, tamanho=None):
    size = tamanho or calcular_tamanho()
    log(f"Ordem {side.upper()} | {size} BTC")
    result = client.place_order(SYMBOL, side, size)
    return result.get("code") == "00000"

def verificar_stop_loss(preco_atual):
    global posicao_aberta
    if not posicao_aberta:
        return

    entrada = posicao_aberta["preco_entrada"]
    variacao = (preco_atual - entrada) / entrada * 100

    if variacao <= -STOP_LOSS_PERCENT:
        log(f"STOP LOSS atingido ({variacao:.2f}%)")
        if executar_ordem("sell", posicao_aberta["tamanho"]):
            posicao_aberta = None
            log("Posição fechada por Stop Loss")
    elif variacao >= TAKE_PROFIT_PERCENT:
        log(f"TAKE PROFIT atingido ({variacao:.2f}%)")
        if executar_ordem("sell", posicao_aberta["tamanho"]):
            posicao_aberta = None
            log("Posição fechada por Take Profit")

def mostrar_analise(resultado):
    log("=" * 55)
    log(f"Preço: {resultado['preco']:.2f}")
    log(f"Suporte: {resultado['suporte']} | Resistência: {resultado['resistencia']}")
    log(f"Score Compra: {resultado['score_compra']} | Score Venda: {resultado['score_venda']}")
    log(f"Timeframes a favor: Compra {resultado['timeframes_compra']} | Venda {resultado['timeframes_venda']}")

    for tf, det in resultado["detalhes"].items():
        log(f"  [{tf}] Compra:{det['score_compra']} Venda:{det['score_venda']} | {', '.join(det['motivos'][:2])}")

    if resultado["sinal"]:
        log(f">>> SINAL: {resultado['sinal'].upper()}")
    else:
        log(">>> Sem sinal forte (precisa de múltiplos timeframes)")
    log("=" * 55)

def loop():
    global posicao_aberta
    log("Bot Bitget | BTCUSDT Spot | Multi-Timeframe + Stop Loss")
    log(f"Timeframes: {', '.join(TIMEFRAMES)}")
    log(f"Stop Loss: {STOP_LOSS_PERCENT}% | Take Profit: {TAKE_PROFIT_PERCENT}%")

    try:
        while True:
            # Baixa candles de todos os timeframes
            dados = {}
            for tf in TIMEFRAMES:
                df = obter_candles(tf)
                if df is not None:
                    dados[tf] = df

            if len(dados) < 2:
                log("Dados insuficientes")
                time.sleep(INTERVALO_SEGUNDOS)
                continue

            resultado = analisar_multi_timeframe(dados)
            mostrar_analise(resultado)

            preco_atual = obter_preco_atual()
            if preco_atual and posicao_aberta:
                verificar_stop_loss(preco_atual)

            # Entrada
            if resultado["sinal"] == "buy" and not tem_posicao_btc() and not posicao_aberta:
                tamanho = calcular_tamanho()
                if executar_ordem("buy", tamanho):
                    posicao_aberta = {"preco_entrada": preco_atual, "tamanho": tamanho}
                    log(f"Posição aberta em {preco_atual}")

            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        log("Bot parado")

if __name__ == "__main__":
    loop()
