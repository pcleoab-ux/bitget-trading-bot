# ===================== CONFIGURAÇÃO DO BOT BITGET =====================
# BTCUSDT Spot | Versão com gestão de risco completa

# API Keys
API_KEY = "sua_api_key"
SECRET_KEY = "seu_secret_key"
PASSPHRASE = "seu_passphrase"

# Operação
SYMBOL = "BTCUSDT"
TIMEFRAMES = ["15m", "1H", "4H"]

# Risco
USAR_RISCO_PERCENTUAL = True
RISCO_PERCENTUAL = 1.0
LOTE_FIXO = 0.001

# ===== GESTÃO DE RISCO =====
# Limite de perda diária (em % do saldo)
LIMITE_PERDA_DIARIA_PERCENT = 3.0          # Para o bot se perder 3% no dia

# Kill switch (drawdown total desde o início)
KILL_SWITCH_PERCENT = 8.0                  # Para tudo se cair 8% do saldo inicial

# Stop Loss e Take Profit
STOP_LOSS_PERCENT = 2.0
TAKE_PROFIT_PERCENT = 4.0
USAR_ATR_STOP = True                       # Stop dinâmico baseado em volatilidade
ATR_MULTIPLICADOR = 1.5

# Trailing Stop
USAR_TRAILING_STOP = True
TRAILING_ATIVAR_EM_PERCENT = 1.5           # Começa a seguir depois de 1.5% de lucro
TRAILING_DISTANCIA_PERCENT = 1.0           # Mantém 1% atrás do máximo

# Cooldown
COOLDOWN_APOS_PERDA_MINUTOS = 30           # Espera 30 min depois de uma perda

# Controle
INTERVALO_SEGUNDOS = 20
LOG_ARQUIVO = "bot.log"
# =======================================================================
