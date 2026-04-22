import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="LiraPulse - Finans Terminali", layout="wide")

st.sidebar.title("⚙️ LiraPulse Kontrol")
refresh_btn = st.sidebar.button("🔄 Verileri Yenile")
selected_range = st.sidebar.selectbox("Zaman Aralığı", ["1mo", "3mo", "6mo", "1y", "2y"])

if refresh_btn:
    st.cache_data.clear()

st.title("📈 LiraPulse: Portföy ve Piyasa Analiz Terminali")

VARLIKLAR = {
    "THYAO": "THYAO.IS", "TUPRS": "TUPRS.IS", "KCHOL": "KCHOL.IS", 
    "ASTOR": "ASTOR.IS", "AKBNK": "AKBNK.IS", "ASELS": "ASELS.IS", 
    "KONTR": "KONTR.IS", "MIATK": "MIATK.IS", "SASA": "SASA.IS", 
    "BTC": "BTC-USD", "ETH": "ETH-USD", "PAXG": "PAXG-USD"
}

@st.cache_data(ttl=300)
def fetch_finance_data(symbol, period):
    return yf.Ticker(symbol).history(period=period)

# --- CANLI VERİ ÇEKİMİ ---
analiz_data = []
anlik_fiyatlar = {}

for isim, sembol in VARLIKLAR.items():
    try:
        hist = fetch_finance_data(sembol, "1y")
        if hist.empty: continue
        anlik_fiyatlar[isim] = hist['Close'].iloc[-1]
        
        analiz_data.append({
            "Varlık": isim,
            "Fiyat": hist['Close'].iloc[-1],
            "Günlük %": ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100,
            "RSI (14)": 100 - (100 / (1 + (hist['Close'].diff().where(hist['Close'].diff() > 0, 0).rolling(14).mean() / -hist['Close'].diff().where(hist['Close'].diff() < 0, 0).rolling(14).mean()))).iloc[-1]
        })
    except: continue

# --- 1. BÖLÜM: İSTEĞE BAĞLI CÜZDAN (SEÇİMLİ SÜTUN) ---
with st.expander("💼 Kişisel Cüzdanım (Seçim Yapmak İçin Tıklayın)", expanded=False):
    if 'portfoy' not in st.session_state:
        st.session_state['portfoy'] = pd.DataFrame([
            {"Varlık": "THYAO", "Adet": 100.0, "Maliyet": 250.0},
            {"Varlık": "BTC", "Adet": 0.05, "Maliyet": 65000.0}
        ])

    # BURASI KRİTİK: Sütunu Selectbox (Açılır Menü) Yapıyoruz
    edited_df = st.data_editor(
        st.session_state['portfoy'], 
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "Varlık": st.column_config.SelectboxColumn(
                "Varlık Seç",
                help="Takip listendeki varlıklardan birini seç",
                width="medium",
                options=list(VARLIKLAR.keys()), # Sadece bizim listedeki isimler görünecek
                required=True,
            )
        }
    )
    st.session_state['portfoy'] = edited_df

    # Kar/Zarar Hesaplama (Önceki kodla aynı mantık)
    cuzdan_sonuclari = []
    toplam_maliyet_tl = 0
    toplam_guncel_deger_tl = 0
    usd_try = fetch_finance_data("TRY=X", "1d")['Close'].iloc[-1]

    for index, row in edited_df.iterrows():
        varlik = row["Varlık"]
        if varlik in anlik_fiyatlar:
            guncel_f = anlik_fiyatlar[varlik]
            m = row["Maliyet"]
            a = row["Adet"]
            t_m = a * m
            g_d = a * guncel_f
            birim = "$" if varlik in ["BTC", "ETH", "PAXG"] else "TL"
            
            if birim == "$":
                toplam_maliyet_tl += (t_m * usd_try)
                toplam_guncel_deger_tl += (g_d * usd_try)
            else:
                toplam_maliyet_tl += t_m
                toplam_guncel_deger_tl += g_d
                
            cuzdan_sonuclari.append({
                "Varlık": varlik, "Adet": a, "Maliyet": f"{m:.2f} {birim}",
                "Güncel": f"{guncel_f:.2f} {birim}", "K/Z %": ((g_d - t_m) / t_m) * 100 if t_m > 0 else 0
            })

    if cuzdan_sonuclari:
        st.dataframe(pd.DataFrame(cuzdan_sonuclari), use_container_width=True)
        st.metric("🚀 Toplam Portföy Getirisi", f"{toplam_guncel_deger_tl - toplam_maliyet_tl:,.2f} ₺")

# --- 2. BÖLÜM: PİYASA VE GRAFİK ---
st.divider()
st.subheader("📊 Canlı Sinyaller")
st.dataframe(pd.DataFrame(analiz_data), use_container_width=True)

target = st.selectbox("Grafik İncele:", list(VARLIKLAR.keys()))
if target:
    d = fetch_finance_data(VARLIKLAR[target], selected_range)
    st.plotly_chart(go.Figure(data=[go.Candlestick(x=d.index, open=d['Open'], high=d['High'], low=d['Low'], close=d['Close'])]), use_container_width=True)
