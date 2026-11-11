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

def obter_saldo_btc(client):
    """Retorna o saldo de BTC disponível."""
    try:
        resp = client.get_account()
        if resp.get("code") != "00000":
            return 0
        for asset in resp.get("data", []):
            if asset.get("coin") == "BTC":
                return float(asset.get("available", 0))
        return 0
    except:
        return 0

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
            saldo_btc = obter_saldo_btc(client)

            log("-" * 40)
            log(f"Saldo: {saldo:.2f} USDT | BTC: {saldo_btc:.6f} | Preço: {preco:.2f}")
            log(f"Suporte: {resultado.get('suporte')} | Resistência: {resultado.get('resistencia')}")
            log(f"Score Compra: {resultado['score_compra']} | Score Venda: {resultado['score_venda']}")
            log(f"Timeframes → Compra: {resultado['timeframes_compra']} | Venda: {resultado['timeframes_venda']}")
            if resultado["sinal"]:
                log(f">>> SINAL: {resultado['sinal'].upper()}")
            else:
                log(">>> Sem sinal forte")

            posicao = estado.get("posicao")

            # ---------- VENDA (fechar posição) ----------
            if posicao and preco and saldo_btc > 0.00001:
                preco_entrada = posicao.get("preco", preco)
                variacao = (preco - preco_entrada) / preco_entrada * 100

                vender = False
                motivo = ""

                if resultado["sinal"] == "sell":
                    vender = True
                    motivo = "Sinal de venda"
                elif variacao >= TAKE_PROFIT_PERCENT:
                    vender = True
                    motivo = f"Take Profit ({variacao:.2f}%)"
                elif variacao <= -STOP_LOSS_PERCENT:
                    vender = True
                    motivo = f"Stop Loss ({variacao:.2f}%)"

                if vender:
                    log(f"Vendendo BTC | Motivo: {motivo}")
                    if MODO_SIMULACAO:
                        log(f"[SIMULAÇÃO] VENDA | {saldo_btc:.6f} BTC @ {preco}")
                        estado["posicao"] = None
                        salvar_estado(estado)
                    else:
                        resp = client.place_order(SYMBOL, "sell", round(saldo_btc, 6))
                        if resp.get("code") == "00000":
                            log(f"VENDA REAL EXECUTADA | {saldo_btc:.6f} BTC @ {preco} | {motivo}")
                            estado["posicao"] = None
                            salvar_estado(estado)
                        else:
                            log(f"ERRO NA VENDA: {resp.get('msg', 'desconhecido')}")

            # ---------- COMPRA (abrir posição) ----------
            elif resultado["sinal"] == "buy" and not posicao and preco and saldo > 2:
                valor_usdt = max(2.0, round(saldo * 0.9, 2))
                if valor_usdt > saldo - 0.5:
                    valor_usdt = round(saldo - 0.5, 2)
                log(f"Tentando comprar ~{valor_usdt} USDT de BTC")

                if MODO_SIMULACAO:
                    log(f"[SIMULAÇÃO] COMPRA | {valor_usdt} USDT")
                    estado["posicao"] = {"preco": preco, "tamanho_usdt": valor_usdt}
                    salvar_estado(estado)
                else:
                    resp = client.place_order(SYMBOL, "buy", valor_usdt)
                    if resp.get("code") == "00000":
                        estado["posicao"] = {"preco": preco, "tamanho_usdt": valor_usdt}
                        salvar_estado(estado)
                        log(f"COMPRA REAL EXECUTADA | {valor_usdt} USDT")
                    else:
                        log(f"ERRO NA ORDEM: {resp.get('msg', 'desconhecido')}")

            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        log("Bot parado")
        gerar_relatorio(estado, obter_saldo())

if __name__ == "__main__":
    loop()
