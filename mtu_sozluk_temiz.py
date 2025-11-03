import PySimpleGUI as sg
import sqlite3
import csv
import html
import os

DB_DOSYA = 'sozluk.db'

# Tabloyu otomatik oluştur
def tablo_kontrol_ve_olustur():
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sozluk (
            kelime TEXT PRIMARY KEY,
            esanlamlar TEXT,
            zitanlamlar TEXT,
            aciklama TEXT,
            ornek TEXT
        )
    ''')
    conn.commit()
    conn.close()

tablo_kontrol_ve_olustur()

def kelime_bul(kelime):
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute('SELECT * FROM sozluk WHERE kelime = ?', (kelime,))
    row = c.fetchone()
    conn.close()
    return row

def kelime_ekle(kelime, esanlam, zitanlam, aciklama, ornek):
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO sozluk (kelime, esanlamlar, zitanlamlar, aciklama, ornek) VALUES (?, ?, ?, ?, ?)',
                  (kelime, esanlam, zitanlam, aciklama, ornek))
        conn.commit()
        sonuc = "Eklendi."
    except sqlite3.IntegrityError:
        c.execute('UPDATE sozluk SET esanlamlar=?, zitanlamlar=?, aciklama=?, ornek=? WHERE kelime=?',
                  (esanlam, zitanlam, aciklama, ornek, kelime))
        conn.commit()
        sonuc = "Güncellendi."
    conn.close()
    return sonuc

def kelime_sil(kelime):
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute('DELETE FROM sozluk WHERE kelime = ?', (kelime,))
    conn.commit()
    sayi = c.rowcount
    conn.close()
    return sayi

def zincirli_butonlar(esanlamlar):
    if not esanlamlar:
        return [sg.Text("Eşanlamlı yok.")]
    return [sg.Button(k.strip(), key=f'BTN_{k.strip()}') for k in esanlamlar.split(',') if k.strip()]

def tum_kelimeler_tablosu():
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute('SELECT kelime, esanlamlar, zitanlamlar, aciklama, ornek FROM sozluk ORDER BY kelime')
    veriler = c.fetchall()
    conn.close()
    basliklar = ["Kelime", "Eşanlamlılar", "Zıt Anlamlılar", "Açıklama", "Örnek"]
    layout = [
        [sg.Text('Kelime ara:'), sg.Input(key='-ARA-', size=(20,1)), sg.Button('Filtrele')],
        [sg.Table(values=veriler, headings=basliklar, key='-TABLO-', enable_events=True, auto_size_columns=True, num_rows=14, col_widths=[20,20,20,40,20], justification='left')],
        [sg.Button('Kapat')]
    ]
    pencere = sg.Window('Tüm Kelimeler', layout, modal=True, finalize=True, resizable=True, size=(900,350))
    while True:
        e, v = pencere.read()
        if e in (sg.WIN_CLOSED, 'Kapat'):
            break
        if e == 'Filtrele':
            aranan = v['-ARA-'].strip().lower()
            if aranan:
                filtreli = [row for row in veriler if aranan in row[0].lower()]
            else:
                filtreli = veriler
            pencere['-TABLO-'].update(filtreli)
        if e == '-TABLO-':
            secilenler = v['-TABLO-']
            if secilenler:
                secili_kelime = pencere['-TABLO-'].get()[secilenler[0]][0]
                pencere.close()
                return secili_kelime
    pencere.close()
    return None

def disari_aktar_csv(dosya_adi='sozluk_arsiv.csv'):
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute('SELECT kelime, esanlamlar, zitanlamlar, aciklama, ornek FROM sozluk ORDER BY kelime')
    veriler = c.fetchall()
    conn.close()
    basliklar = ["Kelime", "Eşanlamlılar", "Zıt Anlamlılar", "Açıklama", "Örnek"]
    with open(dosya_adi, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(basliklar)
        writer.writerows(veriler)
    return dosya_adi

# --- TDK CSV Toplu İçe Aktarım Fonksiyonu ---
def iceri_aktar_csv(dosya_adi='tdk-20210524.csv'):
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    eklenen, guncellenen = 0, 0
    with open(dosya_adi, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        # başlık satırını atla (ör: #name,TDK Güncel Türkçe Sözlük)
        next(reader)
        for row in reader:
            if not row or not row[0].strip():
                continue
            kelime = row[0].strip()
            aciklama = row[1].strip() if len(row) > 1 else ''
            # KARAKTER DÜZELTME (özellikle bozuk gelenler için)
            aciklama = html.unescape(aciklama)
            try:
                aciklama = aciklama.encode("latin1").decode("utf-8")
            except:
                pass
            esanlam = ''
            zitanlam = ''
            ornek = ''
            try:
                c.execute('INSERT INTO sozluk (kelime, esanlamlar, zitanlamlar, aciklama, ornek) VALUES (?, ?, ?, ?, ?)',
                          (kelime, esanlam, zitanlam, aciklama, ornek))
                eklenen += 1
            except sqlite3.IntegrityError:
                c.execute('UPDATE sozluk SET esanlamlar=?, zitanlamlar=?, aciklama=?, ornek=? WHERE kelime=?',
                          (esanlam, zitanlam, aciklama, ornek, kelime))
                guncellenen += 1
    conn.commit()
    conn.close()
    return eklenen, guncellenen

sg.theme('DarkBlue3')

merkez = 'özgür'
row = kelime_bul(merkez)
layout = [
    [sg.Text('Kelime:'), sg.Input(merkez, key='-KELIME-', enable_events=True), 
     sg.Button('Ara', bind_return_key=True), 
     sg.Button('Tüm Kelimeler', key='-LISTE-'), 
     sg.Button('Dışa Aktar (CSV)', key='-DISARI-'), 
     sg.Button('Toplu İçe Aktar (TDK)', key='-ICERI-')],
    [sg.Text('Açıklama:')],
    [sg.Multiline(row[4] if row and len(row) > 4 else '', key='-ACIKLAMA-', size=(90, 3), disabled=True, autoscroll=True)],
    [sg.Text('Örnek:'), sg.Text(row[5] if row and len(row) > 5 else '', key='-ORNEK-', size=(90,1))],
    [sg.Text('Eşanlamlılar:')],
    [sg.Column([zincirli_butonlar(row[2] if row and len(row) > 2 else '')], key='-ESANLAM_PANEL-')],
    [sg.Text('Zıt anlamlılar:'), sg.Text(row[3] if row and len(row) > 3 else '', key='-ZITANLAM-', size=(90,1))],
    [sg.HorizontalSeparator()],
    [sg.Text('Kelime:'), sg.Input('', key='-Y_KELIME-', size=(10,1)),
     sg.Text('Eşanlam:'), sg.Input('', key='-Y_ESANLAM-', size=(10,1)),
     sg.Text('Zıt:'), sg.Input('', key='-Y_ZIT-', size=(10,1)),
     sg.Text('Açıklama:'), sg.Input('', key='-Y_ACIKLAMA-', size=(15,1)),
     sg.Text('Örnek:'), sg.Input('', key='-Y_ORNEK-', size=(15,1)),
     sg.Button('Ekle/Güncelle')],
    [sg.Text('Silinecek Kelime:'), sg.Input('', key='-SIL-', size=(10,1)), sg.Button('Sil')]
]

window = sg.Window(
    'MTU Zincirli Sözlük (Tablo Destekli)', 
    layout, 
    finalize=True, 
    resizable=False, 
    size=(1100, 400)
)

def panel_guncelle(kelime):
    row = kelime_bul(kelime)
    window['-KELIME-'].update(kelime)
    window['-ACIKLAMA-'].update(row[4] if row and len(row) > 4 else '')
    window['-ORNEK-'].update(row[5] if row and len(row) > 5 else '')
    window['-ZITANLAM-'].update(row[3] if row and len(row) > 3 else '')
    window['-ESANLAM_PANEL-'].update([zincirli_butonlar(row[2] if row and len(row) > 2 else '')])

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    # ENTER ile arama için bind_return_key kullanıldı, ayrıca aşağıdaki satır da alternatif
    if event == 'Ara' or (event == '-KELIME-' and values['-KELIME-']):
        kelime = values['-KELIME-'].strip()
        panel_guncelle(kelime)
    if event.startswith('BTN_'):
        kelime = event[4:]
        panel_guncelle(kelime)
    if event == 'Ekle/Güncelle':
        sonuc = kelime_ekle(
            values['-Y_KELIME-'].strip(),
            values['-Y_ESANLAM-'].strip(),
            values['-Y_ZIT-'].strip(),
            values['-Y_ACIKLAMA-'].strip(),
            values['-Y_ORNEK-'].strip()
        )
        sg.popup(sonuc)
    if event == 'Sil':
        k = values['-SIL-'].strip()
        s = kelime_sil(k)
        sg.popup(f"{k} silindi." if s else "Kelime bulunamadı.")
    if event == '-LISTE-':
        secili = tum_kelimeler_tablosu()
        if secili:
            panel_guncelle(secili)
    if event == '-DISARI-':
        dosya = disari_aktar_csv()
        sg.popup(f"Sözlük başarıyla dışa aktarıldı:\n{dosya}")
    if event == '-ICERI-':
        dosya = sg.popup_get_file('CSV dosyası seç', file_types=(('CSV Dosyası', '*.csv'),), default_extension='csv')
        if dosya:
            eklenen, guncellenen = iceri_aktar_csv(dosya)
            sg.popup(f'Toplu içe aktarma tamamlandı.\nEklenen yeni kelime: {eklenen}\nGüncellenen kelime: {guncellenen}')

window.close()
