"""
Backtest simples da estratégia nos últimos meses de BTC.
Usa dados públicos da Bitget (sem autenticação).
"""
import requests
import pandas as pd
from analise import analisar_timeframe, obter_tendencia_maior

def baixar_candles(granularity="1h", limit=1000):
    url = "https://api.bitget.com/api/v2/spot/market/candles"
    params = {"symbol": "BTCUSDT", "granularity": granularity, "limit": limit}
    resp = requests.get(url, params=params)
    data = resp.json().get("data", [])
    if not data:
        return None
    df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close", "volume", "quote_volume", "extra"])
    df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
    return df.iloc[::-1].reset_index(drop=True)

def rodar_backtest():
    print("Baixando dados históricos...")
    df_1h = baixar_candles("1h", 1000)
    df_4h = baixar_candles("4h", 500)
    df_1d = baixar_candles("1day", 200)

    if df_1h is None:
        print("Erro ao baixar dados")
        return

    print(f"Dados: {len(df_1h)} candles de 1H")

    capital = 1000.0
    posicao = None
    trades = []

    for i in range(100, len(df_1h)):
        janela = df_1h.iloc[i-100:i].reset_index(drop=True)
        res = analisar_timeframe(janela)

        # Tendência maior (simplificada no backtest)
        tendencia = "neutro"
        if df_4h is not None and i > 50:
            idx_4h = min(i // 4, len(df_4h) - 1)
            if idx_4h > 50:
                janela_4h = df_4h.iloc[max(0, idx_4h-100):idx_4h].reset_index(drop=True)
                if len(janela_4h) > 50:
                    res_4h = analisar_timeframe(janela_4h)
                    if res_4h["score_compra"] > res_4h["score_venda"] + 1:
                        tendencia = "alta"
                    elif res_4h["score_venda"] > res_4h["score_compra"] + 1:
                        tendencia = "baixa"

        preco = janela["close"].iloc[-1]

        # Venda
        if posicao:
            variacao = (preco - posicao["preco"]) / posicao["preco"] * 100
            if res["score_venda"] >= 5 or variacao >= 4 or variacao <= -2:
                lucro_pct = variacao
                capital *= (1 + lucro_pct / 100)
                trades.append({"tipo": "venda", "preco": preco, "lucro": lucro_pct})
                posicao = None

        # Compra
        elif not posicao and res["score_compra"] >= 5 and tendencia != "baixa":
            posicao = {"preco": preco}
            trades.append({"tipo": "compra", "preco": preco, "lucro": 0})

    print(f"\n=== RESULTADO DO BACKTEST ===")
    print(f"Capital inicial: $1000")
    print(f"Capital final: ${capital:.2f}")
    print(f"Retorno: {(capital - 1000) / 10:.1f}%")
    print(f"Total de trades: {len([t for t in trades if t['tipo'] == 'venda'])}")

    if trades:
        lucros = [t["lucro"] for t in trades if t["tipo"] == "venda"]
        if lucros:
            print(f"Trades lucrativos: {len([l for l in lucros if l > 0])}")
            print(f"Trades com prejuízo: {len([l for l in lucros if l <= 0])}")
            print(f"Média por trade: {sum(lucros)/len(lucros):.2f}%")

if __name__ == "__main__":
    rodar_backtest()
