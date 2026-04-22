import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Finansal Analiz ve Portföy Paneli", layout="wide")

st.sidebar.title("⚙️ Kontrol Paneli")
refresh_btn = st.sidebar.button("🔄 Verileri Yenile")
selected_range = st.sidebar.selectbox("Zaman Aralığı", ["1mo", "3mo", "6mo", "1y", "2y"])

if refresh_btn:
    st.cache_data.clear()

st.title("📈 Kurumsal Finans ve Teknik Analiz Paneli")
st.markdown("Borsa İstanbul ve Kripto Piyasaları için Anlık Fiyatlama, RSI ve Volatilite İzleme Ekranı")

VARLIKLAR = {
    "THYAO": "THYAO.IS", "TUPRS": "TUPRS.IS", "KCHOL": "KCHOL.IS", 
    "ASTOR": "ASTOR.IS", "AKBNK": "AKBNK.IS", "ASELS": "ASELS.IS", 
    "KONTR": "KONTR.IS", "MIATK": "MIATK.IS", "SASA": "SASA.IS", 
    "BTC": "BTC-USD", "ETH": "ETH-USD", "PAXG": "PAXG-USD"
}

@st.cache_data(ttl=300)
def fetch_finance_data(symbol, period):
    return yf.Ticker(symbol).history(period=period)

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

analiz_data = []

for isim, sembol in VARLIKLAR.items():
    try:
        hist = fetch_finance_data(sembol, "1y")
        if hist.empty: continue
        
        current_price = hist['Close'].iloc[-1]
        daily_change = ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
        
        rsi_val = calculate_rsi(hist).iloc[-1]
        sma50 = hist['Close'].tail(50).mean()
        volume = hist['Volume'].iloc[-1]
        
        # Volatilite (Son 20 günün standart sapması)
        std_dev = hist['Close'].tail(20).std()
        
        analiz_data.append({
            "Varlık": isim,
            "Fiyat": current_price,
            "Günlük %": daily_change,
            "RSI (14)": rsi_val,
            "Destek (SMA50)": sma50,
            "Volatilite": std_dev,
            "Hacim": volume,
            "Durum": "🔴 Aşırı Alım" if rsi_val > 70 else ("🟢 Aşırı Satım" if rsi_val < 30 else "⚪ Stabil")
        })
    except: continue

df = pd.DataFrame(analiz_data)

st.subheader("📊 Canlı Piyasa Sinyalleri ve Likidite")
st.dataframe(df.style.format({
    "Fiyat": "{:.2f}", 
    "Günlük %": "{:.2f}", 
    "RSI (14)": "{:.2f}", 
    "Destek (SMA50)": "{:.2f}",
    "Volatilite": "{:.2f}",
    "Hacim": "{:,.0f}"
}), use_container_width=True)

st.divider()
st.subheader("🔍 İnteraktif Grafik ve Trend Analizi")
target = st.selectbox("Detaylı incelemek istediğiniz varlığı seçin:", list(VARLIKLAR.keys()))

if target:
    detail_data = fetch_finance_data(VARLIKLAR[target], selected_range)
    
    fig = go.Figure()
    
    # Mum Grafik
    fig.add_trace(go.Candlestick(x=detail_data.index,
                open=detail_data['Open'], high=detail_data['High'],
                low=detail_data['Low'], close=detail_data['Close'], name='Fiyat'))
                
    # 20 Günlük Hareketli Ortalama (Trend Çizgisi)
    detail_data['SMA20'] = detail_data['Close'].rolling(window=20).mean()
    fig.add_trace(go.Scatter(x=detail_data.index, y=detail_data['SMA20'], 
                             line=dict(color='orange', width=1.5), name='SMA 20'))
                             
    fig.update_layout(title=f"{target} Teknik Analiz Grafiği", 
                      xaxis_rangeslider_visible=False, 
                      template="plotly_dark",
                      height=500)
    st.plotly_chart(fig, use_container_width=True)

# Kurumsal Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'>Algoritmik Piyasa Takip Paneli | Veriler anlık olarak yfinance altyapısı üzerinden işlenmektedir.</p>", unsafe_allow_html=True)
