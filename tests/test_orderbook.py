from ctrader.data.orderbook import OrderBookL2


def test_snapshot_delta():
    ob = OrderBookL2()
    ob.apply_snapshot([(100, 1), (99, 2)], [(101, 1.5)])
    ob.apply_delta([(100, 0), (98, 3)], [(101, 2)])
    assert ob.best_bid()[0] == 99
    assert ob.best_ask()[0] == 101
