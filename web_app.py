"""
MTU Zincirli Sözlük - Web Uygulaması
Flask tabanlı web arayüzü
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_cors import CORS
import sqlite3
import json
import os
import requests

app = Flask(__name__)

# CORS ayarları - Belirli domain'lere izin ver
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5000",
            "http://127.0.0.1:5000",
            "https://enduluskuran.odoo.com",
            "*"  # Production'da bunu kaldırın ve sadece gerekli domain'leri ekleyin
        ],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Veritabanı dosyası
DB_DOSYA = 'sozluk.db'

# =============== YARDIMCI FONKSİYONLAR ===============

def get_db_connection():
    """Veritabanı bağlantısı oluşturur"""
    conn = sqlite3.connect(DB_DOSYA)
    conn.row_factory = sqlite3.Row
    return conn

def get_sozluk_columns():
    """Sözlük tablosunun sütun isimlerini döndürür"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("PRAGMA table_info(sozluk)")
    cols = [row[1] for row in c.fetchall()]
    conn.close()
    return cols

def kelime_bul(kelime):
    """Veritabanından kelimeyi bulur"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sozluk WHERE kelime = ?", (kelime,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def benzer_kelimeler(kelime, limit=15):
    """Benzer kelimeleri bulur"""
    conn = get_db_connection()
    c = conn.cursor()
    q = f'{kelime[:3]}%' if kelime and len(kelime) >= 3 else f'{kelime}%' if kelime else '%'
    c.execute("SELECT kelime FROM sozluk WHERE kelime LIKE ? ORDER BY kelime LIMIT ?", (q, limit+1))
    rows = [r[0] for r in c.fetchall() if r[0] != kelime]
    conn.close()
    return rows

def gelismis_arama(sorgu, limit=50):
    """Gelişmiş arama fonksiyonu"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT * FROM sozluk 
        WHERE kelime LIKE ? OR esanlamlar LIKE ? OR aciklama LIKE ? OR zitanlamlar LIKE ?
        ORDER BY 
            CASE WHEN kelime = ? THEN 0
                 WHEN kelime LIKE ? THEN 1
                 ELSE 2
            END,
            kelime
        LIMIT ?
    """, (f"%{sorgu}%", f"%{sorgu}%", f"%{sorgu}%", f"%{sorgu}%", sorgu, f"{sorgu}%", limit))
    
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results

def esanlamli_zincir(kelime, derinlik=5, ziyaret_edilen=None):
    """Eşanlamlı kelimeler zincirini oluşturur"""
    if ziyaret_edilen is None:
        ziyaret_edilen = set()
    if kelime in ziyaret_edilen or derinlik == 0:
        return {}
    ziyaret_edilen.add(kelime)
    
    zincir = {kelime: []}
    row = kelime_bul(kelime)
    
    if row and row.get('esanlamlar'):
        esanlamlar = row['esanlamlar']
        esan_list = [k.strip() for k in esanlamlar.split(',') if k.strip()]
        
        for esan in esan_list:
            if esan not in ziyaret_edilen:
                alt_zincir = esanlamli_zincir(esan, derinlik-1, ziyaret_edilen)
                if alt_zincir:
                    zincir[kelime].append(esan)
                    zincir.update(alt_zincir)
    
    return zincir

def tum_zincir_yollari(zincir):
    """Tüm zincir yollarını çıkarır"""
    if not zincir:
        return []
    
    def yollar_bul(node, path):
        if not zincir.get(node, []):
            return [path]
        yollar = []
        for child in zincir[node]:
            yollar.extend(yollar_bul(child, path + [child]))
        return yollar
    
    return yollar_bul(list(zincir.keys())[0], [list(zincir.keys())[0]])

def istatistikler_al():
    """Sözlük istatistiklerini toplar"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Toplam kelime sayısı
    c.execute("SELECT COUNT(*) FROM sozluk")
    toplam_kelime = c.fetchone()[0]
    
    # Eşanlamlı ilişki sayısı
    c.execute("SELECT COUNT(*) FROM esanlamlilar")
    toplam_esanlam = c.fetchone()[0]
    
    # En çok eşanlamlı olan kelimeler (top 10)
    c.execute("""
        SELECT kelime, COUNT(*) as esanlam_sayisi 
        FROM esanlamlilar 
        GROUP BY kelime 
        ORDER BY esanlam_sayisi DESC 
        LIMIT 10
    """)
    en_cok_esanlam = [{"kelime": row[0], "sayi": row[1]} for row in c.fetchall()]
    
    conn.close()
    
    return {
        'toplam_kelime': toplam_kelime,
        'toplam_esanlam': toplam_esanlam,
        'en_cok_esanlam': en_cok_esanlam
    }

