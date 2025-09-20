import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.title("Nifty Index Technical & Fundamental Scanner with Trade Levels")

# Define ticker lists for different Nifty indices (sample tickers for demo)
nifty_50_tickers = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
    "HINDUNILVR.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "SBIN.NS"
]

nifty_100_extra = [
    "ADANIPORTS.NS", "ASIANPAINT.NS", "BAJFINANCE.NS", "BHARTIARTL.NS"
]

nifty_200_extra = [
    "BRITANNIA.NS", "CIPLA.NS", "DRREDDY.NS", "EICHERMOT.NS"
]

nifty_500_extra = [
    "ABCAPITAL.NS", "APOLLOHOSP.NS", "BHEL.NS", "COALINDIA.NS"
]

# Combine for different indices
indices = {
    "Nifty 50": nifty_50_tickers,
    "Nifty 100": nifty_50_tickers + nifty_100_extra,
    "Nifty 200": nifty_50_tickers + nifty_100_extra + nifty_200_extra,
    "Nifty 500": nifty_50_tickers + nifty_100_extra + nifty_200_extra + nifty_500_extra
}

# User selectbox for index choice
index_choice = st.selectbox("Select Nifty index to scan:", list(indices.keys()))

tickers = indices[index_choice]

st.write(f"Scanning {len(tickers)} stocks from {index_choice} with detailed technical and fundamental analysis...")

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

        pe = info.get('trailingPE', None)
        pb = info.get('priceToBook', None)
        debt_equity = info.get('debtToEquity', None)
        roe = info.get('returnOnEquity', None)
        earnings_growth = info.get('earningsQuarterlyGrowth', None)

        pe_ok = pe is not None and pe < 30
        pb_ok = pb is not None and pb < 5
        debt_ok = debt_equity is not None and debt_equity < 1.5
        roe_ok = roe is not None and roe > 0.15
        growth_ok = earnings_growth is not None and earnings_growth > 0.05

        funda_score = sum([pe_ok, pb_ok, debt_ok, roe_ok, growth_ok])

        funda_filter_pass = funda_score >= 3

        if tech_score >= 2 and funda_filter_pass:
            cmp = latest['Close']
            buy_price = cmp
            target_sell_price = buy_price * 1.10
            stop_loss = buy_price * 0.97

            results.append({
                'Ticker': ticker,
                'CMP': round(cmp, 2),
                'Buy Price': round(buy_price, 2),
                'Target Sell Price': round(target_sell_price, 2),
                'Stop Loss': round(stop_loss, 2),
                'RSI': round(latest['RSI'], 2),
                'MACD': round(latest['MACD'], 3),
                'MACD_signal': round(latest['MACD_signal'], 3),
                'SMA_20': round(latest['SMA_20'], 2),
                'SMA_50': round(latest['SMA_50'], 2),
                'ATR': round(latest['ATR'], 2),
                'P/E': round(pe, 2) if pe else None,
                'P/B': round(pb, 2) if pb else None,
                'Debt/Equity': round(debt_equity, 2) if debt_equity else None,
                'ROE': round(roe, 2) if roe else None,
                'Earnings Growth': round(earnings_growth, 2) if earnings_growth else None,
                'Technical Score': tech_score,
                'Fundamental Score': funda_score
            })
    except Exception as e:
        st.write(f"Skipped {ticker}: {str(e)}")

if results:
    df = pd.DataFrame(results)
    st.subheader(f"Stocks Passing Filters in {index_choice}")
    st.dataframe(df)
else:
    st.write(f"No stocks passed the filters in {index_choice}.")
