import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.title("Nifty Scanner: Breakout & 1:3 Risk-Reward Stocks")

# Sample Nifty universes (expand as needed)
nifty_50 = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
            "ICICIBANK.NS", "HINDUNILVR.NS", "KOTAKBANK.NS", "SBIN.NS",
            "ITC.NS", "BHARTIARTL.NS"]

nifty_100_extra = ["BAJFINANCE.NS", "ADANIPORTS.NS", "ASIANPAINT.NS",
                   "ULTRACEMCO.NS", "MARUTI.NS"]

nifty_200_extra = ["CIPLA.NS", "EICHERMOT.NS", "BRITANNIA.NS",
                   "DRREDDY.NS", "TITAN.NS"]

indices = {
    "Nifty 50": nifty_50,
    "Nifty 100": nifty_50 + nifty_100_extra,
    "Nifty 200": nifty_50 + nifty_100_extra + nifty_200_extra
}

universe = st.selectbox("Select Nifty Universe to Scan:", list(indices.keys()))
tickers = indices[universe]

def calculate_breakout_features(ticker):
    try:
        data = yf.Ticker(ticker).history(period="60d")
        if len(data) < 50:
            return None

        data['20d_High'] = data['High'].rolling(window=20).max().shift(1)
        data['50d_High'] = data['High'].rolling(window=50).max().shift(1)
        data['20d_Vol_Avg'] = data['Volume'].rolling(window=20).mean().shift(1)

        latest = data.iloc[-1]

        breakout_20d = latest['Close'] > latest['20d_High']
        breakout_50d = latest['Close'] > latest['50d_High']
        volume_spike = latest['Volume'] > 1.5 * latest['20d_Vol_Avg']

        rsi = ta.rsi(data['Close'], length=14).iloc[-1]
        macd = ta.macd(data['Close'])
        macd_line = macd.iloc[:, 0].iloc[-1]
        macd_signal = macd.iloc[:, 1].iloc[-1]
        macd_cross = macd_line > macd_signal

        breakout_score = sum([breakout_20d, breakout_50d, volume_spike, rsi > 60, macd_cross])

        # Fundamental filters
        info = yf.Ticker(ticker).info
        pe = info.get('trailingPE')
        pb = info.get('priceToBook')
        debt_equity = info.get('debtToEquity')
        roe = info.get('returnOnEquity')
        earnings_growth = info.get('earningsQuarterlyGrowth')

        pe_ok = pe is not None and pe < 30
        pb_ok = pb is not None and pb < 5
        debt_ok = debt_equity is not None and debt_equity < 1.5
        roe_ok = roe is not None and roe > 0.15
        growth_ok = earnings_growth is not None and earnings_growth > 0.05

        funda_score = sum([pe_ok, pb_ok, debt_ok, roe_ok, growth_ok])

        if breakout_score >= 3 and funda_score >= 3:
            # Calculate risk-reward trade levels
            atr = ta.atr(data['High'], data['Low'], data['Close'], length=14).iloc[-1]
            buy_price = latest['Close']
            stop_loss = buy_price - atr
            if stop_loss <= 0:
                return None
            risk = buy_price - stop_loss
            target_sell_price = buy_price + 3 * risk
            risk_reward_ratio = (target_sell_price - buy_price) / risk

            if risk_reward_ratio >= 3:
                return {
                    'Ticker': ticker,
                    'CMP': round(buy_price, 2),
                    'Buy Price': round(buy_price, 2),
                    'Stop Loss': round(stop_loss, 2),
                    'Target Sell Price': round(target_sell_price, 2),
                    'Risk-Reward Ratio': round(risk_reward_ratio, 2),
                    'Breakout Score': breakout_score,
                    'Fundamental Score': funda_score,
                    'RSI': round(rsi, 2),
                    'MACD Cross': macd_cross,
                    'ATR': round(atr, 2),
                    'P/E': round(pe, 2) if pe else None,
                    'P/B': round(pb, 2) if pb else None,
                    'Debt/Equity': round(debt_equity, 2) if debt_equity else None,
                    'ROE': round(roe, 2) if roe else None,
                    'Earnings Growth': round(earnings_growth, 2) if earnings_growth else None
                }
        return None
    except:
        return None

results = []
progress_bar = st.progress(0)
total = len(tickers)

for i, ticker in enumerate(tickers):
    res = calculate_breakout_features(ticker)
    if res:
        results.append(res)
    progress_bar.progress((i+1)/total)

if results:
    df = pd.DataFrame(results)
    st.subheader(f"Stocks with Breakout & 1:3 Risk-Reward Ratio in {universe}")
    st.dataframe(df.sort_values(by='Risk-Reward Ratio', ascending=False).reset_index(drop=True))
else:
    st.write("No stocks matched the breakout and risk-reward criteria.")
