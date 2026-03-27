import ccxt
import os
import pandas as pd

class WeexBot:
    def __init__(self):
        # 建立 WEEX 實例，確保 API 金鑰透過環境變數傳入
        # 若 ccxt 版本低於 4.2.0，請務必更新 requirements.txt
        api_config = {
            'apiKey': os.getenv('WEEX_API_KEY'),
            'secret': os.getenv('WEEX_SECRET_KEY'),
            'password': os.getenv('WEEX_PASSPHRASE'),
            'options': {
                'defaultType': 'swap',  # 強制使用 U 本組合約
                'adjustForTimeDifference': True # 自動同步時間伺服器預防 401 錯誤
            }
        }
        
        if hasattr(ccxt, 'weex'):
            self.exchange = ccxt.weex(api_config)
        else:
            # 兼容舊版邏輯 (建議仍要更新 ccxt)
            raise ImportError("請更新 ccxt 版本至最新 (pip install ccxt --upgrade) 以支援 WEEX 交易所")

    def get_equity(self):
        """獲取總資產餘額 (USDT)"""
        try:
            bal = self.exchange.fetch_balance()
            return float(bal['total']['USDT'])
        except Exception as e:
            print(f"獲取餘額失敗: {e}")
            return 0.0

    def execute_logic(self, symbol, side, price, atr=None):
        """
        執行交易邏輯：
        1. 強制開最大槓桿
        2. 投入總資產 5% 保證金
        3. 設置科學止盈止損 (預設 1.5x 盈虧比或 ATR)
        """
        try:
            # 加載市場數據，確保能獲取最大槓桿資訊
            markets = self.exchange.load_markets()
            if symbol not in markets:
                print(f"找不到交易對: {symbol}")
                return None

            # 1. 設置最大槓桿
            market = self.exchange.market(symbol)
            # WEEX 的最大槓桿通常在 info 裡的 maxLeverage
            max_lev = int(market['info'].get('maxLeverage', 100))
            
            try:
                self.exchange.set_leverage(max_lev, symbol)
            except Exception as e:
                print(f"槓桿設置警告 (可能已設置): {e}")

            # 2. 計算 5% 保證金對應的開倉數量
            equity = self.get_equity()
            if equity <= 0: return None
            
            margin_per_trade = equity * 0.05
            # 部位總價值 = 保證金 * 槓桿
            notional_value = margin_per_trade * max_lev
            amount = notional_value / price

            # 3. 科學止盈止損
            # 如果有 ATR 資料則使用 ATR * 2 作為止損，否則使用固定百分比 (2%)
            sl_percent = (atr * 2 / price) if atr else 0.02
            tp_percent = sl_percent * 1.5 # 1.5 倍盈虧比

            if side == 'buy':
                stop_loss = price * (1 - sl_percent)
                take_profit = price * (1 + tp_percent)
            else:
                stop_loss = price * (1 + sl_percent)
                take_profit = price * (1 - tp_percent)

            # 4. 送出市價單並帶入止盈止損 (WEEX params 格式)
            # 注意：某些交易所需要將 SL/TP 分開下單，這裡使用 ccxt 標準 params
            params = {
                'stopLoss': {'stopPrice': stop_loss},
                'takeProfit': {'stopPrice': take_profit}
            }
            
            print(f"正在開倉: {symbol} | 方向: {side} | 槓桿: {max_lev} | 投入保證金: {margin_per_trade} USDT")
            
            order = self.exchange.create_market_order(
                symbol=symbol, 
                side=side, 
                amount=amount, 
                params=params
            )
            return order

        except Exception as e:
            print(f"執行交易失敗: {e}")
            return None
