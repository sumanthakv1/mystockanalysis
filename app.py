import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.title("Nifty & NSE Universe Scanner with Technical and Fundamental Analysis")

# Sample ticker lists for various Nifty categories (expand as necessary)
nifty_50 = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
            "ICICIBANK.NS", "HINDUNILVR.NS", "KOTAKBANK.NS", "SBIN.NS",
            "ITC.NS", "BHARTIARTL.NS"]

nifty_100_extra = ["BAJFINANCE.NS", "ADANIPORTS.NS", "ASIANPAINT.NS", "ULTRACEMCO.NS", "MARUTI.NS"]

nifty_200_extra = ["CIPLA.NS", "EICHERMOT.NS", "BRITANNIA.NS", "DRREDDY.NS", "TITAN.NS"]

nifty_500_extra = ["APOLLOHOSP.NS", "BHEL.NS", "COALINDIA.NS", "GRASIM.NS", "HCLTECH.NS"]

nifty_1000_extra = ["INDIGO.NS", "MUTHOOTFIN.NS", "PAGEIND.NS", "TATAMOTORS.NS", "ZEEL.NS"]

nifty_all_extra = ["REPCOHOME.NS", "SAIL.NS", "WIPRO.NS", "YESBANK.NS", "ZOMATO.NS"]

indices = {
    "Nifty 50": nifty_50,
    "Nifty 100": nifty_50 + nifty_100_extra,
    "Nifty 200": nifty_50 + nifty_100_extra + nifty_200_extra,
    "Nifty 500": nifty_50 + nifty_100_extra + nifty_200_extra + nifty_500_extra,
    "Nifty 1000": nifty_50 + nifty_100_extra + nifty_200_extra + nifty_500_extra + nifty_1000_extra,
    "NSE All": nifty_50 + nifty_100_extra + nifty_200_extra + nifty_500_extra + nifty_1000_extra + nifty_all_extra,
}

universe = st.selectbox("Select Nifty universe to scan:", list(indices.keys()))

tickers = indices[universe]

st.write(f"Scanning {len(tickers)} stocks from {universe}...")

results = []

for ticker in tickers:
    try:
        data = yf.Ticker(ticker).history(period="60d")
        if len(data) < 50:
            continue

        data['RSI'] = ta.rsi(data['Close'], length=14)
        macd = ta.macd(data['Close'])
        data['MACD'] = macd.iloc[:, 0]
        data['MACD_signal'] = macd.iloc[:, 1]
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['ATR'] = ta.atr(data['High'], data['Low'], data['Close'], length=14)

        latest = data.iloc[-1]

        cond1 = latest['RSI'] < 30
        cond2 = latest['MACD'] > latest['MACD_signal']
        cond3 = latest['SMA_20'] > latest['SMA_50']

        tech_score = sum([cond1, cond2, cond3])

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

        if tech_score >= 2 and funda_score >= 3:
            cmp = latest['Close']
            buy_price = cmp
            target_sell_price = buy_price * 1.10
            stop_loss = buy_price * 0.97

            results.append({
                "Ticker": ticker,
                "CMP": round(cmp, 2),
                "Buy Price": round(buy_price, 2),
                "Target Sell Price": round(target_sell_price, 2),
                "Stop Loss": round(stop_loss, 2),
                "RSI": round(latest['RSI'], 2),
                "MACD": round(latest['MACD'], 3),
                "MACD_signal": round(latest['MACD_signal'], 3),
                "SMA_20": round(latest['SMA_20'], 2),
                "SMA_50": round(latest['SMA_50'], 2),
                "ATR": round(latest['ATR'], 2),
                "P/E": round(pe, 2) if pe else None,
                "P/B": round(pb, 2) if pb else None,
                "Debt/Equity": round(debt_equity, 2) if debt_equity else None,
                "ROE": round(roe, 2) if roe else None,
                "Earnings Growth": round(earnings_growth, 2) if earnings_growth else None,
                "Technical Score": tech_score,
                "Fundamental Score": funda_score
            })

    except Exception as e:
        st.write(f"Skipped {ticker} due to error: {e}")

if results:
    st.subheader(f"Stocks passing screening in {universe}")
    st.dataframe(pd.DataFrame(results))
else:
    st.write(f"No stocks passed the screening criteria from {universe} currently.")
