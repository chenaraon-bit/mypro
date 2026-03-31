from ctrader.execution.paper import PaperBroker


def test_paper_broker_buy_sell_cycle():
    b = PaperBroker(starting_cash=1000, fee_bps=0)
    b.place_market_order("t1", "BTCUSDT", "BUY", qty=1, price=100)
    b.place_market_order("t2", "BTCUSDT", "SELL", qty=1, price=110)
    assert b.realized_pnl == 10
    assert b.positions["BTCUSDT"] == 0
    assert b.cash == 1010
