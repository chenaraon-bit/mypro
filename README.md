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


## 可以接入模拟盘吗？

可以。当前仓库已提供本地模拟盘执行器 `PaperBroker` 与运行脚本：

```bash
export PYTHONPATH=src
python scripts/run_paper_trading.py --csv your_ohlcv.csv --symbol BTCUSDT
```

说明：
- 这是**本地 paper account**（不发真实订单），可先验证信号、仓位与资金曲线。
- 下一步可把 `PaperBroker` 替换为交易所 testnet 适配器（例如 Binance/Bybit testnet REST+WS）。



## OKX 模拟盘接入（Demo）

已新增 `OKXSimClient` 与脚本：

```bash
export PYTHONPATH=src
export OKX_API_KEY=你的key
export OKX_SECRET_KEY=你的secret
export OKX_PASSPHRASE=你的passphrase
python scripts/okx_sim_trade.py --inst-id BTC-USDT --side buy --ord-type market --sz 0.001
```

安全建议：
- **不要**在代码中硬编码 API Key/Secret。
- API 权限建议只开“读取/交易”，**不要开启提現权限**。
- 如果你曾在聊天中暴露密钥，请立即在交易所后台删除并重建。

