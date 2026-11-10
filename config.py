# ===================== CONFIGURAÇÃO DO BOT BITGET =====================
# Foco: BTCUSDT Spot (mais fácil de analisar)

# API Keys (crie em: Bitget > API Management)
API_KEY = "sua_api_key"
SECRET_KEY = "seu_secret_key"
PASSPHRASE = "seu_passphrase"

# Operação
SYMBOL = "BTCUSDT"
# Spot = mais fácil de analisar (sem liquidação e funding)

# Lote / Risco
USAR_RISCO_PERCENTUAL = True
RISCO_PERCENTUAL = 1.0          # % do saldo por operação
LOTE_FIXO = 0.001               # usado se USAR_RISCO_PERCENTUAL = False

# Estratégia
TIMEFRAME = "15m"               # 15m ou 1H são mais limpos que 5m
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
MA_PERIOD = 50

# Gerenciamento (em Spot não tem stop nativo da mesma forma)
STOP_LOSS_PERCENT = 2.0         # %
TAKE_PROFIT_PERCENT = 4.0       # %
MAX_POSICOES = 1

# Controle
INTERVALO_SEGUNDOS = 15
# =======================================================================
