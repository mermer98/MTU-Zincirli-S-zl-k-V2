import sqlite3

conn = sqlite3.connect('sozluk.db')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS sozluk')
c.execute('''
CREATE TABLE sozluk (
    kelime TEXT PRIMARY KEY,
    esanlamlar TEXT,
    zitanlamlar TEXT,
    aciklama TEXT,
    ornek TEXT
)
''')
conn.commit()
conn.close()
print("Tablo başarıyla oluşturuldu!")
