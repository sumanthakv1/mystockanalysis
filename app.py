import streamlit as st
import yfinance as yf
import pandas as pd

st.title("Nifty 200 Weekly Gainers (>10%) Scanner")

# A sample list of Nifty 200 tickers
# You can expand this list with the full Nifty 200 tickers
nifty200_tickers = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "INFY.NS", "HINDUNILVR.NS", "KOTAKBANK.NS", "SBIN.NS",
    "ITC.NS", "BHARTIARTL.NS"
]

st.write(f"Scanning {len(nifty200_tickers)} Nifty 200 stocks...")

gainers = []

for ticker in nifty200_tickers:
    try:
        data = yf.Ticker(ticker).history(period="8d", interval="1d")  # last 8 days of daily data
        if len(data) < 6:
            continue  # skip if data is insufficient

        start_price = data['Close'][0]
        end_price = data['Close'][-1]
        pct_change = (end_price - start_price) / start_price * 100

        if pct_change >= 10:
            gainers.append({
                "Ticker": ticker,
                "Start Price": round(start_price, 2),
                "End Price": round(end_price, 2),
                "Weekly % Gain": round(pct_change, 2)
            })
    except Exception as e:
        st.write(f"Skipped {ticker} due to error: {str(e)}")

if gainers:
    df = pd.DataFrame(gainers)
    st.subheader("Stocks with ≥10% Weekly Gain")
    st.dataframe(df)
else:
    st.write("No Nifty 200 stocks gained 10% or more in the last week.")
