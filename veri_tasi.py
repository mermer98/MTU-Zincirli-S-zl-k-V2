import sqlite3

conn = sqlite3.connect('sozluk.db')
c = conn.cursor()

# Mevcut verileri yeni tabloya taşı
c.execute("SELECT kelime, esanlamlar FROM sozluk WHERE esanlamlar IS NOT NULL AND esanlamlar != ''")
for kelime, esanlamlar in c.fetchall():
    esan_list = [k.strip() for k in esanlamlar.split(',') if k.strip()]
    for esan in esan_list:
        c.execute("INSERT OR IGNORE INTO esanlamlilar (kelime, esanlamli) VALUES (?, ?)", (kelime, esan))

conn.commit()
conn.close()
print('Veriler yeni tabloya taşındı.')