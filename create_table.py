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
c.execute('DROP TABLE IF EXISTS esanlamlilar')
c.execute('''
CREATE TABLE esanlamlilar (
    kelime TEXT,
    esanlamli TEXT,
    UNIQUE(kelime, esanlamli)
)
''')
c.execute('CREATE INDEX IF NOT EXISTS idx_esanlamlilar_kelime ON esanlamlilar(kelime)')
c.execute('CREATE INDEX IF NOT EXISTS idx_esanlamlilar_esanlamli ON esanlamlilar(esanlamli)')
conn.commit()
conn.close()
print("Tablolar başarıyla oluşturuldu!")
