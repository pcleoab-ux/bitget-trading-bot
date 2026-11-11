import time
import pandas as pd
from datetime import datetime
from bitget_client import BitgetClient
from analise import analisar_multi_timeframe
from risco import *
from conexao import testar_conexao, obter_saldo
from relatorio import gerar_relatorio
from config import *

def log(msg):
    linha = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(linha)
    with open(LOG_ARQUIVO, "a", encoding="utf-8") as f:
        f.write(linha + "\n")

def obter_candles(client, timeframe, limit=100):
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
    except Exception as e:
        log(f"Erro ao buscar candles: {e}")
        return None

def obter_preco(client):
    try:
        resp = client.get_ticker(SYMBOL)
        if resp.get("code") != "00000":
            return None
        return float(resp.get("data", [{}])[0].get("lastPr", 0))
    except:
        return None

def loop():
    log("=" * 50)
    log("BOT BITGET | BTCUSDT SPOT")
    log(f"Modo: {'SIMULAÇÃO' if MODO_SIMULACAO else 'REAL'}")
    log("=" * 50)

    ok, msg = testar_conexao()
    if not ok:
        log(f"ERRO DE CONEXÃO: {msg}")
        return
    log(msg)

    saldo = obter_saldo()
    log(f"Saldo USDT: {saldo:.2f}")

    if saldo < SALDO_MINIMO_USDT and not MODO_SIMULACAO:
        log(f"Saldo abaixo do mínimo ({SALDO_MINIMO_USDT} USDT). Bot não iniciará.")
        return

    client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)
    estado = carregar_estado()
    estado = iniciar_dia(estado, saldo)

    log("Iniciando análise... (Ctrl+C para parar)")

    try:
        while True:
            saldo = obter_saldo()
            estado = iniciar_dia(estado, saldo)

            if verificar_kill_switch(estado, saldo, KILL_SWITCH_PERCENT):
                log(f"KILL SWITCH! Drawdown >= {KILL_SWITCH_PERCENT}%")
                break

            if verificar_limite_diario(estado, saldo, LIMITE_PERDA_DIARIA_PERCENT):
                log(f"Limite diário atingido ({LIMITE_PERDA_DIARIA_PERCENT}%)")
                gerar_relatorio(estado, saldo)
                time.sleep(3600)
                continue

            if em_cooldown(estado, COOLDOWN_APOS_PERDA_MINUTOS):
                log("Em cooldown...")
                time.sleep(INTERVALO_SEGUNDOS)
                continue

            dados = {}
            for tf in TIMEFRAMES:
                df = obter_candles(client, tf)
                if df is not None:
                    dados[tf] = df

            if len(dados) < 2:
                log("Aguardando dados suficientes...")
                time.sleep(INTERVALO_SEGUNDOS)
                continue

            resultado = analisar_multi_timeframe(dados)
            preco = obter_preco(client)

            log("-" * 40)
            log(f"Preço: {resultado.get('preco', 0):.2f} | Suporte: {resultado.get('suporte')} | Resistência: {resultado.get('resistencia')}")
            log(f"Score Compra: {resultado['score_compra']} | Score Venda: {resultado['score_venda']}")
            log(f"Timeframes → Compra: {resultado['timeframes_compra']} | Venda: {resultado['timeframes_venda']}")
            if resultado["sinal"]:
                log(f">>> SINAL: {resultado['sinal'].upper()}")
            else:
                log(">>> Sem sinal forte")

            # Executa compra
            if resultado["sinal"] == "buy" and not estado.get("posicao") and preco:
                tamanho = round(max(0.0001, (saldo * RISCO_PERCENTUAL / 100) / preco), 6)
                log(f"Tentando comprar {tamanho} BTC @ {preco}")

                if MODO_SIMULACAO:
                    log(f"[SIMULAÇÃO] COMPRA | {tamanho} BTC @ {preco}")
                    estado["posicao"] = {"preco": preco, "tamanho": tamanho}
                    salvar_estado(estado)
                else:
                    resp = client.place_order(SYMBOL, "buy", tamanho)
                    log(f"Resposta da API: {resp}")
                    if resp.get("code") == "00000":
                        estado["posicao"] = {"preco": preco, "tamanho": tamanho}
                        salvar_estado(estado)
                        log(f"COMPRA REAL EXECUTADA @ {preco}")
                    else:
                        log(f"ERRO NA ORDEM: {resp.get('msg', 'desconhecido')}")

            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        log("Bot parado")
        gerar_relatorio(estado, obter_saldo())

if __name__ == "__main__":
    loop()
