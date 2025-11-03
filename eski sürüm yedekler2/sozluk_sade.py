import PySimpleGUI as sg
import sqlite3
import csv
import datetime
import os

DB_DOSYA = 'sozluk.db'
ESANLAMLI_BUTON_SAYISI = 10  # Aynı anda en çok gösterilecek eşanlamlı buton sayısı

def get_sozluk_columns():
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute("PRAGMA table_info(sozluk)")
    cols = [row[1] for row in c.fetchall()]
    conn.close()
    return cols

def kelime_bul(kelime):
    cols = get_sozluk_columns()
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute("SELECT * FROM sozluk WHERE kelime = ?", (kelime,))
    row = c.fetchone()
    conn.close()
    if not row:
        return tuple(['']*len(cols))
    return row

def benzer_kelimeler(kelime, limit=15):
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    q = f'{kelime[:3]}%' if kelime else '%'
    c.execute("SELECT kelime FROM sozluk WHERE kelime LIKE ? ORDER BY kelime LIMIT ?", (q, limit+1))
    rows = [r[0] for r in c.fetchall() if r[0] != kelime]
    conn.close()
    return rows

def benzer_kelime_sec(benzerler):
    if not benzerler:
        sg.popup("Benzer kelime yok.", title="Sonuç")
        return None
    layout = [
        [sg.Text('Benzer kelimeler:', font=("Segoe UI", 11))],
        [sg.Listbox(benzerler, size=(30, 8), key='-BENZERLIST-', enable_events=True)],
        [sg.Button('Seç'), sg.Button('İptal')]
    ]
    pencere = sg.Window('Benzer Kelimeler', layout, modal=True, finalize=True, return_keyboard_events=True)
    while True:
        e, v = pencere.read()
        if e in (sg.WIN_CLOSED, 'İptal', 'Escape:27'):
            pencere.close()
            return None
        if e == '-BENZERLIST-' or e == 'Seç':
            sec = v['-BENZERLIST-']
            if sec:
                pencere.close()
                return sec[0]
    pencere.close()
    return None

def kelime_ekle(kelime, esanlam, zitanlam, aciklama, ornek, etiket='', notlar=''):
    cols = get_sozluk_columns()
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    veri = [kelime, esanlam, zitanlam, aciklama, ornek]
    if 'etiket' in cols:
        veri.append(etiket)
    if 'notlar' in cols:
        veri.append(notlar)
    try:
        c.execute(f'INSERT INTO sozluk ({",".join(cols)}) VALUES ({",".join(["?"]*len(cols))})', veri)
        conn.commit()
        sonuc = "Eklendi."
    except sqlite3.IntegrityError:
        update_cols = [f"{col}=?" for col in cols if col != "kelime"]
        update_vals = veri[1:] + [kelime]
        c.execute(f'UPDATE sozluk SET {",".join(update_cols)} WHERE kelime=?', update_vals)
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

def tum_kelimeler_tablosu():
    cols = get_sozluk_columns()
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute(f'SELECT {",".join(cols)} FROM sozluk ORDER BY kelime')
    veriler = c.fetchall()
    conn.close()
    toplam = len(veriler)
    basliklar = [col.capitalize() for col in cols]
    layout = [
        [sg.Text(f"Toplam kelime: {toplam}", font=("Segoe UI", 11), text_color="yellow")],
        [sg.Text('Filtre:'), sg.Input(key='-ARA-', size=(20,1)), sg.Button('Filtrele')],
        [sg.Table(values=veriler, headings=basliklar, key='-TABLO-', enable_events=True, auto_size_columns=False, col_widths=[15]*len(cols), num_rows=16)],
        [sg.Button('Kapat')]
    ]
    pencere = sg.Window('Tüm Kelimeler', layout, modal=True, finalize=True, resizable=True)
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

