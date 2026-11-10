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

    # ---------- Market (Spot) ----------
    def get_candles(self, symbol, granularity, limit=100):
        path = "/api/v2/spot/market/candles"
        params = {"symbol": symbol, "granularity": granularity, "limit": limit}
        return self.request("GET", path, params=params)

    def get_ticker(self, symbol):
        path = "/api/v2/spot/market/tickers"
        params = {"symbol": symbol}
        return self.request("GET", path, params=params)

    # ---------- Account (Spot) ----------
    def get_account(self):
        path = "/api/v2/spot/account/assets"
        return self.request("GET", path)

    # ---------- Trade (Spot) ----------
    def place_order(self, symbol, side, size, order_type="market"):
        path = "/api/v2/spot/trade/place-order"
        body = {
            "symbol": symbol,
            "side": side,               # buy ou sell
            "orderType": order_type,
            "force": "gtc",
            "size": str(size)
        }
        return self.request("POST", path, body=body)

    def get_open_orders(self, symbol):
        path = "/api/v2/spot/trade/unfilled-orders"
        params = {"symbol": symbol}
        return self.request("GET", path, params=params)
