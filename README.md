# Bitget Trading Bot

Bot completo de trading autônomo para a **Bitget** usando a API oficial.

## Estratégia

- RSI + Média Móvel
- Compra quando RSI < 30 e preço acima da média
- Vende quando RSI > 70 e preço abaixo da média
- Gerenciamento de risco configurável

## Como usar

### 1. Criar API Key na Bitget
1. Acesse [Bitget](https://www.bitget.com)
2. Vá em **API Management**
3. Crie uma chave com permissão de **Trade**
4. Guarde: API Key, Secret Key e Passphrase

### 2. Configurar
Edite o arquivo `config.py` e coloque suas chaves:

```python
API_KEY = "sua_api_key"
SECRET_KEY = "seu_secret_key"
PASSPHRASE = "seu_passphrase"
```

### 3. Instalar e rodar

```bash
pip install -r requirements.txt
python bot.py
```

## Parar o bot
Pressione `Ctrl + C`

## Aviso
Use primeiro com valores pequenos ou em conta de teste. Trading automatizado envolve risco.

## Estrutura

```
config.py          → Configurações
bitget_client.py   → Cliente da API
bot.py             → Lógica principal
requirements.txt
```
