import PySimpleGUI as sg
import sqlite3
import csv
import datetime
import os
import json
import requests
import nltk
from nltk.corpus import wordnet
import networkx as nx
import matplotlib.pyplot as plt
import re

nltk.download('wordnet', quiet=True)

DB_DOSYA = 'sozluk.db'
ESANLAMLI_BUTON_SAYISI = 15  # Aynı anda en çok gösterilecek eşanlamlı buton sayısı

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

def semantik_benzer_kelimeler(kelime, limit=15):
    synonyms = set()
    try:
        for syn in wordnet.synsets(kelime):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name().lower())
    except:
        pass
    db_benzer = benzer_kelimeler(kelime, limit)
    all_benzer = list(synonyms) + db_benzer
    return list(set(all_benzer))[:limit]

def esanlamli_zincir(kelime, derinlik=3, ziyaret_edilen=None):
    if ziyaret_edilen is None:
        ziyaret_edilen = set()
    if kelime in ziyaret_edilen or derinlik <= 0:
        return {}
    ziyaret_edilen.add(kelime)
    row = kelime_bul(kelime)
    if not row[0]:
        return {}
    # Yeni tablodan eşanlamlıları al
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute("SELECT esanlamli FROM esanlamlilar WHERE kelime=?", (kelime,))
    esan_list = [row[0] for row in c.fetchall()]
    conn.close()
    zincir = {kelime: {}}
    for esan in esan_list:
        if esan not in ziyaret_edilen:
            zincir[kelime][esan] = esanlamli_zincir(esan, derinlik-1, ziyaret_edilen.copy())
    return zincir

def zincir_to_treedata(zincir):
    treedata = sg.TreeData()
    def ekle(parent, data):
        for key, value in data.items():
            treedata.Insert(parent, key, key, values=[])
            if value:
                ekle(key, value)
    for root in zincir:
        treedata.Insert('', root, root, values=[])
        ekle(root, zincir[root])
    return treedata

def tum_kelimeler_listesi():
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    c.execute("SELECT kelime FROM sozluk ORDER BY kelime")
    kelimeler = [row[0] for row in c.fetchall()]
    conn.close()
    return kelimeler

def zincir_to_graph(zincir):
    G = nx.DiGraph()
    def ekle(node, sub):
        G.add_node(node)  # Ensure node is added
        for child in sub:
            G.add_edge(node, child)
            if sub[child]:
                ekle(child, sub[child])
            else:
                G.add_node(child)  # Ensure leaf nodes are added
    for root in zincir:
        ekle(root, zincir[root])
    return G

def tdk_veri_cek(kelime):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        # Fetch definition
        response = requests.get(f"https://sozluk.gov.tr/gts?ara={kelime}", headers=headers, timeout=10)
        aciklama = ""
        zitanlamlar_str = ""
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and data:
                    entry = data[0]
                    madde = entry.get("madde", kelime)
                    anlamlar = []
                    for anlam in entry.get("anlamlarListe", []):
                        anlam_text = anlam.get("anlam", "")
                        anlamlar.append(anlam_text)
                    aciklama = " | ".join(anlamlar[:3])  # Limit to first 3 meanings
                    # Extract antonyms from meanings
                    zitanlamlar_str = ''
                    for anlam_text in anlamlar:
                        match = re.search(r'Karşıt anlamı?:?\s*([^.]+)', anlam_text, re.IGNORECASE)
                        if match:
                            zitanlamlar_str = match.group(1).strip()
                            break
            except:
                print(f"JSON parse error for definition: {response.text[:200]}")
        # Fetch synonyms
        syn_response = requests.get(f"https://sozluk.gov.tr/esanlam?ara={kelime}", headers=headers, timeout=10)
        esanlamlar = []
        if syn_response.status_code == 200:
            try:
                syn_data = syn_response.json()
                if isinstance(syn_data, list):
                    for group in syn_data:
                        esanlam_str = group.get("esanlam", "")
                        esanlamlar.extend([word.strip() for word in esanlam_str.split('/') if word.strip() and not word.strip().endswith(')')])
            except:
                print(f"JSON parse error for synonyms: {syn_response.text[:200]}")
        esanlamlar_str = ",".join(set(esanlamlar))
        # Insert into sozluk
        conn = sqlite3.connect(DB_DOSYA)
        c = conn.cursor()
        # Check if exists
        c.execute("SELECT 1 FROM sozluk WHERE kelime=?", (kelime,))
        exists = c.fetchone()
        if exists:
            c.execute("UPDATE sozluk SET esanlamlar=?, aciklama=? WHERE kelime=?", (esanlamlar_str, aciklama, kelime))
        else:
            c.execute("INSERT INTO sozluk (kelime, esanlamlar, zitanlamlar, aciklama) VALUES (?, ?, ?, ?)", (kelime, esanlamlar_str, zitanlamlar_str, aciklama))
        conn.commit()
        # Insert into esanlamlilar
        for esan in set(esanlamlar):
            c.execute("INSERT OR IGNORE INTO esanlamlilar (kelime, esanlamli) VALUES (?, ?)", (kelime, esan))
            c.execute("INSERT OR IGNORE INTO esanlamlilar (kelime, esanlamli) VALUES (?, ?)", (esan, kelime))  # Bidirectional
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"TDK veri çekme hatası: {e}")
        return False

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

