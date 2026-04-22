import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="LiraPulse - Finans Terminali", layout="wide")

# BIST 100 ve Global Takip Listesi (Dinamik genişletilebilir)
BIST100_TICKERS = [
    "AEFES.IS", "AGHOL.IS", "AKBNK.IS", "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ALBRK.IS", "ALFAS.IS",
    "ARCLK.IS", "ASELS.IS", "ASTOR.IS", "ASUZU.IS", "BERA.IS", "BIMAS.IS", "BRSAN.IS", "BRYAT.IS",
    "BUCIM.IS", "CANTE.IS", "CCOLA.IS", "CIMSA.IS", "CWENE.IS", "DOAS.IS", "DOHOL.IS", "EGEEN.IS",
    "EKGYO.IS", "ENJSA.IS", "ENKAI.IS", "EREGL.IS", "EUPWR.IS", "FROTO.IS", "GARAN.IS", "GESAN.IS",
    "GUBRF.IS", "GWIND.IS", "HALKB.IS", "HEKTS.IS", "IPEKE.IS", "ISCTR.IS", "ISGYO.IS", "ISMEN.IS",
    "KAYSE.IS", "KCHOL.IS", "KONTR.IS", "KORDS.IS", "KOZAL.IS", "KOZAA.IS", "KRDMD.IS", "MGROS.IS",
    "MIATK.IS", "ODAS.IS", "OTKAR.IS", "OYAKC.IS", "PETKM.IS", "PGSUS.IS", "SAHOL.IS", "SASA.IS",
    "SISE.IS", "SKBNK.IS", "SMRTG.IS", "SOKM.IS", "TAVHL.IS", "TCELL.IS", "THYAO.IS", "TKFEN.IS",
    "TOASO.IS", "TSKB.IS", "TTKOM.IS", "TUPRS.IS", "VAKBN.IS", "VESBE.IS", "VESTL.IS", "YEOTK.IS",
    "YKBNK.IS", "ZOREN.IS", "BTC-USD", "ETH-USD"
]

@st.cache_data(ttl=600)
def get_data(symbol, period="1y"):
    return yf.Ticker(symbol).history(period=period)

st.title("📈 LiraPulse: BIST 100 & Global Terminal")

# --- 1. BÖLÜM: INTERAKTİF TEKNİK GRAFİK (EN ÜSTE GELDİ) ---
st.subheader("🔍 Detaylı Teknik Analiz")
col_g1, col_g2 = st.columns([1, 4])

with col_g1:
    target = st.selectbox("İncelemek istediğiniz varlık:", BIST100_TICKERS, index=BIST100_TICKERS.index("THYAO.IS"))
    range_select = st.selectbox("Zaman Aralığı:", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)

with col_g2:
    hist = get_data(target, range_select)
    if not hist.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name=target
        )])
        
        # Hareketli Ortalama Ekleme (SMA 20)
        hist['SMA20'] = hist['Close'].rolling(window=20).mean()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA20'], line=dict(color='orange', width=1.5), name='SMA 20'))
        
        fig.update_layout(
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=500,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)

# --- 2. BÖLÜM: CANLI PİYASA TAKİBİ ---
st.divider()
st.subheader("📊 Canlı Piyasa İzleme Listesi")

@st.cache_data(ttl=300)
def fetch_market_snapshot(tickers):
    data_list = []
    for t in tickers:
        try:
            d = yf.Ticker(t).history(period="2d")
            if len(d) >= 2:
                current = d['Close'].iloc[-1]
                prev = d['Close'].iloc[-2]
                change = ((current - prev) / prev) * 100
                data_list.append({
                    "Sembol": t.replace(".IS", ""),
                    "Son Fiyat": f"{current:.2f}",
                    "Günlük Değişim %": f"{change:+.2f}%",
                    "Hacim": f"{d['Volume'].iloc[-1]:,}"
                })
        except: continue
    return pd.DataFrame(data_list)

market_df = fetch_market_snapshot(BIST100_TICKERS[:25]) # Performans için ilk 25'i anlık listeler
st.dataframe(market_df, use_container_width=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>LiraPulse | BIST 100 Terminali v2.0</p>", unsafe_allow_html=True)
