from ctrader.utils.rate_limiter import TokenBucket


def test_bucket():
    b = TokenBucket(rate=10, capacity=10)
    assert b.consume(5)
    assert not b.consume(20)
