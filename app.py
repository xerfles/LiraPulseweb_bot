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
st.markdown("Algoritmik piyasa takibi, canlı fiyatlama ve interaktif cüzdan yönetimi.")

VARLIKLAR = {
    "THYAO": "THYAO.IS", "TUPRS": "TUPRS.IS", "KCHOL": "KCHOL.IS", 
    "ASTOR": "ASTOR.IS", "AKBNK": "AKBNK.IS", "ASELS": "ASELS.IS", 
    "KONTR": "KONTR.IS", "MIATK": "MIATK.IS", "SASA": "SASA.IS", 
    "BTC": "BTC-USD", "ETH": "ETH-USD", "PAXG": "PAXG-USD"
}

@st.cache_data(ttl=300)
def fetch_finance_data(symbol, period):
    return yf.Ticker(symbol).history(period=period)

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# --- CANLI VERİ ÇEKİMİ ---
analiz_data = []
anlik_fiyatlar = {}

for isim, sembol in VARLIKLAR.items():
    try:
        hist = fetch_finance_data(sembol, "1y")
        if hist.empty: continue
        
        current_price = hist['Close'].iloc[-1]
        anlik_fiyatlar[isim] = current_price
        
        daily_change = ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
        rsi_val = calculate_rsi(hist).iloc[-1]
        sma50 = hist['Close'].tail(50).mean()
        volume = hist['Volume'].iloc[-1]
        std_dev = hist['Close'].tail(20).std()
        
        analiz_data.append({
            "Varlık": isim,
            "Fiyat": current_price,
            "Günlük %": daily_change,
            "RSI (14)": rsi_val,
            "Destek (SMA50)": sma50,
            "Volatilite": std_dev,
            "Hacim": volume,
            "Durum": "🔴 Aşırı Alım" if rsi_val > 70 else ("🟢 Aşırı Satım" if rsi_val < 30 else "⚪ Stabil")
        })
    except: continue

df_analiz = pd.DataFrame(analiz_data)

# --- 1. BÖLÜM: İNTERAKTİF CÜZDAN (WALLET) ---
st.subheader("💼 Kişisel Cüzdanım (İnteraktif Kar / Zarar Hesaplayıcı)")
st.info("Aşağıdaki tabloya tıklayarak elinizdeki varlıkları, adetlerini ve maliyetlerinizi düzenleyebilirsiniz. Satır ekleyip çıkarabilirsiniz, panel anlık fiyatlarla toplam getirinizi otomatik hesaplar.")

# Varsayılan örnek portföy
if 'portfoy' not in st.session_state:
    st.session_state['portfoy'] = pd.DataFrame({
        "Varlık": ["THYAO", "TUPRS", "BTC"],
        "Adet": [100.0, 50.0, 0.05],
        "Maliyet": [250.0, 150.0, 65000.0]
    })

# Kullanıcının tabloyu canlı olarak düzenlemesine izin veren modül
edited_df = st.data_editor(st.session_state['portfoy'], num_rows="dynamic", use_container_width=True)
st.session_state['portfoy'] = edited_df

# Kar/Zarar Matematiği
cuzdan_sonuclari = []
toplam_maliyet_tl = 0
toplam_guncel_deger_tl = 0

# Kriptolar için anlık Dolar kurunu çekiyoruz
usd_try_data = fetch_finance_data("TRY=X", "1d")
dolar_kuru = usd_try_data['Close'].iloc[-1] if not usd_try_data.empty else 32.50

