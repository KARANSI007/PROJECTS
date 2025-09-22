import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
import matplotlib.pyplot as plt

# ==============================
# 1. Parameters
# ==============================
TICKERS = ["AAPL", "MSFT", "GOOG"]  # add more tickers if needed
INTERVAL = "1m"      # 1-minute bars
LOOKBACK = "5d"      # last 5 days of data
RISK_PER_TRADE = 0.01
INITIAL_CAPITAL = 10000

# Initialize account & positions
account = {
    "cash": INITIAL_CAPITAL,
    "positions": {ticker: {"shares": 0, "entry_price": None, "stop": None, "take": None} for ticker in TICKERS},
    "trades": [],
    "equity_curve": []
}

# ==============================
# 2. Risk Management Functions
# ==============================
def compute_atr(df, period=14):
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr

def compute_sl_tp(entry_price, atr, sl_atr=2.0, tp_multiplier=2.0):
    stop_price = entry_price - atr * sl_atr
    take_price = entry_price + atr * sl_atr * tp_multiplier
    return stop_price, take_price

def position_size(cash, risk_per_trade, entry_price, stop_price):
    risk_amount = cash * risk_per_trade
    stop_distance = abs(entry_price - stop_price)
    if stop_distance == 0:
        return 0
    shares = int(risk_amount / stop_distance)
    return max(shares, 0)

# ==============================
# 3. Check signals & execute trades
# ==============================
def check_signals(ticker):
    global account
    df = yf.download(ticker, period=LOOKBACK, interval=INTERVAL)
    df = df.dropna()
    if len(df) < 50:
        return None, None, None, None

    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["ATR14"] = compute_atr(df)

    last = df.iloc[-1]
    prev = df.iloc[-2]
    price = last["Close"]
    atr = last["ATR14"]

    # Generate signal
    signal = None
    if last["SMA20"] > last["SMA50"] and prev["SMA20"] <= prev["SMA50"]:
        signal = "buy"
    elif last["SMA20"] < last["SMA50"] and prev["SMA20"] >= prev["SMA50"]:
        signal = "sell"

    return signal, price, atr, last.name

def execute_trade(ticker, signal, price, atr, time_idx):
    global account
    pos = account["positions"][ticker]
    cash = account["cash"]

    # Check SL/TP first
    if pos["shares"] > 0:
        if price <= pos["stop"]:
            pnl = (price - pos["entry_price"]) * pos["shares"]
            account["trades"].append({"ticker": ticker, "entry_price": pos["entry_price"], "exit_price": price,
                                      "shares": pos["shares"], "pnl": pnl, "exit_time": time_idx})
            account["cash"] += price * pos["shares"]
            print(f"[{datetime.now()}] {ticker} STOP LOSS hit at {price:.2f}, PnL: {pnl:.2f}")
            account["positions"][ticker] = {"shares":0,"entry_price":None,"stop":None,"take":None}
        elif price >= pos["take"]:
            pnl = (price - pos["entry_price"]) * pos["shares"]
            account["trades"].append({"ticker": ticker, "entry_price": pos["entry_price"], "exit_price": price,
                                      "shares": pos["shares"], "pnl": pnl, "exit_time": time_idx})
            account["cash"] += price * pos["shares"]
            print(f"[{datetime.now()}] {ticker} TAKE PROFIT hit at {price:.2f}, PnL: {pnl:.2f}")
            account["positions"][ticker] = {"shares":0,"entry_price":None,"stop":None,"take":None}

    # Enter trade if no position
    if pos["shares"] == 0 and signal == "buy" and not np.isnan(atr):
        stop_price, take_price = compute_sl_tp(price, atr)
        shares = position_size(account["cash"], RISK_PER_TRADE, price, stop_price)
        if shares > 0:
            account["positions"][ticker] = {"shares": shares, "entry_price": price, "stop": stop_price, "take": take_price}
            account["cash"] -= price * shares
            account["trades"].append({"ticker": ticker, "entry_price": price, "exit_price": None, "shares": shares, "entry_time": time_idx})
            print(f"[{datetime.now()}] BUY {ticker} {shares} shares at {price:.2f} | Stop: {stop_price:.2f} | Take: {take_price:.2f}")

# ==============================
# 4. Run the simulation loop
# ==============================
if __name__ == "__main__":
    print("Starting multi-ticker paper trading simulation...")
    try:
        while True:
            for ticker in TICKERS:
                signal, price, atr, time_idx = check_signals(ticker)
                if signal:
                    execute_trade(ticker, signal, price, atr, time_idx)

            # Calculate total equity
            total_equity = account["cash"] + sum(account["positions"][t]["shares"]*price for t in TICKERS)
            account["equity_curve"].append({"time": datetime.now(), "equity": total_equity})
            time.sleep(60)  # wait 1 minute before next check

    except KeyboardInterrupt:
        print("Simulation stopped by user.")
        print(f"Final Cash: {account['cash']:.2f}")
        for t in TICKERS:
            pos = account["positions"][t]
            if pos["shares"] > 0:
                print(f"Open position {t}: {pos['shares']} shares at {pos['entry_price']:.2f}")

        # Print trades
        print("Trades executed:")
        for trade in account["trades"]:
            print(trade)

        # Plot equity curve
        equity_df = pd.DataFrame(account["equity_curve"]).set_index("time")
        plt.figure(figsize=(10,5))
        plt.plot(equity_df.index, equity_df["equity"], label="Equity Curve")
        plt.title("Multi-Ticker Paper Trading Equity Curve")
        plt.xlabel("Time")
        plt.ylabel("Equity ($)")
        plt.legend()
        plt.show()
