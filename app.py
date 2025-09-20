import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from nsepython import nse_fno_oi

st.title("Nifty & NSE Universe Scanner with Technical, Fundamental, and F&O Impact")

# Sample tickers for each Nifty group (expand or fetch dynamically)
nifty_50 = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "KOTAKBANK", "SBIN", "ITC", "BHARTIARTL"]
nifty_100_extra = ["BAJFINANCE", "ADANIPORTS", "ASIANPAINT", "ULTRACEMCO", "MARUTI"]
nifty_200_extra = ["CIPLA", "EICHERMOT", "BRITANNIA", "DRREDDY", "TITAN"]
nifty_500_extra = ["APOLLOHOSP", "BHEL", "COALINDIA", "GRASIM", "HCLTECH"]
nifty_1000_extra = ["INDIGO", "MUTHOOTFIN", "PAGEIND", "TATAMOTORS", "ZEEL"]
nifty_all_extra = ["REPCOHOME", "SAIL", "WIPRO", "YESBANK", "ZOMATO"]

indices = {
    "Nifty 50": nifty_50,
    "Nifty 100": nifty_50 + nifty_100_extra,
    "Nifty 200": nifty_50 + nifty_100_extra + nifty_200_extra,
    "Nifty 500": nifty_50 + nifty_100_extra + nifty_200_extra + nifty_500_extra,
    "Nifty 1000": nifty_50 + nifty_100_extra + nifty_200_extra + nifty_500_extra + nifty_1000_extra,
    "NSE All": nifty_50 + nifty_100_extra + nifty_200_extra + nifty_500_extra + nifty_1000_extra + nifty_all_extra
}

# User selection of universe
universe = st.selectbox("Select Stock Universe to Scan:", list(indices.keys()))

tickers = indices[universe]

st.write(f"Scanning {len(tickers)} stocks from {universe} with technical, fundamental, and F&O data impact...")

results = []

for ticker in tickers:
    try:
        ticker_ns = ticker + ".NS"
        data = yf.Ticker(ticker_ns).history(period="60d")
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

        cond1 = latest['RSI'] < 30
        cond2 = latest['MACD'] > latest['MACD_signal']
        cond3 = latest['SMA_20'] > latest['SMA_50']

        tech_score = sum([cond1, cond2, cond3])

        # Fundamental Analysis
        info = yf.Ticker(ticker_ns).info

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

        # Fetch F&O data internally
        fno_data = nse_fno_oi(ticker)
        call_oi = fno_data.get('callOI', 0)
        put_oi = fno_data.get('putOI', 0)
        pcr = put_oi / call_oi if call_oi > 0 else None

        fno_score = 0
        if pcr is not None:
            if pcr < 0.8:
                fno_score = 1
            elif pcr > 1.2:
                fno_score = -1

        combined_score = tech_score + funda_score + fno_score

        if combined_score >= 6:
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
                'Fundamental Score': funda_score,
                'F&O Impact Score': fno_score,
                'Combined Score': combined_score
            })

    except Exception as e:
        st.write(f"Skipped {ticker}: {str(e)}")

if results:
    df = pd.DataFrame(results)
    st.subheader(f"Stocks Passing Filters in {universe} Universe")
    st.dataframe(df)
else:
    st.write(f"No stocks passed the filters in {universe}.")
