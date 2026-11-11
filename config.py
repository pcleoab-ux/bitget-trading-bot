import os
from dotenv import load_dotenv

load_dotenv()

# ===================== CONFIGURAÇÃO DO BOT BITGET =====================

API_KEY = os.getenv("API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
PASSPHRASE = os.getenv("PASSPHRASE", "")

# Modo
MODO_SIMULACAO = False
CONFIRMAR_PRIMEIRA_ORDEM = False

# Operação
SYMBOL = "BTCUSDT"
TIMEFRAMES = ["15min", "1h", "4h"]

# Risco
USAR_RISCO_PERCENTUAL = True
RISCO_PERCENTUAL = 10.0          # Aumentado para garantir ordem mínima
LOTE_FIXO = 0.001
SALDO_MINIMO_USDT = 5.0          # Reduzido
ORDEM_MINIMA_USDT = 1.0          # Mínimo da Bitget

# Gestão de risco
LIMITE_PERDA_DIARIA_PERCENT = 3.0
KILL_SWITCH_PERCENT = 8.0
STOP_LOSS_PERCENT = 2.0
TAKE_PROFIT_PERCENT = 4.0
USAR_TRAILING_STOP = True
TRAILING_ATIVAR_EM_PERCENT = 1.5
TRAILING_DISTANCIA_PERCENT = 1.0
COOLDOWN_APOS_PERDA_MINUTOS = 30

# Controle
INTERVALO_SEGUNDOS = 20
LOG_ARQUIVO = "bot.log"
RELATORIO_ARQUIVO = "relatorio_diario.txt"
# =======================================================================
