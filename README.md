# Bitget Trading Bot

Bot completo para BTCUSDT Spot com gestão de risco.

## Como conectar sua conta

### 1. Criar API Key na Bitget
1. Acesse [bitget.com](https://www.bitget.com) e faça login
2. Vá em **API Management**
3. Clique em **Create API**
4. Marque **apenas** a permissão de **Trade** (não marque Withdraw)
5. Guarde:
   - API Key
   - Secret Key
   - Passphrase

### 2. Configurar o bot
```bash
cp .env.example .env
```

Edite o arquivo `.env` e coloque suas chaves:
```
API_KEY=sua_chave
SECRET_KEY=seu_secret
PASSPHRASE=seu_passphrase
```

### 3. Instalar e rodar
```bash
pip install -r requirements.txt
python bot.py
```

## Modos

| Modo | Como ativar |
|------|-------------|
| Simulação | `MODO_SIMULACAO = True` no `config.py` |
| Real | `MODO_SIMULACAO = False` |

## Proteções

- Limite de perda diária: **3%**
- Kill switch: **8%**
- Stop Loss: **2%**
- Take Profit: **4%**
- Trailing Stop
- Cooldown de 30 min após perda

## Arquivos gerados

- `bot.log` → Histórico de tudo que o bot fez
- `relatorio_diario.txt` → Relatório do dia
- `estado_bot.json` → Estado atual (posição, saldo, etc.)
