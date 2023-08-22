import random
import streamlit as st
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import pandas as pd
from dateutil.relativedelta import relativedelta

# Veriyi CSV dosyasından oku
data = pd.read_csv('data/file_out2.csv')

# Veriyi güvenli bir kopya olarak al
df = data.copy()

# İstenmeyen sütunu ('Unnamed: 0') düşür
df.drop(['Unnamed: 0'], axis=1, inplace=True)

# Eksik değerleri içeren satırları kaldır
df.dropna(axis=0, how='any', inplace=True)

# 'Date' sütununu tarih formatına çevir
df['Date'] = pd.to_datetime(df['Date'])

# Birim fiyatı hesapla (Toplam Satış / Miktar)
df['UnitPrice'] = df['TotalSales'] / df['Quantity']

# 'Date' sütunundan yıl ve ay bilgilerini çıkar
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month

# Ürün özetini hesapla: Ürün bazında miktar, toplam satış ve ortalama birim fiyat
product_summary = df.groupby('ProductID').agg(
    {'Quantity': 'sum', 'TotalSales': 'sum', 'UnitPrice': 'mean'}).reset_index()

# Ürün satışlarını içeren bir data frame oluştur
product_sales_df = product_summary[['ProductID', 'UnitPrice', 'Quantity', 'TotalSales']].copy()

# Günlük ortalama satış miktarını hesapla
average_daily_sales = df.groupby(['Date', 'ProductID'])['Quantity'].sum().reset_index()
average_daily_sales = average_daily_sales.groupby('ProductID')['Quantity'].mean().reset_index()

# Uygulama başlığını belirle
st.title('Ciro Simülasyonu')



def create_test():

    # Kullanıcıdan girişleri al
    baslangic_ay = st.number_input("Başlangıç Ay:", min_value=1, max_value=12, step=1, value=6)
    baslangic_yil = st.number_input("Başlangıç Yıl:", min_value=2020, max_value=2023, step=1, value=2020)
    bitis_ay = st.number_input("Bitiş Ay:", min_value=1, max_value=12, step=1, value=6)
    bitis_yil = st.number_input("Bitiş Yıl:", min_value=2021, max_value=2023, step=1, value=2021)
    kac_ay_ileri = st.number_input("Tahmini aylık süre:", min_value=1, max_value=120, step=1, value=12)
    en_onemli_kac_urun = st.number_input("Bir ay içerisinde en fazla satış gerçekleştiren kaç adet ürün dikkate alınmalıdır?", min_value=1,
                                         max_value=25, step=1, value=5)
    cironu_hangi_yuzdelik_dilimi_kadar_etkileyen_urun_satis_oranı = st.number_input(
        "Bir ay içerisinde kazancı yüzde ne kadar etkileyen ürünler dikkate alınmalıdır?",
        min_value=0.00, max_value=1.00, step=0.01, value=0.03)
    urune_gelebilecek_zam_orani_alt = st.number_input("Minimum Zam Oranı:", min_value=1.00, max_value=2.000, step=0.01,
                                                      value=1.0)
    urune_gelebilecek_zam_orani_ust = st.number_input("Maksimum Zam Oranı:", min_value=1.00, max_value=2.000, step=0.01,
                                                      value=1.20)
    yuzde_ne_kadar_fazla_ciro_artsin = st.number_input("Beklenen ciro artış değeri (%):", min_value=1.0, max_value=5.0,
                                                       step=0.1, value=1.2)
    gunluk_islem_sayisi = st.number_input("Günlük İşlem Sayısı", min_value=0,
                                          max_value=int(average_daily_sales['Quantity'].max()), step=1,
                                          value=int(average_daily_sales['Quantity'].mean()))
    deneme_sayisi = st.number_input("Kaç kez test edilsin?", min_value=1, max_value=100, step=1, value=10)

    # Tarih hesaplamaları
    start_date = pd.Timestamp(f'{baslangic_yil}-{baslangic_ay}-01')
    end_date = pd.Timestamp(f'{bitis_yil}-{bitis_ay}-01')
    time_delta = relativedelta(end_date, start_date)
    num_months = time_delta.years * 12 + time_delta.months
    new_start_date = start_date - relativedelta(months=num_months)
    new_end_date = end_date + relativedelta(months=kac_ay_ileri)

    # Veriyi filtrele
    df_target = df[(df['Date'] >= new_start_date) & (df['Date'] <= end_date)]
    total_sales_target_month = df_target['TotalSales'].sum()
    threshold = total_sales_target_month * cironu_hangi_yuzdelik_dilimi_kadar_etkileyen_urun_satis_oranı

    # En çok satan ürünleri belirle
    top_selling_products_target_month = df_target.groupby('ProductID')['TotalSales'].sum().reset_index()
    top_selling_products_target_month = top_selling_products_target_month[
        top_selling_products_target_month['TotalSales'] > threshold]
    top_selling_products_target_month['Contribution'] = top_selling_products_target_month[
                                                            'TotalSales'] / total_sales_target_month * 100
    top_selling_products_target_month = pd.merge(top_selling_products_target_month,
                                                 product_sales_df[['ProductID', 'Quantity', 'UnitPrice']],
                                                 on='ProductID', how='left')
    top_selling_products_target_month = top_selling_products_target_month.astype({"Quantity": 'int'})
    top_selling_products_target_month = top_selling_products_target_month.sort_values(by='TotalSales', ascending=False)
    product_ids = top_selling_products_target_month['ProductID'].tolist()

    # Test verileri oluştur
    test_data = pd.DataFrame(columns=['Date', 'ProductID', 'UnitPrice', 'Quantity', 'TotalSales'])

    # Her bir tarih için veri oluşturma
    if st.button("Test it!"):
        log = []
        for num in range(deneme_sayisi):
            i = 0
            for date in pd.date_range(end_date, new_end_date, freq='D'):
                if i % 2 == 0:
                    product_id = random.choice(product_ids[:en_onemli_kac_urun + 1])
                else:
                    product_id = random.choice(product_ids)
                i+=1
                for _ in range(int(gunluk_islem_sayisi)):
                    unit_price = \
                    top_selling_products_target_month[top_selling_products_target_month['ProductID'] == product_id][
                        'UnitPrice'].values[0] * (
                        random.uniform(urune_gelebilecek_zam_orani_alt, urune_gelebilecek_zam_orani_ust))
                    quantity = int(average_daily_sales[average_daily_sales['ProductID'] == product_id]['Quantity'])
                    total_sales = unit_price * quantity

                    test_data = test_data.append({
                        'Date': date,
                        'ProductID': product_id,
                        'UnitPrice': unit_price,
                        'Quantity': quantity,
                        'TotalSales': total_sales
                    }, ignore_index=True)

            test_sales = test_data['TotalSales'].sum()
            target_sales = df_target['TotalSales'].sum()*yuzde_ne_kadar_fazla_ciro_artsin
            if test_sales > target_sales:
                log.append(test_data)
                gelecek_trendi = test_data.groupby('Date')['TotalSales'].sum()

                st.write("Test Verisi Cirosu: ", int(test_data['TotalSales'].sum()))
                st.write("Referans Verisi Cirosu: ", int(df_target['TotalSales'].sum()))
                st.write("Beklenen Ciro Artış Hedefi: ", int(target_sales))
                st.write("Cirolar Arasındaki Fark", int(target_sales)-int(test_data['TotalSales'].sum()))

                st.subheader("Gelecek Trend Analizi")
                st.line_chart(gelecek_trendi)

                # Aylık kazançları hesaplama
                monthly_data = gelecek_trendi.resample('M').sum()
                monthly_data.index = monthly_data.index.strftime('%B')
                st.subheader('Aylık Kazanç Grafiği')
                st.bar_chart(monthly_data)

                st.write("Aylık Kazanç Verileri")
                st.write(monthly_data)

                break


