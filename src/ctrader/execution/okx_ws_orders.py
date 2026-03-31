from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import AsyncIterator

import websockets


@dataclass
class OKXWSConfig:
    api_key: str
    secret_key: str
    passphrase: str
    ws_url: str = "wss://ws.okx.com:8443/ws/v5/private"
    simulated: bool = True


class OKXOrderStream:
    """Private WS order stream (skeleton): login + subscribe orders channel."""

    def __init__(self, cfg: OKXWSConfig):
        self.cfg = cfg

    @staticmethod
    def _sign(secret_key: str, ts: str, method: str, path: str) -> str:
        msg = f"{ts}{method}{path}".encode()
        return base64.b64encode(hmac.new(secret_key.encode(), msg, hashlib.sha256).digest()).decode()

    async def stream_orders(self) -> AsyncIterator[dict]:
        headers = {}
        if self.cfg.simulated:
            headers["x-simulated-trading"] = "1"

        async with websockets.connect(self.cfg.ws_url, additional_headers=headers) as ws:
            ts = str(int(time.time()))
            sign = self._sign(self.cfg.secret_key, ts, "GET", "/users/self/verify")
            login = {
                "op": "login",
                "args": [{"apiKey": self.cfg.api_key, "passphrase": self.cfg.passphrase, "timestamp": ts, "sign": sign}],
            }
            await ws.send(json.dumps(login))
            await ws.recv()  # login ack

            await ws.send(json.dumps({"op": "subscribe", "args": [{"channel": "orders", "instType": "ANY"}]}))

            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                yield data
                await asyncio.sleep(0)
