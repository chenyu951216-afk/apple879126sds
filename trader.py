import ccxt
import os
import pandas as pd

class WeexBot:
    def __init__(self):
        self.exchange = ccxt.weex({
            'apiKey': os.getenv('WEEX_API_KEY'),
            'secret': os.getenv('WEEX_SECRET_KEY'),
            'password': os.getenv('WEEX_PASSPHRASE'),
            'options': {'defaultType': 'swap'}
        })

    def get_equity(self):
        bal = self.exchange.fetch_balance()
        return bal['total']['USDT']

    def execute_logic(self, symbol, side, price):
        # 1. 設置最大槓桿
        market = self.exchange.market(symbol)
        max_lev = int(market['info'].get('maxLeverage', 100))
        self.exchange.set_leverage(max_lev, symbol)

        # 2. 計算 5% 保證金倉位
        equity = self.get_equity()
        margin_used = equity * 0.05
        # 實際部位價值 = 保證金 * 槓桿
        notional_value = margin_used * max_lev
        amount = notional_value / price

        # 3. 科學止盈止損 (使用 1.5x 盈虧比與 ATR 動態調整)
        # 這裡簡化為固定比例，建議串接 engine.py 的 ATR 數值
        stop_loss = price * 0.98 if side == 'buy' else price * 1.02
        take_profit = price * 1.03 if side == 'buy' else price * 0.97

        order = self.exchange.create_market_order(symbol, side, amount, {
            'stopLoss': stop_loss,
            'takeProfit': take_profit
        })
        return order
