# Bitget Trading Bot

## Como usar a Conta Demo

### 1. Ative o modo Demo na Bitget
1. Entre na Bitget
2. No topo, clique em **Demo Trading** (ou Conta Demo)
3. A Bitget vai criar uma conta com saldo virtual

### 2. Crie uma API Key de Demo
1. Ainda no modo Demo, vá em **API Management**
2. Crie uma nova API Key
3. Marque permissão de **Trade**
4. Anote: API Key, Secret Key e Passphrase

### 3. Configure o `.env`
```
API_KEY=sua_chave_demo
SECRET_KEY=seu_secret_demo
PASSPHRASE=sua_senha_demo
```

### 4. Ative o modo Demo no bot
No arquivo `config.py`:
```python
MODO_DEMO = True
MODO_SIMULACAO = False
```

### 5. Rode
```bash
python bot.py
```

## Importante

- A API Key de **Demo** é diferente da API Key da conta real
- No modo Demo o bot usa o header `paptrading: 1`
- O saldo da Demo é virtual

## Modos

| Configuração | O que faz |
|---------------|-----------|
| `MODO_DEMO = True` | Usa conta Demo da Bitget |
| `MODO_SIMULACAO = True` | Não envia ordem (só mostra) |
| Ambos `False` | Opera na conta real |