def disari_aktar_csv(dosya_adi=None):
    cols = get_sozluk_columns()
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute(f'SELECT {",".join(cols)} FROM sozluk ORDER BY kelime')
    veriler = c.fetchall()
    conn.close()
    basliklar = [col.capitalize() for col in cols]
    if dosya_adi is None:
        tarih = datetime.datetime.now().strftime('%Y%m%d_%H%M')
        dosya_adi = f"sozluk_yedek_{tarih}.csv"
    with open(dosya_adi, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(basliklar)
        writer.writerows(veriler)
    return dosya_adi

def tdk_csv_ozel_aktar(dosya_adi):
    cols = get_sozluk_columns()
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    eklenen, guncellenen = 0, 0
    with open(dosya_adi, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            kelime = row[0].strip()
            aciklama = row[1].strip() if len(row) > 1 else ''
            try:
                c.execute(f'INSERT INTO sozluk (kelime, aciklama) VALUES (?, ?)', (kelime, aciklama))
                eklenen += 1
            except sqlite3.IntegrityError:
                c.execute(f'UPDATE sozluk SET aciklama=? WHERE kelime=?', (aciklama, kelime))
                guncellenen += 1
    conn.commit()
    conn.close()
    return eklenen, guncellenen

def tabloyu_guncelle():
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute('VACUUM')
    conn.commit()
    conn.close()

def tablo_var_mi():
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sozluk'")
    var = c.fetchone()
    conn.close()
    return bool(var)

def tablo_olustur():
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS sozluk (
        kelime TEXT PRIMARY KEY,
        esanlamlar TEXT,
        zitanlamlar TEXT,
        aciklama TEXT,
        ornek TEXT,
        etiket TEXT,
        notlar TEXT
    )
    ''')
    conn.commit()
    conn.close()

if not tablo_var_mi():
    tablo_olustur()

# Tema ve font
sg.theme('DarkGrey12')
FONT = ("Segoe UI", 12)

cols = get_sozluk_columns()
merkez = 'özgür'
row = kelime_bul(merkez)
esanlamlar = row[cols.index('esanlamlar')] if 'esanlamlar' in cols else ''
esan_list = [k.strip() for k in esanlamlar.split(',')] if esanlamlar else []

# Layout
layout = [
    [sg.Text('Kelime:', font=FONT), sg.Input(merkez, key='-KELIME-', font=FONT),
     sg.Button('Ara', font=FONT, bind_return_key=True),
     sg.Button('Tüm Kelimeler', key='-LISTE-', font=FONT),
     sg.Button('Dışa Aktar (CSV)', key='-DISARI-', font=FONT),
     sg.Button('Toplu İçe Aktar (TDK)', key='-ICERI-', font=FONT),
     sg.Button('Yedekle', key='-YEDEK-', font=FONT)],
    [sg.Text('Açıklama:', font=FONT), sg.Text(row[cols.index('aciklama')], key='-ACIKLAMA-', font=FONT, size=(60,1)) if 'aciklama' in cols else sg.Text('')],
    [sg.Text('Örnek:', font=FONT), sg.Text(row[cols.index('ornek')], key='-ORNEK-', font=FONT, size=(60,1)) if 'ornek' in cols else sg.Text('')],
    [sg.Text('Etiket:', font=FONT), sg.Text(row[cols.index('etiket')], key='-ETIKET-', font=FONT, size=(20,1)) if 'etiket' in cols else sg.Text(''),
     sg.Text('Not:', font=FONT), sg.Text(row[cols.index('notlar')], key='-NOTLAR-', font=FONT, size=(30,1)) if 'notlar' in cols else sg.Text('')],
    [sg.Text('Eşanlamlılar:', font=FONT)],
    [
        *[sg.Button(esan_list[i] if i < len(esan_list) else '', key=f'BTN_ES_{i}', visible=(i < len(esan_list)), font=FONT, size=(10,1)) for i in range(ESANLAMLI_BUTON_SAYISI)]
    ],
    [sg.Text('Zıt anlamlılar:', font=FONT), sg.Text(row[cols.index('zitanlamlar')], key='-ZITANLAM-', font=FONT) if 'zitanlamlar' in cols else sg.Text('')],
    [sg.HorizontalSeparator()],
    [sg.Text('Kelime:', font=FONT), sg.Input('', key='-Y_KELIME-', size=(10,1), font=FONT),
     sg.Text('Eşanlam:', font=FONT), sg.Input('', key='-Y_ESANLAM-', size=(10,1), font=FONT),
     sg.Text('Zıt:', font=FONT), sg.Input('', key='-Y_ZIT-', size=(10,1), font=FONT),
     sg.Text('Etiket:', font=FONT) if 'etiket' in cols else sg.Text(''), sg.Input('', key='-Y_ETIKET-', size=(10,1), font=FONT) if 'etiket' in cols else sg.Text('')],
    [sg.Text('Açıklama:', font=FONT), sg.Input('', key='-Y_ACIKLAMA-', size=(15,1), font=FONT),
     sg.Text('Örnek:', font=FONT), sg.Input('', key='-Y_ORNEK-', size=(15,1), font=FONT),
     sg.Text('Not:', font=FONT) if 'notlar' in cols else sg.Text(''), sg.Input('', key='-Y_NOTLAR-', size=(15,1), font=FONT) if 'notlar' in cols else sg.Text(''),
     sg.Button('Ekle/Güncelle', font=FONT)],
    [sg.Text('Silinecek Kelime:', font=FONT), sg.Input('', key='-SIL-', size=(10,1), font=FONT), sg.Button('Sil', font=FONT)]
]

window = sg.Window('MTU Zincirli Sözlük (Modern Sürüm)', layout, finalize=True, font=FONT, resizable=True)

def panel_guncelle(kelime):
    cols = get_sozluk_columns()
    row = kelime_bul(kelime)
    window['-KELIME-'].update(kelime)
    if 'aciklama' in cols: window['-ACIKLAMA-'].update(row[cols.index('aciklama')])
    if 'ornek' in cols: window['-ORNEK-'].update(row[cols.index('ornek')])
    if 'zitanlamlar' in cols: window['-ZITANLAM-'].update(row[cols.index('zitanlamlar')])
    if 'etiket' in cols: window['-ETIKET-'].update(row[cols.index('etiket')])
    if 'notlar' in cols: window['-NOTLAR-'].update(row[cols.index('notlar')])
    if 'esanlamlar' in cols:
        esanlamlar = row[cols.index('esanlamlar')]
        esan_list = [k.strip() for k in esanlamlar.split(',')] if esanlamlar else []
        for i in range(ESANLAMLI_BUTON_SAYISI):
            if i < len(esan_list):
                window[f'BTN_ES_{i}'].update(text=esan_list[i], visible=True)
            else:
                window[f'BTN_ES_{i}'].update(visible=False)

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == 'Ara':
        kelime = values['-KELIME-'].strip()
        if kelime_bul(kelime)[0]:
            panel_guncelle(kelime)
        else:
            benzer = benzer_kelimeler(kelime)
            if benzer:
                secili = benzer_kelime_sec(benzer)
                if secili:
                    panel_guncelle(secili)
                    window['-KELIME-'].update(secili)
            else:
                sg.popup("Kayıt yok!", title="Arama Sonucu")
    # Eşanlamlı butonlara tıklama:
    for i in range(ESANLAMLI_BUTON_SAYISI):
        if event == f'BTN_ES_{i}':
            btn_kelime = window[f'BTN_ES_{i}'].get_text()
            if btn_kelime:
                panel_guncelle(btn_kelime)
    if event == 'Ekle/Güncelle':
        etiket = values['-Y_ETIKET-'].strip() if '-Y_ETIKET-' in values else ''
        notlar = values['-Y_NOTLAR-'].strip() if '-Y_NOTLAR-' in values else ''
        sonuc = kelime_ekle(
            values['-Y_KELIME-'].strip(),
            values['-Y_ESANLAM-'].strip(),
            values['-Y_ZIT-'].strip(),
            values['-Y_ACIKLAMA-'].strip(),
            values['-Y_ORNEK-'].strip(),
            etiket,
            notlar
        )
        sg.popup(sonuc)
        tabloyu_guncelle()
    if event == 'Sil':
        k = values['-SIL-'].strip()
        s = kelime_sil(k)
        sg.popup(f"{k} silindi." if s else "Kelime bulunamadı.")
        tabloyu_guncelle()
    if event == '-LISTE-':
        secili = tum_kelimeler_tablosu()
        if secili:
            panel_guncelle(secili)
    if event == '-DISARI-':
        dosya = disari_aktar_csv()
        sg.popup(f"Sözlük başarıyla dışa aktarıldı:\n{dosya}")
    if event == '-ICERI-':
        dosya_yolu = sg.popup_get_file('CSV dosyasını seç:', file_types=(("CSV Dosyası", "*.csv"),))
        if dosya_yolu:
            eklenen, guncellenen = tdk_csv_ozel_aktar(dosya_yolu)
            sg.popup(f"Toplu içe aktarma tamamlandı.\nEklenen yeni kelime: {eklenen}\nGüncellenen kelime: {guncellenen}")
            tabloyu_guncelle()
    if event == '-YEDEK-':
        dosya = disari_aktar_csv()
        sg.popup(f"Otomatik yedek alındı:\n{os.path.abspath(dosya)}")

window.close()
