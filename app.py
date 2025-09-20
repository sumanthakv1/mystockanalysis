import streamlit as st
import yfinance as yf
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Title and subtitle
st.title("Advanced AI Stock Analysis Utility")
st.write("Enter a stock ticker (e.g., TCS.NS for Tata Consultancy Services).")

# Input field for ticker symbol
ticker = st.text_input("Stock ticker")

if ticker:
    try:
        # Download historical stock price data (last 3 months)
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")

        st.subheader(f"{ticker} Closing Prices")
        st.line_chart(hist['Close'])

        # Calculate simple moving averages
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()

        st.subheader("20 & 50 Day Simple Moving Averages (SMA)")
        st.line_chart(hist[['Close', 'SMA_20', 'SMA_50']])

        # Display basic company fundamental data
        st.subheader("Basic Company Info")
        info = stock.info
        st.write(f"**Market Cap:** {info.get('marketCap', 'N/A')}")
        st.write(f"**Trailing P/E:** {info.get('trailingPE', 'N/A')}")
        st.write(f"**Forward P/E:** {info.get('forwardPE', 'N/A')}")
        st.write(f"**Return on Equity:** {info.get('returnOnEquity', 'N/A')}")

        # Sample news
