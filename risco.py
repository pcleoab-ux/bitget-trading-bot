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
            "preco_maximo": None
        }
    with open(ARQUIVO_ESTADO, "r") as f:
        return json.load(f)

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
