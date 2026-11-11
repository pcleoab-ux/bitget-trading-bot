import json
import os
from datetime import datetime, date

ARQUIVO_ESTADO = "estado_bot.json"

def carregar_estado():
    if not os.path.exists(ARQUIVO_ESTADO):
        return {
            "saldo_inicial": None,
            "saldo_inicio_dia": None,
            "data_dia": None,
            "perdas_hoje": 0.0,
            "ultimo_loss": None,
            "posicao": None,
            "preco_maximo": None,
            "trades": [],
            "score_ajuste": 0
        }
    with open(ARQUIVO_ESTADO, "r") as f:
        estado = json.load(f)
        if "trades" not in estado:
            estado["trades"] = []
        if "score_ajuste" not in estado:
            estado["score_ajuste"] = 0
        return estado

def salvar_estado(estado):
    with open(ARQUIVO_ESTADO, "w") as f:
        json.dump(estado, f, indent=2, default=str)

def iniciar_dia(estado, saldo_atual):
    hoje = str(date.today())
    if estado["data_dia"] != hoje:
        estado["data_dia"] = hoje
        estado["saldo_inicio_dia"] = saldo_atual
        estado["perdas_hoje"] = 0.0
        salvar_estado(estado)
    if estado["saldo_inicial"] is None:
        estado["saldo_inicial"] = saldo_atual
        salvar_estado(estado)
    return estado

def verificar_limite_diario(estado, saldo_atual, limite_percent):
    if not estado["saldo_inicio_dia"]:
        return False
    perda = (estado["saldo_inicio_dia"] - saldo_atual) / estado["saldo_inicio_dia"] * 100
    return perda >= limite_percent

def verificar_kill_switch(estado, saldo_atual, limite_percent):
    if not estado["saldo_inicial"]:
        return False
    drawdown = (estado["saldo_inicial"] - saldo_atual) / estado["saldo_inicial"] * 100
    return drawdown >= limite_percent

def em_cooldown(estado, minutos):
    if not estado.get("ultimo_loss"):
        return False
    ultimo = datetime.fromisoformat(estado["ultimo_loss"])
    return (datetime.now() - ultimo).total_seconds() < minutos * 60

def registrar_perda(estado):
    estado["ultimo_loss"] = datetime.now().isoformat()
    salvar_estado(estado)

def registrar_trade(estado, lucro_percent):
    """Registra o resultado de um trade e ajusta o score."""
    estado["trades"].append({
        "data": datetime.now().isoformat(),
        "lucro": round(lucro_percent, 2)
    })
    # Mantém só os últimos 20 trades
    estado["trades"] = estado["trades"][-20:]

    # Ajuste adaptativo
    recentes = estado["trades"][-5:]
    perdas_recentes = len([t for t in recentes if t["lucro"] < 0])
    ganhos_recentes = len([t for t in recentes if t["lucro"] > 0])

    if perdas_recentes >= 3:
        estado["score_ajuste"] = min(estado.get("score_ajuste", 0) + 1, 3)
    elif ganhos_recentes >= 3:
        estado["score_ajuste"] = max(estado.get("score_ajuste", 0) - 1, 0)

    salvar_estado(estado)

def get_score_minimo_ajustado(score_base, estado):
    """Retorna o score mínimo ajustado pelo desempenho."""
    return score_base + estado.get("score_ajuste", 0)

def get_estatisticas(estado):
    """Retorna estatísticas dos trades."""
    trades = estado.get("trades", [])
    if not trades:
        return {"total": 0, "ganhos": 0, "perdas": 0, "taxa": 0, "media": 0}
    ganhos = len([t for t in trades if t["lucro"] > 0])
    perdas = len([t for t in trades if t["lucro"] <= 0])
    media = sum(t["lucro"] for t in trades) / len(trades)
    taxa = (ganhos / len(trades)) * 100 if trades else 0
    return {
        "total": len(trades),
        "ganhos": ganhos,
        "perdas": perdas,
        "taxa": round(taxa, 1),
        "media": round(media, 2)
    }
