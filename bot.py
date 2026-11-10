import time
import pandas as pd
from datetime import datetime
from bitget_client import BitgetClient
from analise import analisar_multi_timeframe
from risco import *
from config import *

def log(msg):
    linha = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(linha)
    with open(LOG_ARQUIVO, "a", encoding="utf-8") as f:
        f.write(linha + "\n")

client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)
estado = carregar_estado()

def obter_candles(timeframe, limit=100):
    try:
        resp = client.get_candles(SYMBOL, timeframe, limit)
        if resp.get("code") != "00000":
            return None
        data = resp.get("data", [])
        if not data:
            return None
        df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close", "volume", "quote_volume"])
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        return df.iloc[::-1].reset_index(drop=True)
    except Exception as e:
        log(f"Erro candles: {e}")
        return None

def obter_saldo_usdt():
    try:
        resp = client.get_account()
        if resp.get("code") != "00000":
            return 0
        for asset in resp.get("data", []):
            if asset.get("coin") == "USDT":
                return float(asset.get("available", 0))
        return 0
    except:
        return 0

def obter_preco():
    try:
        resp = client.get_ticker(SYMBOL)
        if resp.get("code") != "00000":
            return None
        return float(resp.get("data", [{}])[0].get("lastPr", 0))
    except:
        return None

def tem_btc():
    try:
        resp = client.get_account()
        if resp.get("code") != "00000":
            return False
        for asset in resp.get("data", []):
            if asset.get("coin") == "BTC" and float(asset.get("available", 0)) > 0.0001:
                return True
        return False
    except:
        return False

def calcular_atr(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"].shift(1)
    tr = pd.concat([high - low, (high - close).abs(), (low - close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]

def calcular_tamanho(preco):
    if not USAR_RISCO_PERCENTUAL:
        return LOTE_FIXO
    saldo = obter_saldo_usdt()
    if saldo <= 0:
        return LOTE_FIXO
    return round(max(0.0001, (saldo * RISCO_PERCENTUAL / 100) / preco), 4)

def executar(side, tamanho):
    try:
        result = client.place_order(SYMBOL, side, tamanho)
        return result.get("code") == "00000"
    except Exception as e:
        log(f"Erro ordem: {e}")
        return False

def verificar_stops(preco):
    global estado
    pos = estado.get("posicao")
    if not pos:
        return

    entrada = pos["preco"]
    variacao = (preco - entrada) / entrada * 100

    # Atualiza máximo para trailing
    if estado.get("preco_maximo") is None or preco > estado["preco_maximo"]:
        estado["preco_maximo"] = preco
        salvar_estado(estado)

    # Trailing Stop
    if USAR_TRAILING_STOP and variacao >= TRAILING_ATIVAR_EM_PERCENT:
        trailing_stop = estado["preco_maximo"] * (1 - TRAILING_DISTANCIA_PERCENT / 100)
        if preco <= trailing_stop:
            log(f"TRAILING STOP ativado ({variacao:.2f}%)")
            if executar("sell", pos["tamanho"]):
                estado["posicao"] = None
                estado["preco_maximo"] = None
                registrar_perda(estado) if variacao < 0 else None
                salvar_estado(estado)
                return

    # Stop Loss normal
    stop = -STOP_LOSS_PERCENT
    if USAR_ATR_STOP:
        # ATR já calculado na análise se necessário
        pass

    if variacao <= stop:
        log(f"STOP LOSS ({variacao:.2f}%)")
        if executar("sell", pos["tamanho"]):
            estado["posicao"] = None
            estado["preco_maximo"] = None
            registrar_perda(estado)
            salvar_estado(estado)
    elif variacao >= TAKE_PROFIT_PERCENT:
        log(f"TAKE PROFIT ({variacao:.2f}%)")
        if executar("sell", pos["tamanho"]):
            estado["posicao"] = None
            estado["preco_maximo"] = None
            salvar_estado(estado)

def loop():
    global estado
    log("Bot iniciado | BTCUSDT Spot | Gestão de risco completa")
    log(f"Limite diário: {LIMITE_PERDA_DIARIA_PERCENT}% | Kill switch: {KILL_SWITCH_PERCENT}%")

    try:
        while True:
            saldo = obter_saldo_usdt()
            estado = iniciar_dia(estado, saldo)

            # Kill switch
            if verificar_kill_switch(estado, saldo, KILL_SWITCH_PERCENT):
                log(f"KILL SWITCH ativado! Drawdown >= {KILL_SWITCH_PERCENT}%")
                break

            # Limite diário
            if verificar_limite_diario(estado, saldo, LIMITE_PERDA_DIARIA_PERCENT):
                log(f"Limite diário atingido ({LIMITE_PERDA_DIARIA_PERCENT}%). Pausando até amanhã.")
                time.sleep(3600)
                continue

            # Cooldown
            if em_cooldown(estado, COOLDOWN_APOS_PERDA_MINUTOS):
                log("Em cooldown após perda...")
                time.sleep(INTERVALO_SEGUNDOS)
                continue

            # Análise
            dados = {}
            for tf in TIMEFRAMES:
                df = obter_candles(tf)
                if df is not None:
                    dados[tf] = df

            if len(dados) < 2:
                time.sleep(INTERVALO_SEGUNDOS)
                continue

            resultado = analisar_multi_timeframe(dados)
            preco = obter_preco()

            if preco and estado.get("posicao"):
                verificar_stops(preco)

            if resultado["sinal"] == "buy" and not tem_btc() and not estado.get("posicao") and preco:
                tamanho = calcular_tamanho(preco)
                if executar("buy", tamanho):
                    estado["posicao"] = {"preco": preco, "tamanho": tamanho}
                    estado["preco_maximo"] = preco
                    salvar_estado(estado)
                    log(f"COMPRA executada @ {preco}")

            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        log("Bot parado pelo usuário")

if __name__ == "__main__":
    loop()
