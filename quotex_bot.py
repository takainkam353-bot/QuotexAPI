import os
import asyncio
import pandas as pd
import ta
from quotexpy import Quotex
from quotexpy.utils.account_type import AccountType
from quotexpy.utils.operation_type import OperationType

# Koyeb সার্ভারের এনভায়রনমেন্ট ভ্যারিয়েবল থেকে আইডি-পাসওয়ার্ড আসবে
QUOTEX_EMAIL = os.environ.get("QUOTEX_EMAIL")
QUOTEX_PASSWORD = os.environ.get("QUOTEX_PASSWORD")
TRADE_ASSET = "EURUSD"      
TRADE_AMOUNT = 10.0         
TRADE_DURATION = 60         

def on_pin_code() -> str:
    print("⚠️ Please enter OTP pin in Koyeb console:")
    code = input()
    return code

async def get_market_data(client, asset):
    candles = client.get_candles(asset, 60, 30)
    df = pd.DataFrame(candles)
    df['close'] = df['close'].astype(float)
    return df

async def rsi_strategy(df):
    rsi_indicator = ta.momentum.RSIIndicator(close=df['close'], window=14)
    df['rsi'] = rsi_indicator.rsi()
    latest_rsi = df['rsi'].iloc[-1]
    
    if latest_rsi < 30:
        return OperationType.CALL
    elif latest_rsi > 70:
        return OperationType.PUT
    return None

async def main():
    if not QUOTEX_EMAIL or not QUOTEX_PASSWORD:
        print("❌ Error: Environment variables NOT set properly!")
        return

    print("🔄 Connecting to Quotex...")
    client = Quotex(email=QUOTEX_EMAIL, password=QUOTEX_PASSWORD, headless=True, on_pin_code=on_pin_code)
    client.change_account(AccountType.DEMO)
    print(f"✅ Connected! Demo Balance: ${client.get_balance()}")

    try:
        while True:
            df = await get_market_data(client, TRADE_ASSET)
            signal = await rsi_strategy(df)
            
            if signal == OperationType.CALL:
                client.buy(TRADE_ASSET, TRADE_AMOUNT, OperationType.CALL, TRADE_DURATION)
                print("🚀 CALL Trade Placed!")
            elif signal == OperationType.PUT:
                client.buy(TRADE_ASSET, TRADE_AMOUNT, OperationType.PUT, TRADE_DURATION)
                print("📉 PUT Trade Placed!")
                
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("Stopped.")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
