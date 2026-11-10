from datetime import datetime, date
import os
from config import RELATORIO_ARQUIVO

def gerar_relatorio(estado, saldo_atual):
    hoje = str(date.today())
    linhas = [
        f"===== RELATÓRIO {hoje} =====",
        f"Gerado em: {datetime.now().strftime('%H:%M:%S')}",
        f"Saldo atual: {saldo_atual:.2f} USDT",
        f"Saldo início do dia: {estado.get('saldo_inicio_dia', 0):.2f} USDT",
        f"Posição aberta: {'Sim' if estado.get('posicao') else 'Não'}",
        "=" * 40,
        ""
    ]

    with open(RELATORIO_ARQUIVO, "a", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
