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
    return macd, macd_signal

def calcular_bollinger(series, period=20, std=2):
    ma = series.rolling(period).mean()
    desvio = series.rolling(period).std()
    return ma + (desvio * std), ma, ma - (desvio * std)

def calcular_adx(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()
    return adx

def calcular_atr(df, period=14):
    high = df["high"]
    low = df["low"]
    close = df["close"]
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def calcular_suporte_resistencia(df, janela=20):
    resistencia = df["high"].rolling(janela).max().iloc[-1]
    suporte = df["low"].rolling(janela).min().iloc[-1]
    return suporte, resistencia

def analisar_timeframe(df):
    if len(df) < 50:
        return {"score_compra": 0, "score_venda": 0, "motivos": [], "suporte": 0, "resistencia": 0, "preco": 0, "rsi": 0, "adx": 0, "atr_pct": 0, "volume_agressao": 0}

    df = df.copy()
    df["rsi"] = calcular_rsi(df["close"])
    df["ema12"] = calcular_ema(df["close"], 12)
    df["ema26"] = calcular_ema(df["close"], 26)
    df["ema50"] = calcular_ema(df["close"], 50)
    macd, macd_signal = calcular_macd(df["close"])
    df["macd"] = macd
    df["macd_signal"] = macd_signal
    bb_sup, _, bb_inf = calcular_bollinger(df["close"])
    df["bb_sup"] = bb_sup
    df["bb_inf"] = bb_inf
    df["volume_ma"] = df["volume"].rolling(20).mean()
    df["adx"] = calcular_adx(df)
    df["atr"] = calcular_atr(df)

    ultimo = df.iloc[-1]
    anterior = df.iloc[-2]

    score_compra = 0
    score_venda = 0
    motivos = []

    # RSI
    if ultimo["rsi"] < 30:
        score_compra += 2
        motivos.append("RSI muito sobrevendido")
    elif ultimo["rsi"] < 40:
        score_compra += 1
        motivos.append("RSI sobrevendido")
    elif ultimo["rsi"] > 70:
        score_venda += 2
        motivos.append("RSI muito sobrecomprado")
    elif ultimo["rsi"] > 60:
        score_venda += 1
        motivos.append("RSI sobrecomprado")

    # Tendência EMA
    if ultimo["ema12"] > ultimo["ema26"] > ultimo["ema50"]:
        score_compra += 2
        motivos.append("Tendência de alta forte")
    elif ultimo["ema12"] > ultimo["ema26"]:
        score_compra += 1
        motivos.append("Tendência de alta")
    elif ultimo["ema12"] < ultimo["ema26"] < ultimo["ema50"]:
        score_venda += 2
        motivos.append("Tendência de baixa forte")
    else:
        score_venda += 1
        motivos.append("Tendência de baixa")

    # MACD
    if anterior["macd"] < anterior["macd_signal"] and ultimo["macd"] > ultimo["macd_signal"]:
        score_compra += 2
        motivos.append("MACD cruzou alta")
    elif anterior["macd"] > anterior["macd_signal"] and ultimo["macd"] < ultimo["macd_signal"]:
        score_venda += 2
        motivos.append("MACD cruzou baixa")

    # Bollinger
    if ultimo["close"] <= ultimo["bb_inf"]:
        score_compra += 1
        motivos.append("Tocou banda inferior")
    elif ultimo["close"] >= ultimo["bb_sup"]:
        score_venda += 1
        motivos.append("Tocou banda superior")

    # Volume de agressão (volume alto + direção)
    volume_ratio = ultimo["volume"] / ultimo["volume_ma"] if ultimo["volume_ma"] > 0 else 1
    if volume_ratio > 1.5:
        if ultimo["close"] > anterior["close"]:
            score_compra += 2
            motivos.append(f"Volume agressão compra ({volume_ratio:.1f}x)")
        else:
            score_venda += 2
            motivos.append(f"Volume agressão venda ({volume_ratio:.1f}x)")
    elif volume_ratio > 1.2:
        if ultimo["close"] > anterior["close"]:
            score_compra += 1
            motivos.append("Volume acima da média")
        else:
            score_venda += 1
            motivos.append("Volume acima da média")

    # Suporte / Resistência
    suporte, resistencia = calcular_suporte_resistencia(df)
    preco = ultimo["close"]
    if (preco - suporte) / preco * 100 < 0.8:
        score_compra += 1
        motivos.append("Perto do suporte")
    if (resistencia - preco) / preco * 100 < 0.8:
        score_venda += 1
        motivos.append("Perto da resistência")

    # ADX
    adx = ultimo["adx"] if not pd.isna(ultimo["adx"]) else 0
    if adx < 20:
        score_compra = max(0, score_compra - 1)
        score_venda = max(0, score_venda - 1)
        motivos.append(f"ADX fraco ({adx:.0f})")

    # ATR percentual (volatilidade)
    atr_pct = (ultimo["atr"] / preco * 100) if preco > 0 and not pd.isna(ultimo["atr"]) else 0

    return {
        "score_compra": score_compra,
        "score_venda": score_venda,
        "motivos": motivos,
        "suporte": round(suporte, 2),
        "resistencia": round(resistencia, 2),
        "preco": preco,
        "rsi": round(ultimo["rsi"], 1),
        "adx": round(adx, 1),
        "atr_pct": round(atr_pct, 2),
        "volume_agressao": round(volume_ratio, 2)
    }

def analisar_multi_timeframe(dados_por_tf, tendencia_maior="neutro"):
    resultados = {}
    score_total_compra = 0
    score_total_venda = 0
    tfs_compra = 0
    tfs_venda = 0
    adx_medio = 0
    atr_medio = 0

    for tf, df in dados_por_tf.items():
        res = analisar_timeframe(df)
        resultados[tf] = res
        score_total_compra += res["score_compra"]
        score_total_venda += res["score_venda"]
        adx_medio += res.get("adx", 0)
        atr_medio += res.get("atr_pct", 0)
        if res["score_compra"] > res["score_venda"]:
            tfs_compra += 1
        elif res["score_venda"] > res["score_compra"]:
            tfs_venda += 1

    n = len(dados_por_tf) if dados_por_tf else 1
    adx_medio = adx_medio / n
    atr_medio = atr_medio / n

    # Score mínimo dinâmico baseado na volatilidade
    # Alta volatilidade = exige mais confiança
    if atr_medio > 3.0:
        score_minimo = 7
    elif atr_medio > 2.0:
        score_minimo = 6
    else:
        score_minimo = 5

    sinal = None

    # Filtro de tendência maior
    if tendencia_maior == "alta":
        # Só permite compra
        if score_total_compra >= score_minimo and tfs_compra >= 2 and adx_medio >= 20:
            sinal = "buy"
    elif tendencia_maior == "baixa":
        # Só permite venda
        if score_total_venda >= score_minimo and tfs_venda >= 2 and adx_medio >= 20:
            sinal = "sell"
    else:
        # Neutro: exige score ainda maior
        if score_total_compra >= score_minimo + 1 and tfs_compra >= 2 and adx_medio >= 22:
            sinal = "buy"
        elif score_total_venda >= score_minimo + 1 and tfs_venda >= 2 and adx_medio >= 22:
            sinal = "sell"

    principal = resultados.get("15min", resultados.get("15m", {}))

    return {
        "sinal": sinal,
        "score_compra": score_total_compra,
        "score_venda": score_total_venda,
        "score_minimo": score_minimo,
        "timeframes_compra": tfs_compra,
        "timeframes_venda": tfs_venda,
        "adx": round(adx_medio, 1),
        "atr_pct": round(atr_medio, 2),
        "tendencia_maior": tendencia_maior,
        "detalhes": resultados,
        "suporte": principal.get("suporte"),
        "resistencia": principal.get("resistencia"),
        "preco": principal.get("preco")
    }

def obter_tendencia_maior(df_4h=None, df_1d=None):
    """Retorna 'alta', 'baixa' ou 'neutro' baseado no 4H e diário."""
    votos_alta = 0
    votos_baixa = 0

    for df in [df_4h, df_1d]:
        if df is None or len(df) < 50:
            continue
        ema12 = calcular_ema(df["close"], 12).iloc[-1]
        ema26 = calcular_ema(df["close"], 26).iloc[-1]
        ema50 = calcular_ema(df["close"], 50).iloc[-1]
        if ema12 > ema26 > ema50:
            votos_alta += 1
        elif ema12 < ema26 < ema50:
            votos_baixa += 1

    if votos_alta > votos_baixa:
        return "alta"
    elif votos_baixa > votos_alta:
        return "baixa"
    return "neutro"
