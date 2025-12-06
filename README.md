# MTU Zincirli Sözlük V2

Web tabanlı Türkçe sözlük uygulaması. Kelimeler arası bağlantıları (zincirli yapı) destekleyen, modern ve kullanıcı dostu bir sözlük sistemi.

## 🌟 Özellikler

- **Kelime Arama**: Hızlı ve kolay kelime arama
- **Zincirli Yapı**: Kelimeler arası ilişkili bağlantılar
- **Kelime Ekleme**: Yeni kelimeler ekleme ve düzenleme
- **Yerel Depolama**: Tarayıcı local storage ile veri saklama
- **Modern Arayüz**: Kullanıcı dostu ve responsive tasarım
- **Türkçe Dil Desteği**: Tamamen Türkçe arayüz

## 📂 Dosya Yapısı

```
MTU-Zincirli-Sözlük-V2/
├── index.html           # Ana HTML dosyası
├── styles.css          # Stil dosyası
├── app.js              # Uygulama mantığı
├── dictionary-data.js  # Veri yönetimi ve depolama
└── README.md           # Dokümantasyon
```

## 🚀 Kullanım

1. **Uygulamayı Açma**:
   - `index.html` dosyasını bir web tarayıcısında açın
   - Veya bir web sunucusunda barındırın

2. **Kelime Arama**:
   - Arama kutusuna kelime yazın
   - "Ara" butonuna tıklayın veya Enter tuşuna basın

3. **Yeni Kelime Ekleme**:
   - "Yeni Kelime Ekle" butonuna tıklayın
   - Formu doldurun:
     - Kelime
     - Tanım
     - Örnek cümle (opsiyonel)
     - İlişkili kelimeler (virgülle ayırarak)
     - Kategori (isim, fiil, sıfat, vb.)
   - "Kaydet" butonuna tıklayın

4. **İlişkili Kelimeler Arasında Gezinme**:
   - Kelime detaylarında gösterilen ilişkili kelimelere tıklayın
   - Otomatik olarak o kelimeye yönlendirilirsiniz

## 💾 Veri Depolama

Uygulama, verileri tarayıcının `localStorage` özelliğini kullanarak saklar:

- Veriler tarayıcıda yerel olarak saklanır
- İnternet bağlantısı gerektirmez
- Tarayıcı önbelleği temizlenene kadar veriler kalıcıdır

### Varsayılan Kelimeler

Uygulama şu varsayılan kelimelerle gelir:
- merhaba
- kitap
- okuma
- yazma
- öğrenme
- eğitim
- bilgisayar
- teknoloji
- internet
- iletişim

## 🔧 Teknik Detaylar

### Kullanılan Teknolojiler

- **HTML5**: Sayfa yapısı
- **CSS3**: Stil ve responsive tasarım
- **Vanilla JavaScript**: Uygulama mantığı
- **LocalStorage API**: Veri saklama

### Tarayıcı Desteği

Modern web tarayıcılarında çalışır:
- Chrome (önerilen)
- Firefox
- Safari
- Edge

### API Fonksiyonları

`dictionary-data.js` dosyasında sunulan fonksiyonlar:

```javascript
loadDictionary()        // Sözlüğü yükle
saveDictionary()        // Sözlüğü kaydet
getDictionary()         // Tüm sözlüğü al
getWord(word)          // Belirli bir kelimeyi al
addWord(wordData)      // Yeni kelime ekle
updateWord(word, data) // Kelimeyi güncelle
deleteWord(word)       // Kelimeyi sil
searchWords(query)     // Kelime ara
getWordCount()         // Toplam kelime sayısı
```

## 🎨 Özelleştirme

### Renkleri Değiştirme

`styles.css` dosyasındaki renk değişkenlerini düzenleyin:

```css
/* Ana renkler */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
border-color: #667eea;
```

### Yeni Kelime Kategorileri

Kelime kategorileri tamamen özelleştirilebilir. Örnek kategoriler:
- isim
- fiil
- sıfat
- zarf
- edat

## 📱 Responsive Tasarım

Uygulama, mobil cihazlarda da sorunsuz çalışacak şekilde tasarlanmıştır:
- Telefon (< 768px)
- Tablet
- Masaüstü

## 🔒 Güvenlik

- Tüm veriler yerel tarayıcıda saklanır
- Sunucu tarafı işlem yoktur
- Kişisel veri toplanmaz

## 🤝 Katkıda Bulunma

Projeye katkıda bulunmak için:
1. Fork yapın
2. Yeni bir branch oluşturun
3. Değişikliklerinizi commit edin
4. Pull request gönderin

## 📄 Lisans

Bu proje açık kaynak kodludur.

## 📞 İletişim

Sorularınız için issue açabilirsiniz.

---

**Not**: Bu uygulama eğitim amaçlı geliştirilmiştir ve yerel tarayıcı depolama kullanır. Profesyonel kullanım için bir backend veritabanı entegrasyonu önerilir.