import pandas as pd

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
    return macd, macd_signal

def calcular_bollinger(series, period=20, std=2):
    ma = series.rolling(period).mean()
    desvio = series.rolling(period).std()
    return ma + (desvio * std), ma, ma - (desvio * std)

def calcular_suporte_resistencia(df, janela=20):
    resistencia = df["high"].rolling(janela).max().iloc[-1]
    suporte = df["low"].rolling(janela).min().iloc[-1]
    return suporte, resistencia

def analisar_timeframe(df):
    if len(df) < 50:
        return {"score_compra": 0, "score_venda": 0, "motivos": [], "suporte": 0, "resistencia": 0, "preco": 0, "rsi": 0}

    df = df.copy()
    df["rsi"] = calcular_rsi(df["close"])
    df["ema12"] = calcular_ema(df["close"], 12)
    df["ema26"] = calcular_ema(df["close"], 26)
    macd, macd_signal = calcular_macd(df["close"])
    df["macd"] = macd
    df["macd_signal"] = macd_signal
    bb_sup, _, bb_inf = calcular_bollinger(df["close"])
    df["bb_sup"] = bb_sup
    df["bb_inf"] = bb_inf
    df["volume_ma"] = df["volume"].rolling(20).mean()

    ultimo = df.iloc[-1]
    anterior = df.iloc[-2]

    score_compra = 0
    score_venda = 0
    motivos = []

    if ultimo["rsi"] < 35:
        score_compra += 1
        motivos.append("RSI sobrevendido")
    elif ultimo["rsi"] > 65:
        score_venda += 1
        motivos.append("RSI sobrecomprado")

    if ultimo["ema12"] > ultimo["ema26"]:
        score_compra += 1
        motivos.append("Tendência de alta")
    else:
        score_venda += 1
        motivos.append("Tendência de baixa")

    if anterior["macd"] < anterior["macd_signal"] and ultimo["macd"] > ultimo["macd_signal"]:
        score_compra += 2
        motivos.append("MACD cruzou alta")
    elif anterior["macd"] > anterior["macd_signal"] and ultimo["macd"] < ultimo["macd_signal"]:
        score_venda += 2
        motivos.append("MACD cruzou baixa")

    if ultimo["close"] <= ultimo["bb_inf"]:
        score_compra += 1
        motivos.append("Banda inferior")
    elif ultimo["close"] >= ultimo["bb_sup"]:
        score_venda += 1
        motivos.append("Banda superior")

    if ultimo["volume"] > ultimo["volume_ma"] * 1.3:
        if ultimo["close"] > anterior["close"]:
            score_compra += 1
            motivos.append("Volume + alta")
        else:
            score_venda += 1
            motivos.append("Volume + baixa")

    suporte, resistencia = calcular_suporte_resistencia(df)
    preco = ultimo["close"]
    if (preco - suporte) / preco * 100 < 1.0:
        score_compra += 1
        motivos.append(f"Perto do suporte ({suporte:.0f})")
    if (resistencia - preco) / preco * 100 < 1.0:
        score_venda += 1
        motivos.append(f"Perto da resistência ({resistencia:.0f})")

    return {
        "score_compra": score_compra,
        "score_venda": score_venda,
        "motivos": motivos,
        "suporte": round(suporte, 2),
        "resistencia": round(resistencia, 2),
        "preco": preco,
        "rsi": round(ultimo["rsi"], 1)
    }

def analisar_multi_timeframe(dados_por_tf):
    resultados = {}
    score_total_compra = 0
    score_total_venda = 0
    tfs_compra = 0
    tfs_venda = 0

    for tf, df in dados_por_tf.items():
        res = analisar_timeframe(df)
        resultados[tf] = res
        score_total_compra += res["score_compra"]
        score_total_venda += res["score_venda"]
        if res["score_compra"] > res["score_venda"]:
            tfs_compra += 1
        elif res["score_venda"] > res["score_compra"]:
            tfs_venda += 1

    sinal = None
    if score_total_compra >= 3 and tfs_compra >= 2:
        sinal = "buy"
    elif score_total_venda >= 3 and tfs_venda >= 2:
        sinal = "sell"

    principal = resultados.get("15min", resultados.get("15m", {}))

    return {
        "sinal": sinal,
        "score_compra": score_total_compra,
        "score_venda": score_total_venda,
        "timeframes_compra": tfs_compra,
        "timeframes_venda": tfs_venda,
        "detalhes": resultados,
        "suporte": principal.get("suporte"),
        "resistencia": principal.get("resistencia"),
        "preco": principal.get("preco")
    }