def tdk_veri_cek(kelime):
    """TDK'den kelime verisi çeker"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Tanım çek
        response = requests.get(
            f"https://sozluk.gov.tr/gts?ara={kelime}", 
            headers=headers, 
            timeout=10
        )
        
        aciklama = ""
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and data:
                    entry = data[0]
                    anlamlar = []
                    anlamlar_liste = entry.get("anlamlarListe", [])
                    for anlam in anlamlar_liste:
                        anlam_text = anlam.get("anlam", "")
                        anlamlar.append(anlam_text)
                    aciklama = " | ".join(anlamlar[:3])
            except:
                pass
        
        # Eşanlamlıları çek
        syn_response = requests.get(
            f"https://sozluk.gov.tr/esanlam?ara={kelime}", 
            headers=headers, 
            timeout=10
        )
        
        esanlamlar = []
        if syn_response.status_code == 200:
            try:
                syn_data = syn_response.json()
                if isinstance(syn_data, list):
                    for group in syn_data:
                        esanlam_str = group.get("esanlam", "")
                        esanlamlar.extend([
                            word.strip() for word in esanlam_str.split('/') 
                            if word.strip() and not word.strip().endswith(')')
                        ])
            except:
                pass
        
        return {
            'aciklama': aciklama,
            'esanlamlar': list(set(esanlamlar))
        }
        
    except Exception as e:
        return {'aciklama': '', 'esanlamlar': [], 'error': str(e)}

# =============== WEB SAYFALARI ===============

@app.route('/')
def ana_sayfa():
    """Ana sayfa"""
    stats = istatistikler_al()
    return render_template('index.html', stats=stats)

@app.route('/ara')
def arama_sayfasi():
    """Arama sayfası"""
    sorgu = request.args.get('q', '').strip()
    sonuclar = []
    
    if sorgu:
        sonuclar = gelismis_arama(sorgu)
    
    return render_template('arama.html', sorgu=sorgu, sonuclar=sonuclar)

@app.route('/kelime/<kelime>')
def kelime_detay(kelime):
    """Kelime detay sayfası"""
    veri = kelime_bul(kelime)
    benzerler = benzer_kelimeler(kelime, 10) if veri else []
    
    # Eşanlamlı listesi
    esanlamlar = []
    if veri and veri.get('esanlamlar'):
        esanlamlar = [k.strip() for k in veri['esanlamlar'].split(',') if k.strip()]
    
    # Zıt anlamlı listesi
    zitanlamlar = []
    if veri and veri.get('zitanlamlar'):
        zitanlamlar = [k.strip() for k in veri['zitanlamlar'].split(',') if k.strip()]
    
    return render_template('kelime.html', 
                         kelime=kelime, 
                         veri=veri, 
                         benzerler=benzerler,
                         esanlamlar=esanlamlar,
                         zitanlamlar=zitanlamlar)

@app.route('/zincir/<kelime>')
def zincir_sayfasi(kelime):
    """Zincir görselleştirme sayfası"""
    derinlik = request.args.get('derinlik', 3, type=int)
    zincir = esanlamli_zincir(kelime, derinlik=derinlik)
    yollar = tum_zincir_yollari(zincir)
    
    return render_template('zincir.html', 
                         kelime=kelime, 
                         zincir=zincir, 
                         yollar=yollar,
                         derinlik=derinlik)

@app.route('/istatistikler')
def istatistikler_sayfasi():
    """İstatistikler sayfası"""
    stats = istatistikler_al()
    return render_template('istatistikler.html', stats=stats)

@app.route('/tum-kelimeler')
def tum_kelimeler():
    """Tüm kelimeler sayfası (sayfalama ile)"""
    sayfa = request.args.get('sayfa', 1, type=int)
    limit = 50
    offset = (sayfa - 1) * limit
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Toplam kelime sayısı
    c.execute("SELECT COUNT(*) FROM sozluk")
    toplam = c.fetchone()[0]
    
    # Kelimeler
    c.execute("SELECT kelime FROM sozluk ORDER BY kelime LIMIT ? OFFSET ?", (limit, offset))
    kelimeler = [row[0] for row in c.fetchall()]
    conn.close()
    
    toplam_sayfa = (toplam + limit - 1) // limit
    
    return render_template('tum_kelimeler.html', 
                         kelimeler=kelimeler, 
                         sayfa=sayfa,
                         toplam_sayfa=toplam_sayfa,
                         toplam=toplam)

# =============== API ENDPOINT'LERİ ===============

@app.route('/api/ara')
def api_ara():
    """Arama API'si"""
    sorgu = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    
    if not sorgu:
        return jsonify({'error': 'Sorgu parametresi gerekli', 'sonuclar': []})
    
    sonuclar = gelismis_arama(sorgu, limit)
    return jsonify({'sorgu': sorgu, 'sonuclar': sonuclar, 'toplam': len(sonuclar)})

