# Crypto Trader Prototype (Engineering-Oriented)

按你的思路，这版代码已升级为工程化原型结构：

- `src/ctrader/data`: 交易所数据接口与订单簿重建
- `src/ctrader/backtest`: 事件、经纪商撮合、指标
- `src/ctrader/strategies`: 均值回归、资金费率套利信号
- `src/ctrader/ml`: Purged CV、DSR/PBO接口
- `src/ctrader/utils`: TokenBucket 限速器
- `scripts/`: 运行脚本
- `tests/`: 单元测试

## 快速运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
python scripts/run_backtest_mean_reversion.py --csv your_ohlcv.csv
```

CSV至少包含：`timestamp, open, high, low, close, volume`。

## 当前实现边界

- 已实现：bar级事件回测、成本模型、回撤熔断、两类策略信号、Purged CV/PBO接口、订单簿snapshot+delta。
- 未完全实现：真实交易所私有WS对账、复杂排队成交模型、严格CPCV版PBO。

建议下一步：补上实时适配器、审计日志、影子模式与金丝雀执行器。
