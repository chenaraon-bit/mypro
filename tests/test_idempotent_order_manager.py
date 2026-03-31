from ctrader.execution.idempotent import IdempotentOrderManager


class DummyClient:
    def __init__(self):
        self.calls = 0

    def place_order(self, **kwargs):
        self.calls += 1
        return {"ok": True, "kwargs": kwargs}


def test_clord_id_and_retry_wrapper():
    client = DummyClient()
    om = IdempotentOrderManager(client=client)
    out = om.place_order_with_retry(inst_id="BTC-USDT", side="buy", ord_type="market", sz="0.001")
    assert out["ok"] is True
    assert "cl_ord_id" in out["kwargs"]
    assert client.calls == 1