def customer_analysis():
    ay = st.number_input("Ay:", min_value=1, max_value=12, step=1, value=1)
    yil = st.number_input("Yıl:", min_value=2000, max_value=2023, step=1, value=2021)

    filtre = (df['Month'] == ay) & (df['Year'] == yil)
    secilen_veriler = df[filtre]

    musteri_ciro = secilen_veriler.groupby('CustomerID')['TotalSales'].sum()
    en_cok_harcayanlar = musteri_ciro.nlargest(10)

    st.subheader("Müşteri Bazlı Analiz: En Çok Harcayanlar")
    st.bar_chart(en_cok_harcayanlar)

def product_analysis():
    ay = st.number_input("Ay:", min_value=1, max_value=12, step=1, value=1)
    yil = st.number_input("Yıl:", min_value=2000, max_value=2023, step=1, value=2021)

    filtre = (df['Month'] == ay) & (df['Year'] == yil)
    secilen_veriler = df[filtre]

    urun_satis = secilen_veriler.groupby('ProductID')['Quantity'].sum()
    en_cok_satan_urunler = urun_satis.nlargest(10)

    st.subheader("Ürün Bazlı Analiz: En Çok Satan Ürünler")
    st.bar_chart(en_cok_satan_urunler)


def discount_analysis():
    ay = st.number_input("Ay:", min_value=1, max_value=12, step=1, value=1)
    yil = st.number_input("Yıl:", min_value=2000, max_value=2023, step=1, value=2021)

    filtre = (df['Month'] == ay) & (df['Year'] == yil)
    secilen_veriler = df[filtre]

    indirimli_satislar = secilen_veriler[secilen_veriler['Discount'] > 0]
    indirim_oranlari = indirimli_satislar.groupby('Discount')['TotalSales'].sum()

    st.subheader("İndirim Bazlı Analiz")
    st.bar_chart(indirim_oranlari.nlargest(10))


def trend_analysis():
    ay = st.number_input("Ay:", min_value=1, max_value=12, step=1, value=1)
    yil = st.number_input("Yıl:", min_value=2000, max_value=2023, step=1, value=2021)

    filtre = (df['Month'] == ay) & (df['Year'] == yil)
    secilen_veriler = df[filtre]

    ciro_trendi = secilen_veriler.groupby('Date')['TotalSales'].sum()

    st.subheader("Ciro Trendi Analizi")
    st.line_chart(ciro_trendi)

st.sidebar.markdown("# Menü")
page = st.sidebar.radio("Gitmek istediğiniz sayfayı seçin:",
                        ('Simülasyon Testi','Müşteri Bazlı Analiz', 'Ürün Bazlı Analiz', 'İndirim Bazlı Analiz', 'Ciro Trendi Analizi'))

if page == 'Müşteri Bazlı Analiz':
    customer_analysis()
elif page == 'Ürün Bazlı Analiz':
    product_analysis()
elif page == 'İndirim Bazlı Analiz':
    discount_analysis()
elif page == 'Ciro Trendi Analizi':
    trend_analysis()
elif page == 'Simülasyon Testi':
    create_test()

