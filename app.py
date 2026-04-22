import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="LiraPulse - Finans Terminali", layout="wide")

# BIST 30 Listesi ve Ek Varlıklar
BIST30_TICKERS = [
    "AKBNK.IS", "AKSEN.IS", "ALARK.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS", "BRSAN.IS",
    "DOAS.IS", "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "GUBRF.IS", "HEKTS.IS",
    "ISCTR.IS", "KCHOL.IS", "KONTR.IS", "KOZAL.IS", "KRDMD.IS", "ODAS.IS", "OYAKC.IS", "PETKM.IS",
    "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS",
    "YKBNK.IS", "BTC-USD", "XAUUSD=X"
]

@st.cache_data(ttl=300)
def get_extended_data(ticker):
    try:
        # Tüm periyotlar için yeterli veriyi tek seferde çekiyoruz (2 yıllık)
        data = yf.Ticker(ticker).history(period="2y")
        if data.empty: return None
        
        current_price = data['Close'].iloc[-1]
        
        # Değişim Hesaplamaları
        def get_change(days):
            target_date = data.index[-1] - timedelta(days=days)
            # Hedef tarihe en yakın iş gününü bul
            closest_idx = data.index.get_indexer([target_date], method='nearest')[0]
            old_price = data['Close'].iloc[closest_idx]
            return ((current_price - old_price) / old_price) * 100

        # Teknik Göstergeler (Al-Sat Sinyali İçin)
        # RSI 14
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1]))
        
        # SMA 20 ve 50
        sma20 = data['Close'].tail(20).mean()
        sma50 = data['Close'].tail(50).mean()

        # Sinyal Algoritması
        if rsi < 30: sinyal = "🔵 GÜÇLÜ AL (Aşırı Satım)"
        elif rsi > 70: sinyal = "🟠 GÜÇLÜ SAT (Aşırı Alım)"
        elif current_price > sma20 and sma20 > sma50: sinyal = "🟢 AL (Trend Yukarı)"
        elif current_price < sma20 and sma20 < sma50: sinyal = "🔴 SAT (Trend Aşağı)"
        else: sinyal = "⚪ NÖTR"

        return {
            "Sembol": ticker.replace(".IS", ""),
            "Fiyat": round(current_price, 2),
            "Günlük %": round(((current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100, 2),
            "Haftalık %": round(get_change(7), 2),
            "Aylık %": round(get_change(30), 2),
            "Yıllık %": round(get_change(365), 2),
            "Sinyal": sinyal,
            "RSI": round(rsi, 1)
        }
    except: return None

st.sidebar.title("⚙️ LiraPulse Kontrol")
if st.sidebar.button("🔄 Verileri Şimdi Tazele"):
    st.cache_data.clear()
    st.rerun()

st.title("📈 LiraPulse: BIST 30 Stratejik Terminal")

# --- 1. BÖLÜM: GRAFİK ---
target = st.selectbox("Grafik Analizi:", BIST30_TICKERS, index=BIST30_TICKERS.index("THYAO.IS"))
hist = yf.Ticker(target).history(period="1y")
fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name='Fiyat')])
fig.update_layout(template="plotly_dark", height=450, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)

# --- 2. BÖLÜM: DEV TABLO ---
st.subheader("📊 BIST 30 Performans ve Sinyal Tablosu")

with st.spinner('Veriler analiz ediliyor, lütfen bekleyin...'):
    all_data = [get_extended_data(t) for t in BIST30_TICKERS]
    df = pd.DataFrame([x for x in all_data if x is not None])

# Renklendirme Fonksiyonu
def color_df(val):
    if isinstance(val, str): return ''
    color = '#2ecc71' if val > 0 else '#e74c3c' if val < 0 else 'white'
    return f'color: {color}'

st.dataframe(
    df.style.map(color_df, subset=['Günlük %', 'Haftalık %', 'Aylık %', 'Yıllık %']),
    use_container_width=True,
    height=600
)

st.markdown("---")
st.caption("💡 **Sinyal Notu:** AL/SAT sinyalleri RSI ve Hareketli Ortalama (SMA) kesişimlerine göre otomatik üretilir, yatırım tavsiyesi değildir.")
