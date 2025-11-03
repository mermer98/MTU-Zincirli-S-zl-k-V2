import sqlite3

DB_DOSYA = 'sozluk.db'

conn = sqlite3.connect(DB_DOSYA)
c = conn.cursor()

# Sadece "aciklama" sütunu dolu olan kayıtlar üzerinde işlem yap
c.execute("SELECT kelime, aciklama FROM sozluk WHERE aciklama IS NOT NULL AND aciklama != ''")
for kelime, aciklama in c.fetchall():
    # Eşanlamlılar'a aktar, açıklamayı boş bırak
    c.execute("UPDATE sozluk SET esanlamlar=?, aciklama='' WHERE kelime=?", (aciklama, kelime))

conn.commit()
conn.close()

print("Tüm eşanlamlar doğru sütuna taşındı, aciklama sütunu boşaltıldı.")
