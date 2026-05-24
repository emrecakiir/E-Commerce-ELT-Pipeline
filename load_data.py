import os
import pandas as pd
from sqlalchemy import create_engine, text

# Veritabanı motorunu çalıştırıyoruz
engine = create_engine('postgresql://postgres:postgres@localhost:5432/ecommerce_db')

# Python'a "Eğer yoksa olist_raw ve olist_analytics odasını bizzat sen aç" diyoruz 
with engine.begin() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS olist_raw;"))
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS olist_analytics;"))

data_klasoru = "data"

print(" Veriler olist_raw şemasına yüklenmeye başlıyor...\n")

# Klasördeki tüm dosyaları tek tek geziyoruz
for dosya in os.listdir(data_klasoru):
    if dosya.endswith(".csv"):
        dosya_yolu = os.path.join(data_klasoru, dosya)
        
        # Dosya adındaki .csv kısmını atıp tablo adı yapıyoruz
        tablo_adi = dosya.replace(".csv", "")
        
        print(f" {tablo_adi} okunuyor ve veritabanına taşınıyor...")
        
        # Pandas ile CSV'yi okuyoruz
        df = pd.read_csv(dosya_yolu)
        
        # Veriyi PostgreSQL'deki olist_raw şemasına basıyoruz
        df.to_sql(name=tablo_adi, con=engine, schema='olist_raw', if_exists='replace', index=False)
        
print("\nVeriler yüklendi")