import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.title("Nifty 200 Technical & Fundamental Analysis Scanner")

# Sample Nifty 200 ticker list (expand as needed)
nifty200_tickers = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "INFY.NS", "HINDUNILVR.NS", "KOTAKBANK.NS", "SBIN.NS",
    "ITC.NS", "BHARTIARTL.NS"
]

st.write(f"Scanning {len(nifty200_tickers)} stocks with detailed technical and fundamental analysis...")

results = []

for ticker in nifty200_tickers:
    try:
        data = yf.Ticker(ticker).history(period="60d")  # last 60 days
        if len(data) < 50:
            continue

        # Technical Indicators
        data['RSI'] = ta.rsi(data['Close'], length=14)
        macd = ta.macd(data['Close'])
        data['MACD'] = macd.iloc[:, 0]
        data['MACD_signal'] = macd.iloc[:, 1]
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['ATR'] = ta.atr(data['High'], data['Low'], data['Close'], length=14)

        latest = data.iloc[-1]

        # Technical buy signal conditions
        cond1 = latest['RSI'] < 30  # oversold
        cond2 = latest['MACD'] > latest['MACD_signal']  # MACD crossover
        cond3 = latest['SMA_20'] > latest['SMA_50']  # short SMA above long SMA

        score = sum([cond1, cond2, cond3])

        # Fundamental Analysis
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

        # Final combined filter
        if score >= 2 and funda_filter_pass:
            results.append({
                'Ticker': ticker,
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
                'Technical Score': score,
                'Fundamental Score': funda_score
            })

    except Exception as e:
        st.write(f"Skipped {ticker}: {str(e)}")

if results:
    df = pd.DataFrame(results)
    st.subheader("Stocks Passing Combined Technical & Fundamental Filters")
    st.dataframe(df)
else:
    st.write("No stocks passed the combined technical and fundamental criteria.")
