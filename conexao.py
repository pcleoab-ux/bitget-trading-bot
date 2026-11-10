from bitget_client import BitgetClient
from config import API_KEY, SECRET_KEY, PASSPHRASE, SYMBOL

def testar_conexao():
    """Testa se as chaves da API estão válidas."""
    if not API_KEY or not SECRET_KEY or not PASSPHRASE:
        return False, "Chaves não configuradas. Crie o arquivo .env"

    try:
        client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)
        # Testa uma chamada simples
        resp = client.get_account()
        if resp.get("code") == "00000":
            return True, "Conexão OK"
        else:
            return False, f"Erro da API: {resp.get('msg', 'desconhecido')}"
    except Exception as e:
        return False, f"Erro de conexão: {str(e)}"

def obter_saldo():
    try:
        client = BitgetClient(API_KEY, SECRET_KEY, PASSPHRASE)
        resp = client.get_account()
        if resp.get("code") != "00000":
            return 0
        for asset in resp.get("data", []):
            if asset.get("coin") == "USDT":
                return float(asset.get("available", 0))
        return 0
    except:
        return 0
