# MTU Zincirli Sözlük

Modern, kullanıcı dostu Türkçe eşanlamlılar sözlüğü uygulaması. Zincirleme eşanlamlılar keşfi, TDK entegrasyonu ve görselleştirme özellikleriyle.

## Özellikler

- **Kelime Arama**: Hızlı kelime arama ve eşanlamlılar listesi
- **Zincir Keşfi**: Eşanlamlılar zincirini ağaç ve grafik olarak görselleştirme
- **TDK Entegrasyonu**: Otomatik veri çekme ve güncelleme
- **Favoriler**: Kişisel favori kelimeler listesi
- **Sekmeli Arayüz**: Düzenli sekme yapısı (Ana Arama, Favoriler, Yönetim)
- **Sağ Tık Menüleri**: Kopyalama ve seçim işlemleri

## Kurulum

1. Gerekli bağımlılıkları yükleyin:
   ```bash
   pip install PySimpleGUI requests networkx matplotlib nltk
   ```

2. Uygulamayı çalıştırın:
   ```bash
   python sozluk_sade.py
   ```

## Yapılandırma

`config.json` dosyasından ayarları düzenleyin:
- `db_path`: Veritabanı dosyası yolu
- `theme`: PySimpleGUI tema adı
- `font`: Yazı tipi ve boyutu
- `esanlamli_buton_sayisi`: Gösterilecek eşanlamlı buton sayısı

## Kullanım

### Ana Arama Sekmesi
- Kelime girin ve "Ara" butonuna basın
- Eşanlamlı butonlarına tıklayarak zincir keşfedin
- "Zincir Göster" ile ağaç görünümü
- "Zincir Kaydet" ile JSON olarak kaydet

### Favoriler Sekmesi
- Kelimeleri favoriye ekleyin/silin
- Favori listesini yönetin

### Yönetim Sekmesi
- Yeni kelime ekleyin/güncelleyin
- Kelime silin
- CSV dışa aktarma/içe aktarma
- Yedekleme

## Teknik Detaylar

- **Veritabanı**: SQLite
- **GUI**: PySimpleGUI
- **Görselleştirme**: NetworkX + Matplotlib
- **API**: TDK Sözlük API'si

## Geliştirme

Kod modüler yapıya sahiptir:
- `SozlukYonetici` sınıfı: Veritabanı işlemleri
- `config.json`: Yapılandırma
- Sekmeli layout: Düzenli arayüz

## Lisans

Bu proje açık kaynak kodludur.