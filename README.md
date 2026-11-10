# Bitget Trading Bot — BTCUSDT Spot

Bot focado em **BTCUSDT Spot** na Bitget (a operação mais fácil de analisar).

## Por que Spot?

- Sem liquidação
- Sem funding rate
- Gráfico mais limpo
- Indicadores funcionam melhor
- Menor risco para começar

## Estratégia

- RSI + Média Móvel
- Compra quando RSI < 30 e preço acima da média
- Vende quando RSI > 70 e preço abaixo da média
- Timeframe recomendado: **15m** ou **1H**

## Como usar

1. Crie uma API Key na Bitget com permissão de **Trade**
2. Edite `config.py` e coloque suas chaves
3. Rode:

```bash
pip install -r requirements.txt
python bot.py
```

## Parar o bot
Pressione `Ctrl + C`

## Aviso
Use primeiro com valores pequenos. Trading automatizado envolve risco.
