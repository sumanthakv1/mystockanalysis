import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.title("Nifty 200 Technical Analysis Scanner")

nifty200_tickers = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "INFY.NS", "HINDUNILVR.NS", "KOTAKBANK.NS", "SBIN.NS",
    "ITC.NS", "BHARTIARTL.NS"
]

st.write(f"Scanning {len(nifty200_tickers)} stocks with detailed technical analysis...")

results = []

for ticker in nifty200_tickers:
    try:
        data = yf.Ticker(ticker).history(period="60d")  # last 60 days
        if len(data) < 50:
            continue
        
        # Calculate indicators
        data['RSI'] = ta.rsi(data['Close'], length=14)
        data['MACD'] = ta.macd(data['Close']).iloc[:,0]  # MACD line
        data['MACD_signal'] = ta.macd(data['Close']).iloc[:,1]  # Signal line
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['ATR'] = ta.atr(data['High'], data['Low'], data['Close'], length=14)

        # Latest values
        latest = data.iloc[-1]

        # Define simple buy conditions
        cond1 = latest['RSI'] < 30  # oversold RSI
        cond2 = latest['MACD'] > latest['MACD_signal']  # MACD crossover
        cond3 = latest['SMA_20'] > latest['SMA_50']  # short SMA above long SMA

        # Stock qualifies to watch if 2 of 3 conds true
        score = sum([cond1, cond2, cond3])
        if score >= 2:
            results.append({
                'Ticker': ticker,
                'RSI': round(latest['RSI'], 2),
                'MACD': round(latest['MACD'], 3),
                'MACD_signal': round(latest['MACD_signal'], 3),
                'SMA_20': round(latest['SMA_20'], 2),
                'SMA_50': round(latest['SMA_50'], 2),
                'ATR': round(latest['ATR'], 2),
                'Buy Signal Score': score
            })
        
    except Exception as e:
        st.write(f"Skipped {ticker}: {str(e)}")

if results:
    df = pd.DataFrame(results)
    st.subheader("Stocks passing buy signal criteria")
    st.dataframe(df)
else:
    st.write("No stocks passing the buy signal criteria found.")