for index, row in edited_df.iterrows():
    varlik = row["Varlık"]
    adet = row["Adet"]
    maliyet = row["Maliyet"]
    
    if varlik in anlik_fiyatlar and adet > 0:
        guncel_fiyat = anlik_fiyatlar[varlik]
        toplam_maliyet = adet * maliyet
        guncel_deger = adet * guncel_fiyat
        kar_zarar_brm = guncel_deger - toplam_maliyet
        kar_zarar_yuzde = (kar_zarar_brm / toplam_maliyet) * 100 if toplam_maliyet > 0 else 0
        
        birim = "$" if varlik in ["BTC", "ETH", "PAXG"] else "TL"
        
        # Genel toplam için her şeyi TL'ye çeviriyoruz
        if birim == "$":
            toplam_maliyet_tl += (toplam_maliyet * dolar_kuru)
            toplam_guncel_deger_tl += (guncel_deger * dolar_kuru)
        else:
            toplam_maliyet_tl += toplam_maliyet
            toplam_guncel_deger_tl += guncel_deger
            
        cuzdan_sonuclari.append({
            "Varlık": varlik,
            "Adet": adet,
            "Maliyet": f"{maliyet:.2f} {birim}",
            "Güncel Fiyat": f"{guncel_fiyat:.2f} {birim}",
            "Güncel Değer": f"{guncel_deger:.2f} {birim}",
            "Net K/Z": kar_zarar_brm,
            "Getiri %": kar_zarar_yuzde
        })

if cuzdan_sonuclari:
    cuzdan_df = pd.DataFrame(cuzdan_sonuclari)
    def color_kz(val):
        color = '#00FF00' if val > 0 else '#FF0000'
        return f'color: {color}'
    
    st.dataframe(cuzdan_df.style.format({
        "Net K/Z": "{:.2f}",
        "Getiri %": "{:.2f}%"
    }).map(color_kz, subset=["Net K/Z", "Getiri %"]), use_container_width=True)
    
    genel_kz_tl = toplam_guncel_deger_tl - toplam_maliyet_tl
    genel_kz_yuzde = (genel_kz_tl / toplam_maliyet_tl) * 100 if toplam_maliyet_tl > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("💼 Toplam Yatırım Maliyeti (TL)", f"{toplam_maliyet_tl:,.2f} ₺")
    col2.metric("💰 Güncel Bakiye (TL)", f"{toplam_guncel_deger_tl:,.2f} ₺")
    col3.metric("🚀 Toplam Portföy Getirisi", f"{genel_kz_tl:,.2f} ₺", f"{genel_kz_yuzde:.2f}%")

# --- 2. BÖLÜM: PİYASA SİNYALLERİ ---
st.divider()
st.subheader("📊 Piyasa Tarama ve Canlı Sinyaller")
st.dataframe(df_analiz.style.format({
    "Fiyat": "{:.2f}", 
    "Günlük %": "{:.2f}", 
    "RSI (14)": "{:.2f}", 
    "Destek (SMA50)": "{:.2f}",
    "Volatilite": "{:.2f}",
    "Hacim": "{:,.0f}"
}), use_container_width=True)

# --- 3. BÖLÜM: GRAFİK ---
st.divider()
st.subheader("🔍 İnteraktif Grafik ve Trend Analizi")
target = st.selectbox("Detaylı incelemek istediğiniz varlığı seçin:", list(VARLIKLAR.keys()))

if target:
    detail_data = fetch_finance_data(VARLIKLAR[target], selected_range)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=detail_data.index,
                open=detail_data['Open'], high=detail_data['High'],
                low=detail_data['Low'], close=detail_data['Close'], name='Fiyat'))
                
    detail_data['SMA20'] = detail_data['Close'].rolling(window=20).mean()
    fig.add_trace(go.Scatter(x=detail_data.index, y=detail_data['SMA20'], 
                             line=dict(color='orange', width=1.5), name='SMA 20'))
                             
    fig.update_layout(title=f"{target} Teknik Analiz Grafiği", 
                      xaxis_rangeslider_visible=False, 
                      template="plotly_dark",
                      height=500)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'><b>LiraPulse Terminal</b> | Veriler anlık olarak yfinance altyapısı üzerinden işlenmektedir.</p>", unsafe_allow_html=True)
