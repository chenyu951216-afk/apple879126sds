import pandas as pd
import pandas_ta as ta

def get_top_50(ex):
    tickers = ex.fetch_tickers()
    usdt_pairs = [t for t in tickers.values() if '/USDT' in t['symbol'] and 'quoteVolume' in t]
    sorted_p = sorted(usdt_pairs, key=lambda x: x['quoteVolume'], reverse=True)
    return [p['symbol'] for p in sorted_p[:50]]

def smc_scan(df):
    """內建 SMC 指標模型：檢測 FVG 與 OB"""
    # 檢測 Fair Value Gap (FVG)
    df['fvg_up'] = (df['low'].shift(-1) > df['high'].shift(1))
    df['fvg_down'] = (df['high'].shift(-1) < df['low'].shift(1))
    
    # 簡單信號邏輯
    if df['fvg_up'].iloc[-2]: return 'buy'
    if df['fvg_down'].iloc[-2]: return 'sell'
    return None
