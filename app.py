import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from nsepython import nse_fno_oi

st.title("Nifty Index Scanner with Internal F&O Data Impact")

# Sample ticker list (expand as needed)
nifty200_tickers = [
    "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", 
    "HINDUNILVR", "KOTAKBANK", "SBIN", "ITC", "BHARTIARTL"
]

st.write(f"Scanning {len(nifty200_tickers)} stocks with technical, fundamental analysis and F&O impact...")

results = []

for ticker in nifty200_tickers:
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

        # Technical buy signal conditions
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

        # Fetch F&O data internally for scoring impact
        fno_data = nse_fno_oi(ticker)
        call_oi = fno_data.get('callOI', 0)
        put_oi = fno_data.get('putOI', 0)
        pcr = put_oi / call_oi if call_oi > 0 else None

        # Heuristic F&O impact score: neutral=0, bullish if PCR < 1, bearish if PCR > 1
        fno_score = 0
        if pcr is not None:
            if pcr < 0.8:
                fno_score = 1  # bullish bias
            elif pcr > 1.2:
                fno_score = -1  # bearish bias

        # Weighted combined score including F&O impact
        combined_score = tech_score + funda_score + fno_score  # simple sum for demo

        # Filters for passing stock
        if combined_score >= 6:  # adjust threshold as needed
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
                'Combined Score': combined_score,
            })

    except Exception as e:
        st.write(f"Skipped {ticker}: {str(e)}")

if results:
    df = pd.DataFrame(results)
    st.subheader("Stocks with positive combined scores including F&O impact")
    st.dataframe(df)
else:
    st.write("No stocks passed the combined score criteria.")
