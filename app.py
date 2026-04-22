import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="Alper Finans Paneli", layout="wide")

# Otomatik yenileme veya manuel yenileme butonu
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🚀 Kişisel Portföy ve Teknik Analiz Paneli")
with col2:
    st.write("") # Hizalama boşluğu
    if st.button("🔄 Verileri Yenile"):
        st.cache_data.clear() # Önbelleği temizle
        st.rerun() # Sayfayı güncel verilerle yenile

st.markdown("Bu panel; BIST endekslerini, seçili hisse senetlerini ve kripto varlıkları anlık olarak analiz eder.")

ENDEKSLER = {"BIST 100": "XU100.IS", "BIST 30": "XU030.IS"}
VARLIKLAR = {
    "THYAO": "THYAO.IS", "TUPRS": "TUPRS.IS", "KCHOL": "KCHOL.IS", 
    "ASTOR": "ASTOR.IS", "AKBNK": "AKBNK.IS", "ASELS": "ASELS.IS", 
    "KONTR": "KONTR.IS", "MIATK": "MIATK.IS", "SASA": "SASA.IS", 
    "BTC": "BTC-USD", "ETH": "ETH-USD", "PAXG": "PAXG-USD"
}

@st.cache_data(ttl=60) # 60 saniyelik önbellek (Ban yememek için)
def get_data(sembol):
    ticker = yf.Ticker(sembol)
    return ticker.history(period="1y")

# --- 1. BÖLÜM: ENDEKSLER ---
st.subheader("🏗️ Piyasa Genel Durumu")
cols = st.columns(len(ENDEKSLER))

for i, (isim, sembol) in enumerate(ENDEKSLER.items()):
    try:
        data = get_data(sembol)
        if not data.empty and len(data) > 1:
            guncel = data['Close'].iloc[-1]
            degisim = ((guncel - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
            cols[i].metric(label=isim, value=f"{guncel:,.2f}", delta=f"{degisim:.2f}%")
        else:
            cols[i].warning(f"{isim} verisi alınamadı.")
    except:
        cols[i].warning(f"{isim} verisi alınamadı.")

st.divider()

# --- 2. BÖLÜM: DETAYLI VARLIK ANALİZİ ---
st.subheader("💎 Varlık Bazlı Detaylı Analiz")
analiz_listesi = []

for isim, sembol in VARLIKLAR.items():
    try:
        data = get_data(sembol)
        time.sleep(0.5) # Yahoo'yu yormamak için nefes alma süresi
        
        if len(data) < 21:
            continue
            
        guncel = data['Close'].iloc[-1]
        gunluk = ((guncel - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
        haftalik = ((guncel - data['Close'].iloc[-5]) / data['Close'].iloc[-5]) * 100
        aylik = ((guncel - data['Close'].iloc[-21]) / data['Close'].iloc[-21]) * 100
        yillik = ((guncel - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
        
        destek = data['Close'].tail(50).mean()
        direnc = data['Close'].tail(20).max()
        
        analiz_listesi.append({
            "Varlık": isim,
            "Fiyat": guncel,
            "Günlük %": gunluk,
            "Haftalık %": haftalik,
            "Aylık %": aylik,
            "Yıllık %": yillik,
            "Destek (50G SMA)": destek,
            "Direnç (20G Zirve)": direnc
        })
    except Exception as e:
        continue

df = pd.DataFrame(analiz_listesi)

def color_delta(val):
    color = '#00FF00' if val > 0 else '#FF0000'
    return f'color: {color}'

format_dict = {
    'Fiyat': '{:.2f}', 'Günlük %': '{:.2f}', 'Haftalık %': '{:.2f}',
    'Aylık %': '{:.2f}', 'Yıllık %': '{:.2f}', 
    'Destek (50G SMA)': '{:.2f}', 'Direnç (20G Zirve)': '{:.2f}'
}

styled_df = df.style.format(format_dict).map(color_delta, subset=['Günlük %', 'Haftalık %', 'Aylık %', 'Yıllık %'])

st.dataframe(styled_df, use_container_width=True)
st.info("💡 Destek seviyesi alım fırsatlarını, Direnç seviyesi ise kar satışlarını takip etmek için teknik bir göstergedir. Verileri anlık güncellemek için sağ üstteki butonu kullanabilirsiniz.")
