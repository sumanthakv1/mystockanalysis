import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# Placeholder for news sentiment function
def get_news_sentiment(ticker):
    # TODO: Replace with real financial news sentiment analysis per ticker or sector
    return 0.0

def fetch_stock_data(ticker):
    data = yf.Ticker(ticker).history(period="60d")
    if len(data) < 50:
        return None, None
    data['20d_High'] = data['High'].rolling(window=20).max().shift(1)
    data['50d_High'] = data['High'].rolling(window=50).max().shift(1)
    data['20d_Vol_Avg'] = data['Volume'].rolling(window=20).mean().shift(1)
    data['RSI'] = ta.rsi(data['Close'], length=14)
    macd = ta.macd(data['Close'])
    data['MACD'] = macd.iloc[:, 0]
    data['MACD_signal'] = macd.iloc[:, 1]
    data['ATR'] = ta.atr(data['High'], data['Low'], data['Close'], length=14)
    data['AD'] = ta.ad(data['High'], data['Low'], data['Close'], data['Volume'])
    
    latest = data.iloc[-1]
    return data, latest

def analyze_stock(ticker):
    data, latest = fetch_stock_data(ticker)
    if data is None or latest is None:
        return None

    try:
        breakout_20d = latest['Close'] > latest['20d_High']
        breakout_50d = latest['Close'] > latest['50d_High']
        volume_spike = latest['Volume'] > 1.5 * latest['20d_Vol_Avg']
        rsi_ok = latest['RSI'] > 60
        macd_cross = latest['MACD'] > latest['MACD_signal']

        ad_trend = data['AD'].iloc[-5:]
        accumulation_up = ad_trend.is_monotonic_increasing if len(ad_trend) == 5 else False

        breakout_score = sum([breakout_20d, breakout_50d, volume_spike, rsi_ok, macd_cross, accumulation_up])

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

        return {
            'Ticker': ticker,
            'Breakout_20d': breakout_20d,
            'Breakout_50d': breakout_50d,
            'Volume_Spike': volume_spike,
            'RSI': round(latest['RSI'], 2),
            'MACD_Cross': macd_cross,
            'Accumulation_Up': accumulation_up,
            'Breakout_Score': breakout_score,
            'P/E': round(pe, 2) if pe else None,
            'P/B': round(pb, 2) if pb else None,
            'Debt/Equity': round(debt_equity, 2) if debt_equity else None,
            'ROE': round(roe, 2) if roe else None,
            'Earnings Growth': round(earnings_growth, 2) if earnings_growth else None,
            'Fundamental Score': funda_score,
            'Close': round(latest['Close'], 2),
            'ATR': round(latest['ATR'], 2)
        }
    except Exception as e:
        return None

def filter_stocks(stocks):
    recommendations = []
    for stock in stocks:
        if stock is None:
            continue

        news_sentiment = get_news_sentiment(stock['Ticker'])
        combined_score = stock['Breakout_Score'] + stock['Fundamental Score'] + news_sentiment

        buy_price = stock['Close']
        stop_loss = buy_price - stock['ATR']
        if stop_loss <= 0:
            continue
        risk = buy_price - stop_loss
        target_sell = buy_price + 3 * risk
        risk_reward = (target_sell - buy_price) / risk

        if risk_reward >= 3 and combined_score >= 5:
            stock.update({
                'Buy Price': buy_price,
                'Stop Loss': round(stop_loss, 2),
                'Target Sell Price': round(target_sell, 2),
                'Risk-Reward': round(risk_reward, 2),
                'News Sentiment': round(news_sentiment, 2),
                'Combined Score': round(combined_score, 2)
            })
            recommendations.append(stock)
    return recommendations


st.title("Breakout & Fundamental Stock Scanner with News Sentiment & 1:3 Risk-Reward")

# Select universe (expand as needed)
nifty_50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "KOTAKBANK.NS", "SBIN.NS", "ITC.NS", "BHARTIARTL.NS"
]

univ_choice = st.selectbox("Select Universe to Scan:", ["Nifty 50"])  # Expand options as desired

if univ_choice == "Nifty 50":
    tickers = nifty_50
else:
    tickers = []

with st.spinner("Analyzing stocks..."):
    stocks_data = [analyze_stock(ticker) for ticker in tickers]

filtered_stocks = filter_stocks(stocks_data)

if filtered_stocks:
    df = pd.DataFrame(filtered_stocks)
    st.subheader(f"Recommended Stocks with Breakout & 1:3 Risk-Reward")
    st.dataframe(df)
else:
    st.write("No stocks match the criteria currently.")
