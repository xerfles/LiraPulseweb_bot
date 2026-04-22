import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="LiraPulse Terminal", layout="wide")

# Sadece Saf BIST 30
BIST30 = [
    "AKBNK.IS", "AKSEN.IS", "ALARK.IS", "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "BIMAS.IS", "BRSAN.IS",
    "DOAS.IS", "EKGYO.IS", "ENKAI.IS", "EREGL.IS", "FROTO.IS", "GARAN.IS", "GUBRF.IS", "HEKTS.IS",
    "ISCTR.IS", "KCHOL.IS", "KONTR.IS", "KOZAL.IS", "KRDMD.IS", "ODAS.IS", "OYAKC.IS", "PETKM.IS",
    "PGSUS.IS", "SAHOL.IS", "SASA.IS", "SISE.IS", "TCELL.IS", "THYAO.IS", "TOASO.IS", "TUPRS.IS",
    "YKBNK.IS"
]

@st.cache_data(ttl=300)
def get_clean_data(ticker):
    d = yf.Ticker(ticker).history(period="1y")
    # Teknik Hesaplamalar (Sadeleşmiş)
    d['SMA20'] = d['Close'].rolling(20).mean()
    delta = d['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    d['RSI'] = 100 - (100 / (1 + (gain / loss)))
    return d

st.title("📈 LiraPulse Terminal")

target = st.selectbox("Hisse Seçimi", BIST30, index=BIST30.index("THYAO.IS"))
df = get_clean_data(target)

# --- SADELEŞTİRİLMİŞ GRAFİK ---
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])

# Üst Panel: Mumlar ve SMA
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Fiyat'), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], line=dict(color='orange', width=1.5), name='SMA 20'), row=1, col=1)

# Alt Panel: RSI (Sadece çizgi)
fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#00e676', width=1.5), name='RSI'), row=2, col=1)
fig.add_hline(y=70, line_dash="dot", line_color="red", line_width=1, row=2, col=1)
fig.add_hline(y=30, line_dash="dot", line_color="cyan", line_width=1, row=2, col=1)

fig.update_layout(template="plotly_dark", height=550, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)

# --- SADE TABLO ---
st.subheader("📊 BIST 30 Performans")
# Tablo verilerini çekme ve formatlama (Önceki kodun sade hali)
# ... (Buraya önceki tablo kodunu ekleyebilirsin, RSI sütunu olmayan hali)
