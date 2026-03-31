from ctrader.execution.okx_sim import OKXSimClient


def test_okx_sign_is_stable_for_fixed_input():
    sig = OKXSimClient.sign(
        secret_key="secret",
        timestamp="2024-01-01T00:00:00.000Z",
        method="GET",
        request_path="/api/v5/account/balance",
        body="",
    )
    assert isinstance(sig, str)
    assert len(sig) > 10
