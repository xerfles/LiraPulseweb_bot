import streamlit as st
import yfinance as yf
import pandas as pd

# Sayfa Ayarları
st.set_page_config(page_title="Alper Finans Portföy Paneli", layout="wide")

st.title("🚀 Kişisel Portföy ve Teknik Analiz Paneli")
st.markdown("Bu panel; BIST endekslerini, seçili hisse senetlerini ve kripto varlıkları anlık olarak analiz eder.")

# Takip Listeleri
ENDEKSLER = {"BIST 100": "XU100.IS", "BIST 30": "XU030.IS"}
VARLIKLAR = {
    "THYAO": "THYAO.IS", "TUPRS": "TUPRS.IS", "KCHOL": "KCHOL.IS", 
    "ASTOR": "ASTOR.IS", "AKBNK": "AKBNK.IS", "ASELS": "ASELS.IS", 
    "KONTR": "KONTR.IS", "MIATK": "MIATK.IS", "SASA": "SASA.IS", 
    "BTC": "BTC-USD", "ETH": "ETH-USD", "PAXG": "PAXG-USD"
}

def get_data(sembol):
    ticker = yf.Ticker(sembol)
    hist = ticker.history(period="1y")
    return hist

# --- 1. BÖLÜM: ENDEKSLER (Üst Şerit) ---
st.subheader("🏗️ Piyasa Genel Durumu")
cols = st.columns(len(ENDEKSLER))

for i, (isim, sembol) in enumerate(ENDEKSLER.items()):
    try:
        data = get_data(sembol)
        guncel = data['Close'].iloc[-1]
        degisim = ((guncel - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
        cols[i].metric(label=isim, value=f"{guncel:,.2f}", delta=f"{degisim:.2f}%")
    except:
        cols[i].error(f"{isim} verisi alınamadı.")

st.divider()

# --- 2. BÖLÜM: DETAYLI VARLIK ANALİZİ ---
st.subheader("💎 Varlık Bazlı Detaylı Analiz")

analiz_listesi = []

for isim, sembol in VARLIKLAR.items():
    try:
        data = get_data(sembol)
        guncel = data['Close'].iloc[-1]
        
        # Değişimler
        gunluk = ((guncel - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
        haftalik = ((guncel - data['Close'].iloc[-5]) / data['Close'].iloc[-5]) * 100
        aylik = ((guncel - data['Close'].iloc[-21]) / data['Close'].iloc[-21]) * 100
        yillik = ((guncel - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
        
        # Teknik Seviyeler
        destek = data['Close'].tail(50).mean()
        direnc = data['Close'].tail(20).max()
        
        analiz_listesi.append({
            "Varlık": isim,
            "Fiyat": round(guncel, 2),
            "Günlük %": round(gunluk, 2),
            "Haftalık %": round(haftalik, 2),
            "Aylık %": round(aylik, 2),
            "Yıllık %": round(yillik, 2),
            "Destek (50G SMA)": round(destek, 2),
            "Direnç (20G Zirve)": round(direnc, 2)
        })
    except:
        continue

df = pd.DataFrame(analiz_listesi)

# Tabloyu Renklendirme ve Gösterme
def color_delta(val):
    color = 'green' if val > 0 else 'red'
    return f'color: {color}'

st.dataframe(df.style.map(color_delta, subset=['Günlük %', 'Haftalık %', 'Aylık %', 'Yıllık %']), use_container_width=True)

st.info("💡 Destek seviyesi alım fırsatlarını, Direnç seviyesi ise kar satışlarını takip etmek için teknik bir göstergedir.")
