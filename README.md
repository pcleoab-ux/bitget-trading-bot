# Bitget Bot — Análise Completa (BTCUSDT Spot)

Bot com análise multi-indicador para **BTCUSDT Spot** na Bitget.

## Indicadores usados

| Indicador | O que analisa |
|-----------|---------------|
| RSI | Sobrecompra / Sobrevenda |
| EMA 12/26 | Tendência |
| MACD | Cruzamentos de momentum |
| Bollinger Bands | Extremos de preço |
| Volume | Confirmação de movimento |

## Sistema de Score

O bot só opera quando **pelo menos 3 sinais** confirmam a mesma direção.

Exemplo de compra:
- RSI < 35
- EMA12 acima da EMA26
- Cruzamento MACD de alta

## Como usar

```bash
pip install -r requirements.txt
python bot.py
```

## Estrutura

```
bot.py          → Loop principal
analise.py      → Motor de análise completo
bitget_client.py
config.py
```
