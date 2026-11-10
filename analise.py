import pandas as pd
import numpy as np

def calcular_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calcular_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calcular_macd(series, fast=12, slow=26, signal=9):
    ema_fast = calcular_ema(series, fast)
    ema_slow = calcular_ema(series, slow)
    macd = ema_fast - ema_slow
    macd_signal = calcular_ema(macd, signal)
    histograma = macd - macd_signal
    return macd, macd_signal, histograma

def calcular_bollinger(series, period=20, std=2):
    ma = series.rolling(period).mean()
    desvio = series.rolling(period).std()
    superior = ma + (desvio * std)
    inferior = ma - (desvio * std)
    return superior, ma, inferior

def analisar_completo(df):
    """Análise multi-indicador. Retorna score e detalhes."""
    if len(df) < 50:
        return {"score": 0, "sinal": None, "detalhes": "Dados insuficientes"}

    # Indicadores
    df["rsi"] = calcular_rsi(df["close"])
    df["ema12"] = calcular_ema(df["close"], 12)
    df["ema26"] = calcular_ema(df["close"], 26)
    macd, macd_signal, hist = calcular_macd(df["close"])
    df["macd"] = macd
    df["macd_signal"] = macd_signal
    df["histograma"] = hist
    bb_sup, bb_mid, bb_inf = calcular_bollinger(df["close"])
    df["bb_sup"] = bb_sup
    df["bb_mid"] = bb_mid
    df["bb_inf"] = bb_inf
    df["volume_ma"] = df["volume"].rolling(20).mean()

    ultimo = df.iloc[-1]
    anterior = df.iloc[-2]

    score_compra = 0
    score_venda = 0
    motivos_compra = []
    motivos_venda = []

    # 1. RSI
    if ultimo["rsi"] < 35:
        score_compra += 1
        motivos_compra.append(f"RSI sobrevendido ({ultimo['rsi']:.1f})")
    elif ultimo["rsi"] > 65:
        score_venda += 1
        motivos_venda.append(f"RSI sobrecomprado ({ultimo['rsi']:.1f})")

    # 2. Tendência EMA
    if ultimo["ema12"] > ultimo["ema26"]:
        score_compra += 1
        motivos_compra.append("EMA12 acima da EMA26 (tendência de alta)")
    else:
        score_venda += 1
        motivos_venda.append("EMA12 abaixo da EMA26 (tendência de baixa)")

    # 3. MACD cruzamento
    if anterior["macd"] < anterior["macd_signal"] and ultimo["macd"] > ultimo["macd_signal"]:
        score_compra += 2
        motivos_compra.append("Cruzamento MACD de alta")
    elif anterior["macd"] > anterior["macd_signal"] and ultimo["macd"] < ultimo["macd_signal"]:
        score_venda += 2
        motivos_venda.append("Cruzamento MACD de baixa")

    # 4. Bollinger
    if ultimo["close"] <= ultimo["bb_inf"]:
        score_compra += 1
        motivos_compra.append("Preço tocando banda inferior")
    elif ultimo["close"] >= ultimo["bb_sup"]:
        score_venda += 1
        motivos_venda.append("Preço tocando banda superior")

    # 5. Volume
    if ultimo["volume"] > ultimo["volume_ma"] * 1.3:
        if ultimo["close"] > anterior["close"]:
            score_compra += 1
            motivos_compra.append("Volume alto + candle de alta")
        else:
            score_venda += 1
            motivos_venda.append("Volume alto + candle de baixa")

    # 6. Posição em relação à média
    if ultimo["close"] > ultimo["bb_mid"]:
        score_compra += 0.5
    else:
        score_venda += 0.5

    # Decisão
    sinal = None
    if score_compra >= 3 and score_compra > score_venda:
        sinal = "buy"
    elif score_venda >= 3 and score_venda > score_compra:
        sinal = "sell"

    return {
        "sinal": sinal,
        "score_compra": round(score_compra, 1),
        "score_venda": round(score_venda, 1),
        "preco": ultimo["close"],
        "rsi": round(ultimo["rsi"], 1),
        "motivos_compra": motivos_compra,
        "motivos_venda": motivos_venda,
        "ema12": round(ultimo["ema12"], 2),
        "ema26": round(ultimo["ema26"], 2),
        "macd": round(ultimo["macd"], 2),
    }
