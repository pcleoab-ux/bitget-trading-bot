# ===================== CONFIGURAÇÃO DO BOT BITGET =====================
# BTCUSDT Spot | Análise completa + Multi-timeframe + Stop Loss

# API Keys
API_KEY = "sua_api_key"
SECRET_KEY = "seu_secret_key"
PASSPHRASE = "seu_passphrase"

# Operação
SYMBOL = "BTCUSDT"
TIMEFRAMES = ["15m", "1H", "4H"]     # Análise em múltiplos timeframes
TIMEFRAME_PRINCIPAL = "15m"

# Risco
USAR_RISCO_PERCENTUAL = True
RISCO_PERCENTUAL = 1.0
LOTE_FIXO = 0.001

# Stop Loss e Take Profit (manual, já que é Spot)
STOP_LOSS_PERCENT = 2.0              # %
TAKE_PROFIT_PERCENT = 4.0            # %

# Análise
SCORE_MINIMO = 3
REQUIRE_MULTI_TIMEFRAME = True       # Exige confirmação em pelo menos 2 timeframes

# Controle
INTERVALO_SEGUNDOS = 20
# =======================================================================
