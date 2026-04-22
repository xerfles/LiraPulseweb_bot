import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Alper Finans Pro", layout="wide")

# Kenar Çubuğu (Sidebar)
st.sidebar.title("⚙️ Kontrol Paneli")
refresh_btn = st.sidebar.button("🔄 Verileri Yenile")
selected_range = st.sidebar.selectbox("Zaman Aralığı", ["1mo", "3mo", "6mo", "1y", "2y"])

if refresh_btn:
    st.cache_data.clear()

st.title("📈 Alper Finans Gelişmiş Dashboard")

VARLIKLAR = {
    "THYAO": "THYAO.IS", "TUPRS": "TUPRS.IS", "KCHOL": "KCHOL.IS", 
    "ASTOR": "ASTOR.IS", "AKBNK": "AKBNK.IS", "ASELS": "ASELS.IS", 
    "KONTR": "KONTR.IS", "MIATK": "MIATK.IS", "SASA": "SASA.IS", 
    "BTC": "BTC-USD", "ETH": "ETH-USD", "PAXG": "PAXG-USD"
}

@st.cache_data(ttl=300)
def fetch_finance_data(symbol, period):
    return yf.Ticker(symbol).history(period=period)

# RSI Hesaplama Fonksiyonu
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- ÖZET TABLO VE ANALİZ ---
analiz_data = []

for isim, sembol in VARLIKLAR.items():
    try:
        hist = fetch_finance_data(sembol, "1y")
        if hist.empty: continue
        
        current_price = hist['Close'].iloc[-1]
        daily_change = ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
        
        # RSI ve SMA50
        rsi_val = calculate_rsi(hist).iloc[-1]
        sma50 = hist['Close'].tail(50).mean()
        
        analiz_data.append({
            "Varlık": isim,
            "Fiyat": current_price,
            "Günlük %": daily_change,
            "RSI (14)": rsi_val,
            "Destek (SMA50)": sma50,
            "Durum": "🔥 Aşırı Alım" if rsi_val > 70 else ("❄️ Aşırı Satım" if rsi_val < 30 else "💎 Stabil")
        })
    except: continue

df = pd.DataFrame(analiz_data)

# Tabloyu Göster
st.subheader("📊 Canlı Takip ve Sinyaller")
st.dataframe(df.style.format("{:.2f}", subset=["Fiyat", "Günlük %", "RSI (14)", "Destek (SMA50)"]), use_container_width=True)

# --- GRAFİK BÖLÜMÜ ---
st.divider()
st.subheader("🔍 Detaylı Grafik İnceleme")
target = st.selectbox("Grafiğini görmek istediğin varlığı seç:", list(VARLIKLAR.keys()))

if target:
    detail_data = fetch_finance_data(VARLIKLAR[target], selected_range)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=detail_data.index,
                open=detail_data['Open'], high=detail_data['High'],
                low=detail_data['Low'], close=detail_data['Close'], name='Fiyat'))
    fig.update_layout(title=f"{target} Fiyat Grafiği", xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

st.success("Tebrikler kanka! LinkedIn için mükemmel bir portföy paneli oldu.")
