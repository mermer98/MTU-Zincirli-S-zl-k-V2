import csv

kaynak = 'eski_veri.csv'
hedef = 'sozluk_programi_icin.csv'

def temizle(val):
    if val is None:
        return ''
    return val.strip()

with open(kaynak, 'r', encoding='utf-8') as f_in, open(hedef, 'w', encoding='utf-8', newline='') as f_out:
    reader = csv.DictReader(f_in)
    # Başlıkları boşluksuz hale getir
    if reader.fieldnames:
        reader.fieldnames = [field.strip() for field in reader.fieldnames]
    writer = csv.writer(f_out)
    writer.writerow(['Kelime', 'Eşanlamlılar', 'Zıt Anlamlılar', 'Açıklama', 'Örnek'])
    for row in reader:
        if not row:  # Boş satırları atla
            continue
        kelime = temizle(row.get('kelime'))
        esanlamlar = [
            temizle(row.get('esanlam')),
            temizle(row.get('esanlam2')),
            temizle(row.get('esanlam3')),
            temizle(row.get('esanlam4'))
        ]
        esanlamlar = ','.join([e for e in esanlamlar if e])
        zitanlam = temizle(row.get('zitanlam'))
        aciklama = temizle(row.get('aciklama'))
        ornek = temizle(row.get('ornek'))
        writer.writerow([kelime, esanlamlar, zitanlam, aciklama, ornek])
