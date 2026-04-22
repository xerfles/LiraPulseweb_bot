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

# Takip listemiz
VARLIKLAR = {
    "THYAO": "THYAO.IS", "TUPRS": "TUPRS.IS", "KCHOL": "KCHOL.IS", 
    "ASTOR": "ASTOR.IS", "AKBNK": "AKBNK.IS", "ASELS": "ASELS.IS", 
    "KONTR": "KONTR.IS", "MIATK": "MIATK.IS", "SASA": "SASA.IS", 
    "BTC": "BTC-USD", "ETH": "ETH-USD", "PAXG": "PAXG-USD"
}

@st.cache_data(ttl=300)
def fetch_finance_data(symbol, period):
    try:
        return yf.Ticker(symbol).history(period=period)
    except:
        return pd.DataFrame()

# --- CANLI VERİ ÇEKİMİ ---
analiz_data = []
anlik_fiyatlar = {}

for isim, sembol in VARLIKLAR.items():
    hist = fetch_finance_data(sembol, "5d") # Sadece son fiyat için kısa vade çekiyoruz
    if not hist.empty:
        fiyat = hist['Close'].iloc[-1]
        anlik_fiyatlar[isim] = fiyat
        analiz_data.append({"Varlık": isim, "Fiyat": fiyat})

# --- 💼 CÜZDAN BÖLÜMÜ (GÜNCELLENDİ) ---
with st.expander("💼 Kişisel Cüzdanım (Yönetmek İçin Tıklayın)", expanded=True): # Sorunu görebilmek için şimdilik açık kalsın
    st.info("Hisse seçmek için 'Varlık' sütununa tıklayın.")

    # Session State Başlatma
    if 'portfoy' not in st.session_state:
        st.session_state.portfoy = pd.DataFrame([
            {"Varlık": "THYAO", "Adet": 0.0, "Maliyet": 0.0}
        ])

    # Sütun Yapılandırması
    column_config = {
        "Varlık": st.column_config.SelectboxColumn(
            "Varlık Seçiniz",
            options=list(VARLIKLAR.keys()),
            required=True,
        ),
        "Adet": st.column_config.NumberColumn("Adet", min_value=0, format="%.4f"),
        "Maliyet": st.column_config.NumberColumn("Birim Maliyet", min_value=0, format="%.2f")
    }

    # Data Editor
    edited_df = st.data_editor(
        st.session_state.portfoy,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="wallet_editor" # Benzersiz anahtar ekledik
    )
    st.session_state.portfoy = edited_df

    # Hesaplamalar
    if not edited_df.empty:
        try:
            usd_try = yf.Ticker("TRY=X").history(period="1d")['Close'].iloc[-1]
            
            cuzdan_ozet = []
            toplam_deger_tl = 0
            
            for _, row in edited_df.iterrows():
                v = row["Varlık"]
                if v in anlik_fiyatlar:
                    f = anlik_fiyatlar[v]
                    a = row["Adet"]
                    m = row["Maliyet"]
                    guncel_deger = a * f
                    
                    if v in ["BTC", "ETH", "PAXG"]:
                        toplam_deger_tl += (guncel_deger * usd_try)
                    else:
                        toplam_deger_tl += guncel_deger
                        
                    cuzdan_ozet.append({
                        "Varlık": v, "Adet": a, "Güncel Değer": f"{guncel_deger:,.2f}"
                    })
            
            if cuzdan_ozet:
                st.write("📊 Anlık Portföy Özeti")
                st.table(pd.DataFrame(cuzdan_ozet))
                st.metric("💰 Toplam Portföy Değeri (TL)", f"{toplam_deger_tl:,.2f} ₺")
        except Exception as e:
            st.warning("Hesaplama yapılırken bir veri hatası oluştu.")

# --- DİĞER BÖLÜMLER (PİYASA ANALİZİ) ---
st.divider()
st.subheader("📊 Genel Piyasa Durumu")
if analiz_data:
    st.dataframe(pd.DataFrame(analiz_data), use_container_width=True)
