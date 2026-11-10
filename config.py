# ===================== CONFIGURAÇÃO DO BOT BITGET =====================

# API Keys (crie em: Bitget > API Management)
API_KEY = "sua_api_key"
SECRET_KEY = "seu_secret_key"
PASSPHRASE = "seu_passphrase"

# Operação
SYMBOL = "BTCUSDT"
PRODUCT_TYPE = "USDT-FUTURES"   # USDT-FUTURES ou SPOT
MARGIN_MODE = "crossed"         # crossed ou isolated
LEVERAGE = 5

# Lote / Risco
USAR_RISCO_PERCENTUAL = True
RISCO_PERCENTUAL = 1.0          # % do saldo por operação
LOTE_FIXO = 0.001               # usado se USAR_RISCO_PERCENTUAL = False

# Estratégia
TIMEFRAME = "5m"                # 1m, 5m, 15m, 1H, 4H
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
MA_PERIOD = 50

# Gerenciamento
STOP_LOSS_PERCENT = 1.0         # %
TAKE_PROFIT_PERCENT = 2.0       # %
MAX_POSICOES = 1

# Controle
INTERVALO_SEGUNDOS = 10
# =======================================================================