@app.route('/api/kelime/<kelime>')
def api_kelime(kelime):
    """Kelime detay API'si"""
    veri = kelime_bul(kelime)
    
    if not veri:
        return jsonify({'error': 'Kelime bulunamadı', 'kelime': kelime})
    
    # Eşanlamlı listesi
    esanlamlar = []
    if veri.get('esanlamlar'):
        esanlamlar = [k.strip() for k in veri['esanlamlar'].split(',') if k.strip()]
    
    # Zıt anlamlı listesi
    zitanlamlar = []
    if veri.get('zitanlamlar'):
        zitanlamlar = [k.strip() for k in veri['zitanlamlar'].split(',') if k.strip()]
    
    return jsonify({
        'kelime': kelime,
        'aciklama': veri.get('aciklama', ''),
        'ornek': veri.get('ornek', ''),
        'esanlamlar': esanlamlar,
        'zitanlamlar': zitanlamlar
    })

@app.route('/api/benzer/<kelime>')
def api_benzer(kelime):
    """Benzer kelimeler API'si"""
    limit = request.args.get('limit', 15, type=int)
    benzerler = benzer_kelimeler(kelime, limit)
    return jsonify({'kelime': kelime, 'benzerler': benzerler})

@app.route('/api/zincir/<kelime>')
def api_zincir(kelime):
    """Zincir API'si"""
    derinlik = request.args.get('derinlik', 3, type=int)
    zincir = esanlamli_zincir(kelime, derinlik=derinlik)
    yollar = tum_zincir_yollari(zincir)
    
    return jsonify({
        'kelime': kelime,
        'derinlik': derinlik,
        'zincir': zincir,
        'yollar': yollar
    })

@app.route('/api/istatistikler')
def api_istatistikler():
    """İstatistikler API'si"""
    stats = istatistikler_al()
    return jsonify(stats)

@app.route('/api/tdk/<kelime>')
def api_tdk(kelime):
    """TDK'den veri çekme API'si"""
    veri = tdk_veri_cek(kelime)
    return jsonify({'kelime': kelime, **veri})

@app.route('/api/kelime-ekle', methods=['POST'])
def api_kelime_ekle():
    """Kelime ekleme/güncelleme API'si"""
    try:
        data = request.get_json()
        
        kelime = data.get('kelime', '').strip()
        if not kelime:
            return jsonify({'error': 'Kelime alanı zorunludur'}), 400
        
        esanlamlar = data.get('esanlamlar', '')
        zitanlamlar = data.get('zitanlamlar', '')
        aciklama = data.get('aciklama', '')
        ornek = data.get('ornek', '')
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # INSERT OR REPLACE kullan
        c.execute('''
            INSERT OR REPLACE INTO sozluk (kelime, esanlamlar, zitanlamlar, aciklama, ornek) 
            VALUES (?, ?, ?, ?, ?)
        ''', (kelime, esanlamlar, zitanlamlar, aciklama, ornek))
        
        # Eşanlamlıları esanlamlilar tablosuna ekle
        if esanlamlar:
            for esan in esanlamlar.split(','):
                esan = esan.strip()
                if esan:
                    c.execute("INSERT OR IGNORE INTO esanlamlilar (kelime, esanlamli) VALUES (?, ?)", 
                            (kelime, esan))
                    c.execute("INSERT OR IGNORE INTO esanlamlilar (kelime, esanlamli) VALUES (?, ?)", 
                            (esan, kelime))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'"{kelime}" başarıyla kaydedildi'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kelime-sil/<kelime>', methods=['DELETE'])
def api_kelime_sil(kelime):
    """Kelime silme API'si"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('DELETE FROM sozluk WHERE kelime = ?', (kelime,))
        c.execute('DELETE FROM esanlamlilar WHERE kelime = ? OR esanlamli = ?', (kelime, kelime))
        
        conn.commit()
        silinen = c.rowcount
        conn.close()
        
        if silinen > 0:
            return jsonify({'success': True, 'message': f'"{kelime}" silindi'})
        else:
            return jsonify({'error': 'Kelime bulunamadı'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rastgele-kelime')
def api_rastgele_kelime():
    """Rastgele kelime API'si"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sozluk ORDER BY RANDOM() LIMIT 1")
    row = c.fetchone()
    conn.close()
    
    if row:
        return jsonify(dict(row))
    return jsonify({'error': 'Sözlük boş'})

# =============== HATA SAYFALARI ===============

@app.errorhandler(404)
def sayfa_bulunamadi(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def sunucu_hatasi(e):
    return render_template('500.html'), 500

# =============== UYGULAMA BAŞLATMA ===============

if __name__ == '__main__':
    # Templates ve static klasörlerini kontrol et
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    print("=" * 50)
    print("MTU Zincirli Sözlük - Web Uygulaması")
    print("=" * 50)
    print(f"Veritabanı: {DB_DOSYA}")
    print("Sunucu başlatılıyor...")
    print("Tarayıcıda açın: http://localhost:5000")
    print("=" * 50)
    
    # Railway için port ayarı
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
