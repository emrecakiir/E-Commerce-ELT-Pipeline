import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# Sayfa Ayarları
st.set_page_config(page_title="Olist Analitik Yönetim Paneli", layout="wide")

# Veritabanı Bağlantısı ve Veri Çekme (Bellek Optimizasyonu)
# Veriyi tek seferde RAM'e (cache) alıyoruz ki kullanıcı her filtre değiştirdiğinde veritabanı yorulmasın.
@st.cache_data
def veri_yukle():
    engine = create_engine('postgresql://postgres:postgres@db:5432/ecommerce_db')
    df_siparis = pd.read_sql("SELECT * FROM olist_analytics.temiz_musteri_siparisleri;", engine)
    df_urun = pd.read_sql("SELECT * FROM olist_analytics.temiz_urun_satislari;", engine)
    
    # Python (Pandas) ile tarih özelliklerini çıkarıyoruz (İleri Analiz İçin)
    df_siparis['yil'] = df_siparis['siparis_tarihi'].dt.year
    df_siparis['siparis_saati'] = df_siparis['siparis_tarihi'].dt.hour
    df_siparis['teslimat_suresi_gun'] = (df_siparis['teslimat_tarihi'] - df_siparis['siparis_tarihi']).dt.days
    return df_siparis, df_urun

df_siparis_ham, df_urun = veri_yukle()


# SOL MENÜ: İNTERAKTİF FİLTRELER (SCENARIOS)

st.sidebar.header("Kontrol Paneli (Filtreler)")
st.sidebar.markdown("Senaryo analizleri için aşağıdaki filtreleri kullanabilirsiniz.")

# Yıl Filtresi
secilen_yillar = st.sidebar.multiselect(
    "Yıl Seçiniz:",
    options=sorted(df_siparis_ham['yil'].dropna().unique()),
    default=sorted(df_siparis_ham['yil'].dropna().unique())
)

# Eyalet Filtresi
secilen_eyaletler = st.sidebar.multiselect(
    "Müşteri Eyaleti Seçiniz (Örn: SP, RJ):",
    options=sorted(df_siparis_ham['musteri_eyaleti'].dropna().unique()),
    default=sorted(df_siparis_ham['musteri_eyaleti'].dropna().unique())
)

# Veriyi Filtrelere Göre Anlık Olarak Kırpma İşlemi
df_siparis = df_siparis_ham[
    (df_siparis_ham['yil'].isin(secilen_yillar)) & 
    (df_siparis_ham['musteri_eyaleti'].isin(secilen_eyaletler))
]

# Ana Başlık
st.title("Olist E-Ticaret Yönetim ve Analitik Paneli")
st.markdown("---")


# ÜST KPI KARTLARI (Dinamik)

col1, col2, col3, col4 = st.columns(4)

toplam_ciro = df_siparis['toplam_harcama'].sum()
toplam_siparis = df_siparis['order_id'].nunique()
sepet_ortalamasi = toplam_ciro / toplam_siparis if toplam_siparis > 0 else 0
ort_teslimat = df_siparis['teslimat_suresi_gun'].mean()

with col1:
    st.metric(label="Toplam Sipariş Hacmi", value=f"{toplam_siparis:,}")
with col2:
    st.metric(label="Gerçekleşen Ciro (BRL)", value=f"R$ {toplam_ciro:,.2f}")
with col3:
    st.metric(label="Ortalama Sepet Tutarı (AOV)", value=f"R$ {sepet_ortalamasi:,.2f}")
with col4:
    st.metric(label="Ortalama Teslimat", value=f"{ort_teslimat:.1f} Gün")

st.markdown("---")


# SEKME (TAB) MİMARİSİ: DERİNLEMESİNE ANALİZLER

tab1, tab2, tab3 = st.tabs(["Satış ve Finans Analitiği", "Operasyon ve Lojistik", "Müşteri Davranışları (RFM)"])

