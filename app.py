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
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")

        st.subheader(f"{ticker} Closing Prices")
        st.line_chart(hist['Close'])

        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()

        st.subheader("20 & 50 Day Simple Moving Averages (SMA)")
        st.line_chart(hist[['Close', 'SMA_20', 'SMA_50']])

        st.subheader("Basic Company Info")
        info = stock.info
        st.write(f"**Market Cap:** {info.get('marketCap', 'N/A')}")
        st.write(f"**Trailing P/E:** {info.get('trailingPE', 'N/A')}")
        st.write(f"**Forward P/E:** {info.get('forwardPE', 'N/A')}")
        st.write(f"**Return on Equity:** {info.get('returnOnEquity', 'N/A')}")

        sample_news = [
            "Company reports record quarterly profits.",
            "New product launch may boost future revenues.",
            "Regulatory concerns on upcoming projects.",
            "CEO resigns unexpectedly.",
        ]

        st.subheader("Sample News Sentiment Analysis")
        analyzer = SentimentIntensityAnalyzer()
        for headline in sample_news:
            score = analyzer.polarity_scores(headline)['compound']
            sentiment = "Positive" if score > 0.05 else "Neutral" if score > -0.05 else "Negative"
            st.write(f"News: {headline}")
            st.write(f"Sentiment score: {score} ({sentiment})")
            st.markdown("---")

    except Exception as e:
        st.error(f"Error retrieving data for ticker '{ticker}'. Please check the symbol and try again.")

