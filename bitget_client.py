import hmac
import base64
import json
import time
import requests
from hashlib import sha256

class BitgetClient:
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.base_url = "https://api.bitget.com"

    def _sign(self, timestamp, method, request_path, body=""):
        message = timestamp + method.upper() + request_path + body
        mac = hmac.new(self.secret_key.encode("utf-8"), message.encode("utf-8"), digestmod=sha256)
        return base64.b64encode(mac.digest()).decode()

    def _headers(self, method, request_path, body=""):
        timestamp = str(int(time.time() * 1000))
        sign = self._sign(timestamp, method, request_path, body)
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": sign,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US"
        }

    def request(self, method, path, params=None, body=None):
        url = self.base_url + path
        body_str = json.dumps(body) if body else ""
        headers = self._headers(method, path, body_str)

        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        else:
            response = requests.post(url, headers=headers, data=body_str)

        return response.json()

    # ---------- Market ----------
    def get_candles(self, symbol, granularity, limit=100):
        path = "/api/v2/mix/market/candles"
        params = {"symbol": symbol, "granularity": granularity, "limit": limit}
        return self.request("GET", path, params=params)

    def get_ticker(self, symbol):
        path = "/api/v2/mix/market/ticker"
        params = {"symbol": symbol}
        return self.request("GET", path, params=params)

    # ---------- Account ----------
    def get_account(self, symbol, product_type="USDT-FUTURES"):
        path = "/api/v2/mix/account/account"
        params = {"symbol": symbol, "productType": product_type, "marginCoin": "USDT"}
        return self.request("GET", path, params=params)

    def get_positions(self, product_type="USDT-FUTURES"):
        path = "/api/v2/mix/position/all-position"
        params = {"productType": product_type, "marginCoin": "USDT"}
        return self.request("GET", path, params=params)

    # ---------- Trade ----------
    def place_order(self, symbol, side, size, order_type="market", product_type="USDT-FUTURES"):
        path = "/api/v2/mix/order/place-order"
        body = {
            "symbol": symbol,
            "productType": product_type,
            "marginMode": "crossed",
            "marginCoin": "USDT",
            "size": str(size),
            "side": side,               # buy ou sell
            "tradeSide": "open",
            "orderType": order_type,
            "force": "gtc"
        }
        return self.request("POST", path, body=body)

    def close_position(self, symbol, hold_side, product_type="USDT-FUTURES"):
        path = "/api/v2/mix/order/close-positions"
        body = {
            "symbol": symbol,
            "productType": product_type,
            "holdSide": hold_side
        }
        return self.request("POST", path, body=body)
