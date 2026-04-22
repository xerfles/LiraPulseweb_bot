import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="LiraPulse Terminal", layout="wide")

# BIST 30 TAM LİSTE
BIST30 = [
    "AKBNK.IS", "AKSEN.IS", "ALARK.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS", "BRSAN.IS",
    "DOAS.IS", "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "GUBRF.IS", "HEKTS.IS",
    "ISCTR.IS", "KCHOL.IS", "KONTR.IS", "KOZAL.IS", "KRDMD.IS", "ODAS.IS", "OYAKC.IS", "PETKM.IS",
    "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS",
    "YKBNK.IS"
]

@st.cache_data(ttl=300)
def get_extended_data(ticker):
    try:
        data = yf.Ticker(ticker).history(period="2y")
        if data.empty: return None
        current_price = data['Close'].iloc[-1]
        
        def calc_change(days):
            target_date = data.index[-1] - timedelta(days=days)
            idx = data.index.get_indexer([target_date], method='nearest')[0]
            old_price = data['Close'].iloc[idx]
            return ((current_price - old_price) / old_price) * 100

        # Teknik Sinyal (RSI & SMA)
        sma20 = data['Close'].tail(20).mean()
        sma50 = data['Close'].tail(50).mean()
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / loss).iloc[-1]))

        if rsi < 35: sinyal = "🔵 GÜÇLÜ AL"
        elif rsi > 65: sinyal = "🟠 GÜÇLÜ SAT"
        elif current_price > sma20 and sma20 > sma50: sinyal = "🟢 AL"
        elif current_price < sma20 and sma20 < sma50: sinyal = "🔴 SAT"
        else: sinyal = "⚪ NÖTR"

        return {
            "Sembol": ticker.replace(".IS", ""),
            "Fiyat": current_price,
            "Günlük %": ((current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100,
            "Haftalık %": calc_change(7),
            "Aylık %": calc_change(30),
            "Yıllık %": calc_change(365),
            "Sinyal": sinyal
        }
    except: return None

# SIDEBAR: VERİLERİ TAZELE (GERİ GELDİ)
st.sidebar.title("⚙️ Kontrol Paneli")
if st.sidebar.button("🔄 Verileri Şimdi Tazele"):
    st.cache_data.clear()
    st.rerun()

st.title("📈 LiraPulse: Stratejik Analiz Terminali")

# GRAFİK
target = st.selectbox("Hisse Seçimi", BIST30, index=BIST30.index("THYAO.IS"))
h = yf.Ticker(target).history(period="1y")
h['SMA20'] = h['Close'].rolling(20).mean()
# RSI
dr = h['Close'].diff()
gr = (dr.where(dr > 0, 0)).rolling(14).mean()
lr = (-dr.where(dr < 0, 0)).rolling(14).mean()
h['RSI'] = 100 - (100 / (1 + (gr / lr)))

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
fig.add_trace(go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name='Fiyat'), row=1, col=1)
fig.add_trace(go.Scatter(x=h.index, y=h['SMA20'], line=dict(color='orange', width=1.5), name='SMA 20'), row=1, col=1)
fig.add_trace(go.Scatter(x=h.index, y=h['RSI'], line=dict(color='#00e676', width=1.5), name='RSI'), row=2, col=1)
fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
fig.add_hline(y=30, line_dash="dot", line_color="cyan", row=2, col=1)
fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)

# TABLO (FULL VERİ)
st.subheader("📊 BIST 30 Strateji Tablosu")
with st.spinner('Piyasa verileri işleniyor...'):
    data_list = [get_extended_data(t) for t in BIST30]
    df_main = pd.DataFrame([x for x in data_list if x is not None])

f_map = {"Fiyat": "{:.2f}", "Günlük %": "{:+.2f}%", "Haftalık %": "{:+.2f}%", "Aylık %": "{:+.2f}%", "Yıllık %": "{:+.2f}%"}
def color_rows(val):
    if not isinstance(val, (int, float)): return ''
    return f'color: {"#2ecc71" if val > 0 else "#e74c3c" if val < 0 else "white"}'

st.dataframe(df_main.style.format(f_map).map(color_rows, subset=['Günlük %', 'Haftalık %', 'Aylık %', 'Yıllık %']), use_container_width=True, height=600)