# ----------------- SEKME 1: SATIŞ VE FİNANS -----------------
with tab1:
    st.subheader("Finansal Performans Metrikleri")
    g1_col1, g1_col2 = st.columns(2)
    
    with g1_col1:
        # Dinamik Aylık Trend
        trend_df = df_siparis.set_index('siparis_tarihi').resample('M')['toplam_harcama'].sum().reset_index()
        fig_trend = px.area(trend_df, x='siparis_tarihi', y='toplam_harcama', title="Zaman İçinde Ciro Gelişimi (Aylık)",
                            labels={'siparis_tarihi': 'Tarih', 'toplam_harcama': 'Ciro (BRL)'})
        fig_trend.update_traces(line_color='#1f77b4', fillcolor='rgba(31, 119, 180, 0.3)')
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with g1_col2:
        # Sipariş ID'leri üzerinden ürün tablosunu filtrelenen siparişlerle birleştirme
        df_birlestirilmis = pd.merge(df_siparis[['order_id']], df_urun, on='order_id', how='inner')
        kategori_df = df_birlestirilmis.groupby('urun_kategorisi')['urun_fiyati'].sum().reset_index()
        kategori_df = kategori_df.sort_values(by='urun_fiyati', ascending=False).head(10)
        kategori_sozlugu = {
            'health_beauty': 'Sağlık & Güzellik',
            'watches_gifts': 'Saat & Hediyelik',
            'bed_bath_table': 'Yatak, Banyo & Ev Tekstili',
            'sports_leisure': 'Spor & Serbest Zaman',
            'computers_accessories': 'Bilgisayar & Aksesuarları',
            'furniture_decor': 'Mobilya & Dekorasyon',
            'cool_stuff': 'İlginç Ürünler',
            'housewares': 'Ev Eşyaları',
            'auto': 'Otomotiv',
            'garden_tools': 'Bahçe Aletleri'
        }
        
        kategori_df['urun_kategorisi'] = kategori_df['urun_kategorisi'].replace(kategori_sozlugu)
        fig_kategori = px.bar(kategori_df, y='urun_kategorisi', x='urun_fiyati', orientation='h',
                              title="En Yüksek Gelir Getiren 10 Kategori",
                              labels={'urun_kategorisi': 'Kategori', 'urun_fiyati': 'Toplam Gelir'})
        fig_kategori.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_kategori, use_container_width=True)

# ----------------- SEKME 2: OPERASYON VE LOJİSTİK -----------------
with tab2:
    st.subheader("Lojistik ve Sipariş İşleme Performansı")
    g2_col1, g2_col2 = st.columns(2)
    
    with g2_col1:
        # Teslimat Süreleri Dağılımı (Kutu Grafiği / Outlier Analizi)
        fig_box = px.box(df_siparis, x='musteri_eyaleti', y='teslimat_suresi_gun',
                         title="Eyaletlere Göre Teslimat Süresi Dağılımı ve Sapmalar",
                         labels={'musteri_eyaleti': 'Eyalet', 'teslimat_suresi_gun': 'Teslimat (Gün)'})
        st.plotly_chart(fig_box, use_container_width=True)
        
    with g2_col2:
        # Müşterilerin Hangi Saatlerde Sipariş Verdiği (Yoğunluk Analizi)
        saat_df = df_siparis['siparis_saati'].value_counts().reset_index()
        saat_df.columns = ['Saat', 'Sipariş Sayısı']
        saat_df = saat_df.sort_values(by='Saat')
        
        fig_saat = px.bar(saat_df, x='Saat', y='Sipariş Sayısı', 
                          title="Günün Saatlerine Göre Sipariş Yoğunluğu",
                          labels={'Saat': 'Günün Saati (0-23)'})
        st.plotly_chart(fig_saat, use_container_width=True)

# ----------------- SEKME 3: MÜŞTERİ DAVRANIŞLARI -----------------
with tab3:
    st.subheader("Müşteri Segmentasyonu ve Değer Analizi")
    g3_col1, g3_col2 = st.columns(2)

    with g3_col1:
        st.markdown("**En Sadık ve Değerli 15 Müşteri (RFM Analizi)**")
        
        # Dinamik RFM metriklerinin hesaplanması
        rfm_df = df_siparis.groupby('customer_unique_id').agg(
            son_siparis_tarihi=('siparis_tarihi', 'max'),
            siparis_sikligi=('order_id', 'nunique'),
            toplam_harcama=('toplam_harcama', 'sum')
        ).reset_index().sort_values(by='toplam_harcama', ascending=False).head(15)
        
        # Veri gizliliği ve arayüz okunabilirliği için Müşteri ID maskeleme (Data Masking)
        rfm_df['Müşteri ID'] = [f"{str(uid)[:4]}...{str(uid)[-4:]}" for uid in rfm_df['customer_unique_id']]
        
        # Formatlanmış veri setinin gösterimi
        st.dataframe(
            rfm_df[['Müşteri ID', 'son_siparis_tarihi', 'siparis_sikligi', 'toplam_harcama']].set_index('Müşteri ID'),
            use_container_width=True
        )

    with g3_col2:
        # Sipariş durumlarına göre frekans dağılımının çıkarılması
        durum_df = df_siparis['siparis_durumu'].value_counts().reset_index()
        durum_df.columns = ['Durum', 'Adet']
        
        # Oransal dağılımın görselleştirilmesi
        fig_pie = px.pie(durum_df, names='Durum', values='Adet', hole=0.4)
        
        # UI/UX optimizasyonu: Görsel karmaşayı önlemek adına grafik içi etiketlerin gizlenmesi
        fig_pie.update_traces(textinfo='none')
        fig_pie.update_layout(
            title_text='Sipariş Durumlarına Göre Dağılım', 
            title_x=0.5, 
            title_font_size=16
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)