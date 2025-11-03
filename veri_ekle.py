import sqlite3

conn = sqlite3.connect('sozluk.db')
c = conn.cursor()

c.execute("INSERT OR REPLACE INTO sozluk (kelime, esanlamlar, zitanlamlar, aciklama, ornek) VALUES (?, ?, ?, ?, ?)", 
          ('özgür', 'serbest,hür,bağımsız', 'tutsak,esir', 'Özgür olmak, bağımsızlık.', 'Özgür bir ülkede yaşıyoruz.'))
c.execute("INSERT OR REPLACE INTO sozluk (kelime, esanlamlar, zitanlamlar, aciklama, ornek) VALUES (?, ?, ?, ?, ?)", 
          ('serbest', 'özgür,hür,bağımsız', 'tutsak,esir', 'Serbest olmak, özgürlük.', 'Serbest bırakıldı.'))
c.execute("INSERT OR REPLACE INTO sozluk (kelime, esanlamlar, zitanlamlar, aciklama, ornek) VALUES (?, ?, ?, ?, ?)", 
          ('hür', 'özgür,serbest,bağımsız', 'tutsak,esir', 'Hür olmak.', 'Hür bir insan.'))

conn.commit()
conn.close()
print('Veri eklendi.')