def kelime_ekle(kelime, esanlam, zitanlam, aciklama, ornek):
    cols = get_sozluk_columns()
    conn = sqlite3.connect(DB_DOSYA)
    c = conn.cursor()
    # Eşanlamlıları temizle: strip, boş olanları çıkar, virgülle birleştir
    esanlam = ','.join([k.strip() for k in esanlam.split(',') if k.strip()])
    zitanlam = ','.join([k.strip() for k in zitanlam.split(',') if k.strip()])
    veri = [kelime, esanlam, zitanlam, aciklama, ornek]
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
    # Eşanlamlıları yeni tabloya ekle
    esan_list = [k.strip() for k in esanlam.split(',') if k.strip()]
    c.execute("DELETE FROM esanlamlilar WHERE kelime=?", (kelime,))
    for esan in esan_list:
        c.execute("INSERT OR IGNORE INTO esanlamlilar (kelime, esanlamli) VALUES (?, ?)", (kelime, esan))
    conn.commit()
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
        ornek TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS esanlamlilar (
        id INTEGER PRIMARY KEY,
        kelime TEXT,
        esanlamli TEXT,
        UNIQUE(kelime, esanlamli)
    )
    ''')
    # İndeksler
    c.execute('CREATE INDEX IF NOT EXISTS idx_esanlamlilar_kelime ON esanlamlilar(kelime)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_esanlamlilar_esanlamli ON esanlamlilar(esanlamli)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_sozluk_kelime ON sozluk(kelime)')
    conn.commit()
    conn.close()

if not tablo_var_mi():
    tablo_olustur()

# Başlangıç verilerini ekle
conn = sqlite3.connect(DB_DOSYA)
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM sozluk")
if c.fetchone()[0] == 0:
    c.execute("INSERT OR IGNORE INTO sozluk (kelime, esanlamlar, zitanlamlar, aciklama, ornek) VALUES (?, ?, ?, ?, ?)", 
              ('özgür', 'serbest,hür,bağımsız', 'tutsak,esir', 'Özgür olmak, bağımsızlık.', 'Özgür bir ülkede yaşıyoruz.'))
    c.execute("INSERT OR IGNORE INTO sozluk (kelime, esanlamlar, zitanlamlar, aciklama, ornek) VALUES (?, ?, ?, ?, ?)", 
              ('serbest', 'özgür,hür,bağımsız', 'tutsak,esir', 'Serbest olmak, özgürlük.', 'Serbest bırakıldı.'))
    c.execute("INSERT OR IGNORE INTO sozluk (kelime, esanlamlar, zitanlamlar, aciklama, ornek) VALUES (?, ?, ?, ?, ?)", 
              ('hür', 'özgür,serbest,bağımsız', 'tutsak,esir', 'Hür olmak.', 'Hür bir insan.'))
    conn.commit()
conn.close()

# Tema ve font
sg.theme('DarkBlue3')
FONT = ("Segoe UI", 12)

cols = get_sozluk_columns()
merkez = 'özgür'
row = kelime_bul(merkez)
esanlamlar = row[cols.index('esanlamlar')] if 'esanlamlar' in cols else ''
esan_list = [k.strip() for k in esanlamlar.split(',')] if esanlamlar else []

kelime_list = tum_kelimeler_listesi()

# Layout
tab1_layout = [
    [sg.Text('Kelime:', font=FONT), sg.Combo(kelime_list, default_value=merkez, key='-KELIME-', font=FONT, size=(20,1), enable_events=True),
     sg.Button('Ara', font=FONT, bind_return_key=True),
     sg.Button('Semantik Ara', key='-SEMANTIK_ARA-', font=FONT), sg.Button('TDK\'den Ekle', key='-TDK_EKLE-', font=FONT),
     sg.Button('Geri', key='-GERI-', font=FONT), sg.Button('İleri', key='-ILERI-', font=FONT)],
    [sg.Text('Açıklama:', font=FONT), sg.Multiline('', key='-ACIKLAMA-', size=(60,3), font=FONT, disabled=True, right_click_menu=['&Right', ['Copy', 'Select All']], enable_events=True) if 'aciklama' in cols else sg.Text('')],
    [sg.Text('Örnek:', font=FONT), sg.Text(row[cols.index('ornek')], key='-ORNEK-', font=FONT, size=(60,1), right_click_menu=['&Right', ['Copy Örnek']]) if 'ornek' in cols else sg.Text('')],
    [sg.Text('Eşanlamlılar:', font=FONT)],
    [
        *[sg.Button(esan_list[i] if i < len(esan_list) else '', key=f'BTN_ES_{i}', visible=(i < len(esan_list)), font=FONT, size=(10,1)) for i in range(ESANLAMLI_BUTON_SAYISI)]
    ],
    [sg.Button('Zincir Göster', key='-ZINCIR_GOSTER-', font=FONT)],
    [sg.Button('Zincir Kaydet (JSON)', key='-ZINCIR_KAYDET-', font=FONT)],
]

tab2_layout = [
    [sg.Text('Favoriler:', font=FONT), sg.Listbox([], key='-FAVORILER-', size=(40,15), font=FONT, enable_events=True)],
    [sg.Button('Favoriye Ekle', key='-FAV_EKLE-', font=FONT), sg.Button('Favoriden Sil', key='-FAV_SIL-', font=FONT)],
]

tab3_layout = [
    [sg.Text('Kelime:', font=FONT), sg.Input('', key='-Y_KELIME-', size=(15,1), font=FONT),
     sg.Text('Eşanlam:', font=FONT), sg.Input('', key='-Y_ESANLAM-', size=(15,1), font=FONT),
     sg.Text('Zıt:', font=FONT), sg.Input('', key='-Y_ZIT-', size=(15,1), font=FONT)],
    [sg.Text('Açıklama:', font=FONT), sg.Multiline('', key='-Y_ACIKLAMA-', size=(50,3), font=FONT),
     sg.Text('Örnek:', font=FONT), sg.Input('', key='-Y_ORNEK-', size=(20,1), font=FONT)],
    [sg.Button('Ekle/Güncelle', font=FONT), sg.Button('temizle', font=FONT)],
    [sg.Text('Silinecek Kelime:', font=FONT), sg.Input('', key='-SIL-', size=(15,1), font=FONT), sg.Button('Sil', font=FONT)],
    [sg.Button('Tüm Kelimeler', key='-LISTE-', font=FONT),
     sg.Button('Dışa Aktar (CSV)', key='-DISARI-', font=FONT),
     sg.Button('Toplu İçe Aktar (TDK)', key='-ICERI-', font=FONT),
     sg.Button('Yedekle', key='-YEDEK-', font=FONT)],
]

layout = [
    [sg.TabGroup([
        [sg.Tab('Ana Arama', tab1_layout)],
        [sg.Tab('Favoriler', tab2_layout)],
        [sg.Tab('Yönetim', tab3_layout)],
    ])],
    [sg.Column([
        [sg.Text('Zıt anlamlılar:', font=FONT), sg.Text(row[cols.index('zitanlamlar')], key='-ZITANLAM-', font=FONT, right_click_menu=['&Right', ['Copy Zıt']]) if 'zitanlamlar' in cols else sg.Text('')],
    ], vertical_alignment='top'),
     sg.Column([
        [sg.Tree(sg.TreeData(), key='-ZINCIR-', headings=[], auto_size_columns=True, num_rows=15, col0_width=30, font=FONT),
         sg.Image(key='-GRAFIK-', size=(400,300))]
     ], vertical_alignment='top')]
]

window = sg.Window('MTU Zincirli Sözlük (Modern Sürüm)', layout, finalize=True, font=FONT, resizable=True)

gecmis = [merkez]
current_index = 0
favoriler = []

def panel_guncelle(kelime):
    """Verilen kelime için arayüzü günceller."""
    cols = get_sozluk_columns()
    row = kelime_bul(kelime)
    window['-KELIME-'].update(kelime)
    if 'aciklama' in cols: window['-ACIKLAMA-'].update(value=row[cols.index('aciklama')])
    if 'ornek' in cols: window['-ORNEK-'].update(row[cols.index('ornek')])
    if 'zitanlamlar' in cols: window['-ZITANLAM-'].update(row[cols.index('zitanlamlar')])
    if 'esanlamlar' in cols:
        esanlamlar = row[cols.index('esanlamlar')]
        esan_list = [k.strip() for k in esanlamlar.split(',')] if esanlamlar else []
        for i in range(ESANLAMLI_BUTON_SAYISI):
            if i < len(esan_list):
                window[f'BTN_ES_{i}'].update(text=esan_list[i], visible=True)
            else:
                window[f'BTN_ES_{i}'].update(visible=False)

# ----- YENİ: Temizle fonksiyonu -----
def inputlari_temizle():
    window['-Y_KELIME-'].update('')
    window['-Y_ESANLAM-'].update('')
    window['-Y_ZIT-'].update('')
    window['-Y_ACIKLAMA-'].update('')
    window['-Y_ORNEK-'].update('')

while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    if event == 'Copy':
        try:
            selected = window['-ACIKLAMA-'].Widget.selection_get()
            sg.clipboard_set(selected)
        except:
            sg.clipboard_set(values['-ACIKLAMA-'])
    if event == 'Select All':
        window['-ACIKLAMA-'].Widget.tag_add('sel', '1.0', 'end')
        window['-ACIKLAMA-'].Widget.focus_set()
    if event == 'Copy Zıt':
        sg.clipboard_set(values['-ZITANLAM-'])
    if event == 'Copy Örnek':
        sg.clipboard_set(values['-ORNEK-'])
    if event == 'Ara':
        kelime = values['-KELIME-'].strip()
        if kelime:
            if kelime_bul(kelime)[0]:
                panel_guncelle(kelime)
                gecmis.append(kelime)
                current_index = len(gecmis) - 1
            else:
                # Otomatik TDK'den çek
                sg.popup("Kelime bulunamadı, TDK'den çekiliyor...", title="Bilgi")
                if tdk_veri_cek(kelime):
                    sg.popup("Veri TDK'den eklendi.", title="Başarılı")
                    panel_guncelle(kelime)
                    gecmis.append(kelime)
                    current_index = len(gecmis) - 1
                else:
                    sg.popup("Veri çekilemedi. Benzer kelimeler aranıyor.", title="Uyarı")
                    benzer = benzer_kelimeler(kelime)
                    if benzer:
                        secili = benzer_kelime_sec(benzer)
                        if secili:
                            panel_guncelle(secili)
                            window['-KELIME-'].update(secili)
                            gecmis.append(secili)
                            current_index = len(gecmis) - 1
                    else:
                        sg.popup("Benzer kelime de bulunamadı.", title="Sonuç")
    if event == '-SEMANTIK_ARA-':
        kelime = values['-KELIME-'].strip()
        if kelime:
            benzer = semantik_benzer_kelimeler(kelime)
            if benzer:
                secili = benzer_kelime_sec(benzer)
                if secili:
                    panel_guncelle(secili)
                    window['-KELIME-'].update(secili)
                    gecmis.append(secili)
                    current_index = len(gecmis) - 1
            else:
                sg.popup("Semantik benzer kelime yok!", title="Arama Sonucu")
    if event == '-TDK_EKLE-':
        kelime = values['-KELIME-'].strip()
        if kelime:
            if tdk_veri_cek(kelime):
                sg.popup("Veri TDK'den eklendi.", title="Başarılı")
                panel_guncelle(kelime)
            else:
                sg.popup("Veri çekilemedi. İnternet bağlantınızı kontrol edin.", title="Hata")
    if event == '-GERI-':
        if current_index > 0:
            current_index -= 1
            panel_guncelle(gecmis[current_index])
            window['-KELIME-'].update(gecmis[current_index])
    if event == '-ILERI-':
        if current_index < len(gecmis) - 1:
            current_index += 1
            panel_guncelle(gecmis[current_index])
            window['-KELIME-'].update(gecmis[current_index])
    # Eşanlamlı butonlara tıklama:
    for i in range(ESANLAMLI_BUTON_SAYISI):
        if event == f'BTN_ES_{i}':
            btn_kelime = window[f'BTN_ES_{i}'].get_text()
            if btn_kelime:
                panel_guncelle(btn_kelime)
    if event == '-ZINCIR_GOSTER-':
        kelime = values['-KELIME-'].strip()
        if kelime:
            zincir = esanlamli_zincir(kelime)
            if zincir:
                treedata = zincir_to_treedata(zincir)
                window['-ZINCIR-'].update(values=treedata)
                window.refresh()
                # Grafik
                try:
                    G = zincir_to_graph(zincir)
                    plt.figure(figsize=(4,3))
                    nx.draw(G, with_labels=True, node_color='lightblue', font_size=10, arrowsize=20)
                    image_path = os.path.join(os.getcwd(), 'zincir.png')
                    plt.savefig(image_path)
                    plt.close()
                    window['-GRAFIK-'].update(filename=image_path)
                    window.refresh()
                except Exception as e:
                    sg.popup(f"Grafik oluşturma hatası: {str(e)}", title="Hata")
            else:
                sg.popup("Zincir bulunamadı. Kelime eşanlamlılarına sahip olmayabilir.", title="Uyarı")
        else:
            sg.popup("Lütfen bir kelime girin.", title="Uyarı")
    if event == '-ZINCIR_KAYDET-':
        kelime = values['-KELIME-'].strip()
        if kelime:
            zincir = esanlamli_zincir(kelime)
            if zincir:
                dosya = sg.popup_get_file('JSON dosyasını kaydet:', save_as=True, file_types=(("JSON Dosyası", "*.json"),))
                if dosya:
                    with open(dosya, 'w', encoding='utf-8') as f:
                        json.dump(zincir, f, ensure_ascii=False, indent=4)
                    sg.popup(f"Zincir kaydedildi: {dosya}")
            else:
                sg.popup("Zincir bulunamadı.")
    if event == '-FAV_EKLE-':
        kelime = values['-KELIME-'].strip()
        if kelime and kelime not in favoriler:
            favoriler.append(kelime)
            window['-FAVORILER-'].update(favoriler)
    if event == '-FAV_SIL-':
        secili = values['-FAVORILER-']
        if secili:
            favoriler.remove(secili[0])
            window['-FAVORILER-'].update(favoriler)
    if event == '-FAVORILER-':
        secili = values['-FAVORILER-']
        if secili:
            panel_guncelle(secili[0])
            gecmis.append(secili[0])
            current_index = len(gecmis) - 1
            window['-KELIME-'].update(secili[0])
    if event == 'Ekle/Güncelle':
        sonuc = kelime_ekle(
            values['-Y_KELIME-'].strip(),
            values['-Y_ESANLAM-'].strip(),
            values['-Y_ZIT-'].strip(),
            values['-Y_ACIKLAMA-'].strip(),
            values['-Y_ORNEK-'].strip()
        )
        sg.popup(sonuc)
        tabloyu_guncelle()
        panel_guncelle(values['-Y_KELIME-'].strip())
        inputlari_temizle()   # Otomatik temizle!
    if event == 'temizle':
        inputlari_temizle()
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
