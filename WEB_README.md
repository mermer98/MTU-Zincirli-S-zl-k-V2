# MTU Zincirli Sözlük - Web Uygulaması

🔗 **Türkçe kelimelerin eş anlamları ve zıt anlamları arasında zincir kuran web sözlüğü**

## 🚀 Hızlı Başlangıç

```bash
# Repo klonla
git clone https://github.com/mermer98/MTU-Zincirli-S-zl-k-V2.git
cd MTU-Zincirli-S-zl-k-V2

# Gereklilikleri yükle
pip install -r requirements.txt

# Sunucuyu başlat
python web_app.py
```

Tarayıcıda **http://localhost:5000** açın!

## 📁 Dosya Yapısı

- `web_app.py` - Ana Flask sunucusu
- `sozluk.db` - SQLite veritabanı (100+ Türkçe kelime)
- `templates/` - HTML şablonları
- `static/` - CSS ve JavaScript dosyaları
- `requirements.txt` - Python gereklilikleri

## 🔌 API Endpoints

- `GET /api/ara?q={kelime}` - Kelime arama
- `GET /api/kelime/{kelime}` - Kelime detayı
- `GET /api/zincir/{kelime}` - Eş anlam zinciri
- `GET /api/istatistikler` - Sözlük istatistikleri

## 🌐 Web Sitesine Gömme

### İFrame ile:
```html
<iframe src="http://localhost:5000" 
        style="width: 100%; height: 600px; border: none;">
</iframe>
```

### Widget olarak:
```html
<!-- Kompakt arama kutusu -->
<div id="sozluk-widget">
  <!-- JavaScript ile dinamik içerik -->
</div>
```

## 💡 Özellikler

- ✅ Kelime arama ve filtreleme
- ✅ Eş anlam/zıt anlam zincirleri
- ✅ D3.js ile interaktif grafik
- ✅ Responsive tasarım
- ✅ REST API
- ✅ CORS desteği

## 🛠 Teknolojiler

- **Backend:** Python Flask
- **Database:** SQLite3
- **Frontend:** HTML5, CSS3, JavaScript
- **Visualization:** D3.js
- **UI Framework:** Bootstrap benzeri custom CSS

## 📞 Destek

GitHub Issues kullanarak sorularınızı sorabilirsiniz.

---
**Geliştirici:** GitHub Copilot ile geliştirildi  
**Lisans:** MIT