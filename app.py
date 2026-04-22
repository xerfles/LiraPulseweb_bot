import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="LiraPulse - Finans Terminali", layout="wide")

# BIST 30 Listesi
BIST30_TICKERS = [
    "AKBNK.IS", "AKSEN.IS", "ALARK.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS", "BRSAN.IS",
    "DOAS.IS", "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "GUBRF.IS", "HEKTS.IS",
    "ISCTR.IS", "KCHOL.IS", "KONTR.IS", "KOZAL.IS", "KRDMD.IS", "ODAS.IS", "OYAKC.IS", "PETKM.IS",
    "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS",
    "YKBNK.IS", "BTC-USD", "ETH-USD"
]

@st.cache_data(ttl=300)
def get_extended_data(ticker):
    try:
        data = yf.Ticker(ticker).history(period="2y")
        if data.empty: return None
        
        current_price = data['Close'].iloc[-1]
        
        def get_change(days):
            target_date = data.index[-1] - timedelta(days=days)
            closest_idx = data.index.get_indexer([target_date], method='nearest')[0]
            old_price = data['Close'].iloc[closest_idx]
            return ((current_price - old_price) / old_price) * 100

        # RSI Hesaplama
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss).iloc[-1]))
        
        # Hareketli Ortalamalar
        sma20 = data['Close'].tail(20).mean()
        sma50 = data['Close'].tail(50).mean()

        if rsi < 30: sinyal = "🔵 GÜÇLÜ AL"
        elif rsi > 70: sinyal = "🟠 GÜÇLÜ SAT"
        elif current_price > sma20 and sma20 > sma50: sinyal = "🟢 AL (Trend ↑)"
        elif current_price < sma20 and sma20 < sma50: sinyal = "🔴 SAT (Trend ↓)"
        else: sinyal = "⚪ NÖTR"

        return {
            "Sembol": ticker.replace(".IS", ""),
            "Fiyat": current_price,
            "Günlük %": ((current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100,
            "Haftalık %": get_change(7),
            "Aylık %": get_change(30),
            "Yıllık %": get_change(365),
            "Sinyal": sinyal,
            "RSI": rsi
        }
    except: return None

st.sidebar.title("⚙️ LiraPulse Kontrol")
if st.sidebar.button("🔄 Verileri Tazele"):
    st.cache_data.clear()
    st.rerun()

st.title("📈 LiraPulse: BIST 30 Stratejik Terminal")

# --- GRAFİK ---
target = st.selectbox("Grafik Analizi:", BIST30_TICKERS, index=BIST30_TICKERS.index("THYAO.IS"))
hist = yf.Ticker(target).history(period="1y")
fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'], name='Fiyat')])
fig.update_layout(template="plotly_dark", height=400, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)

# --- TABLO ---
st.subheader("📊 Performans ve Teknik Sinyaller")

all_data = [get_extended_data(t) for t in BIST30_TICKERS]
df = pd.DataFrame([x for x in all_data if x is not None])

# FORMATLAMA: Sıfırları temizleyen ve ondalığı sabitleyen kısım
format_dict = {
    "Fiyat": "{:.2f}",
    "Günlük %": "{:+.2f}%",
    "Haftalık %": "{:+.2f}%",
    "Aylık %": "{:+.2f}%",
    "Yıllık %": "{:+.2f}%",
    "RSI": "{:.1f}"
}

def color_df(val):
    if not isinstance(val, (int, float)): return ''
    return f'color: {"#2ecc71" if val > 0 else "#e74c3c" if val < 0 else "white"}'

# Stili uygula ve tabloyu göster
st.dataframe(
    df.style.format(format_dict).map(color_df, subset=['Günlük %', 'Haftalık %', 'Aylık %', 'Yıllık %']),
    use_container_width=True,
    height=600
)
