import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="LiraPulse - BIST 30 Terminal", layout="wide")

# Sadece Saf BIST 30 Listesi
BIST30_TICKERS = [
    "AKBNK.IS", "AKSEN.IS", "ALARK.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS", "BRSAN.IS",
    "DOAS.IS", "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "GUBRF.IS", "HEKTS.IS",
    "ISCTR.IS", "KCHOL.IS", "KONTR.IS", "KOZAL.IS", "KRDMD.IS", "ODAS.IS", "OYAKC.IS", "PETKM.IS",
    "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS",
    "YKBNK.IS"
]

@st.cache_data(ttl=300)
def get_terminal_data(ticker):
    try:
        data = yf.Ticker(ticker).history(period="2y")
        if data.empty: return None
        
        current_price = data['Close'].iloc[-1]
        
        def get_change(days):
            target_date = data.index[-1] - timedelta(days=days)
            closest_idx = data.index.get_indexer([target_date], method='nearest')[0]
            old_price = data['Close'].iloc[closest_idx]
            return ((current_price - old_price) / old_price) * 100

        # Teknik Sinyal Algoritması (Arka planda çalışır, tabloda görünmez)
        sma20 = data['Close'].tail(20).mean()
        sma50 = data['Close'].tail(50).mean()
        
        if current_price > sma20 and sma20 > sma50: sinyal = "🟢 AL (Trend ↑)"
        elif current_price < sma20 and sma20 < sma50: sinyal = "🔴 SAT (Trend ↓)"
        else: sinyal = "⚪ NÖTR"

        return {
            "Sembol": ticker.replace(".IS", ""),
            "Fiyat": current_price,
            "Günlük %": ((current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100,
            "Haftalık %": get_change(7),
            "Aylık %": get_change(30),
            "Yıllık %": get_change(365),
            "Trend Durumu": sinyal
        }
    except: return None

st.sidebar.title("⚙️ LiraPulse Kontrol")
if st.sidebar.button("🔄 Verileri Tazele"):
    st.cache_data.clear()
    st.rerun()

st.title("📈 LiraPulse: BIST 30 Stratejik Analiz")

# --- GELİŞMİŞ GRAFİK BÖLÜMÜ ---
target = st.selectbox("Analiz Edilecek Hisse:", BIST30_TICKERS, index=BIST30_TICKERS.index("THYAO.IS"))
h = yf.Ticker(target).history(period="1y")

# Bollinger Bantları Hesaplama
h['SMA20'] = h['Close'].rolling(window=20).mean()
h['STD'] = h['Close'].rolling(window=20).std()
h['Upper'] = h['SMA20'] + (h['STD'] * 2)
h['Lower'] = h['SMA20'] - (h['STD'] * 2)

# RSI Hesaplama (Grafik için)
delta = h['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
h['RSI'] = 100 - (100 / (1 + (gain / loss)))

# Grafik Oluşturma (2 Satırlı: Fiyat + RSI)
from plotly.subplots import make_subplots
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

# Ana Fiyat ve Bollinger
fig.add_trace(go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name='Fiyat'), row=1, col=1)
fig.add_trace(go.Scatter(x=h.index, y=h['Upper'], line=dict(color='rgba(173, 216, 230, 0.5)'), name='Bollinger Üst'), row=1, col=1)
fig.add_trace(go.Scatter(x=h.index, y=h['Lower'], line=dict(color='rgba(173, 216, 230, 0.5)'), name='Bollinger Alt', fill='tonexty'), row=1, col=1)
fig.add_trace(go.Scatter(x=h.index, y=h['SMA20'], line=dict(color='orange', width=1), name='SMA 20'), row=1, col=1)

# RSI Alt Grafik
fig.add_trace(go.Scatter(x=h.index, y=h['RSI'], line=dict(color='magenta'), name='RSI (14)'), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=20,b=0))
st.plotly_chart(fig, use_container_width=True)

# --- SIKIŞTIRILMIŞ TABLO ---
st.subheader("📊 BIST 30 Özet Performans")
with st.spinner('BIST 30 verileri işleniyor...'):
    all_data = [get_terminal_data(t) for t in BIST30_TICKERS]
    df = pd.DataFrame([x for x in all_data if x is not None])

format_dict = {
    "Fiyat": "{:.2f}",
    "Günlük %": "{:+.2f}%",
    "Haftalık %": "{:+.2f}%",
    "Aylık %": "{:+.2f}%",
    "Yıllık %": "{:+.2f}%"
}

def color_logic(val):
    if not isinstance(val, (int, float)): return ''
    return f'color: {"#2ecc71" if val > 0 else "#e74c3c" if val < 0 else "white"}'

st.dataframe(
    df.style.format(format_dict).map(color_logic, subset=['Günlük %', 'Haftalık %', 'Aylık %', 'Yıllık %']),
    use_container_width=True,
    height=500
)
