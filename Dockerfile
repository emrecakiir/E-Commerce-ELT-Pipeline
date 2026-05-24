# Python tabanlı hafif ve resmi bir imaj kullanıyoruz
FROM python:3.9-slim

# Konteyner içindeki çalışma odamızı belirliyoruz
WORKDIR /app

# Gerekli kütüphanelerin listesini kopyalıyoruz
COPY requirements.txt .

# Kütüphaneleri yüklüyoruz
RUN apt-get update && apt-get install -y libpq-dev gcc \
    && pip install --no-cache-dir -r requirements.txt

# Projedeki tüm kodlarımızı içeri kopyalıyoruz
COPY . .

# Streamlit'in dışarı yayın yapacağı portu açıyoruz
EXPOSE 8501

# Konteyner çalışınca otomatik olarak Streamlit'i başlat
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]