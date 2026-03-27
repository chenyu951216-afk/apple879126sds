from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from trader import WeexBot
from engine import get_top_50, smc_scan
import asyncio, os

app = FastAPI()
bot = WeexBot()
templates = Jinja2Templates(directory="templates")

# 狀態追蹤
history = {"balance": 0, "logs": []}

async def trading_loop():
    while True:
        try:
            symbols = get_top_50(bot.exchange)
            for sym in symbols:
                ohlcv = bot.exchange.fetch_ohlcv(sym, '15m', limit=50)
                df = pd.DataFrame(ohlcv, columns=['ts','open','high','low','close','vol'])
                signal = smc_scan(df)
                
                if signal:
                    res = bot.execute_logic(sym, signal, df['close'].iloc[-1])
                    history["logs"].insert(0, f"成交: {sym} | 方向: {signal} | 價格: {df['close'].iloc[-1]}")
            
            history["balance"] = bot.get_equity()
            await asyncio.sleep(60) # 24小時循環掃描
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(10)

@app.on_event("startup")
async def start(): asyncio.create_task(trading_loop())

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "history": history})
    import os
import uvicorn

if __name__ == "__main__":
    # Zeabur 會自動分配 port，如果沒有則預設 8080
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
    import os
import uvicorn
from main_app import app # 假設你的 FastAPI 實例叫 app

if __name__ == "__main__":
    # 強制使用 Zeabur 提供的環境變數 PORT，預設為 80
    port = int(os.environ.get("PORT", 80))
    uvicorn.run("main:app", host="0.0.0.0", port=port, proxy_headers=True)
