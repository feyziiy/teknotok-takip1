import requests
from lxml import etree
import json
import os

# --- AYARLARIN ---
BOT_TOKEN = "8591872798:AAH-WNlXVF01knmB6q_iRpQkpHp4oyZvo1w"
CHAT_ID = "7798613067"
XML_URL = "https://teknotok.com/wp-content/uploads/teknotok-feeds/teknotokxml.xml"
HAFIZA_FILE = "urun_takip_hafiza.json"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    r = requests.post(url, json=payload, timeout=10)
    print(f"Telegram Yanıtı: {r.status_code}") # Actions ekranında görmek için

def start_tracking():
    print("İşlem başlıyor...")
    response = requests.get(XML_URL, timeout=30)
    root = etree.fromstring(response.content)
    
    # Hafızayı oku
    if os.path.exists(HAFIZA_FILE):
        with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
            try:
                old_data = json.load(f)
            except:
                old_data = {}
    else:
        old_data = {}

    new_data = {}
    updates = []

    # XML tarama
    for post in root.xpath('.//post'):
        try:
            sku = post.find('Sku').text.strip()
            title = post.find('Title').text.strip()
            price = post.find('Price').text.strip()
            stock = int(''.join(filter(str.isdigit, post.find('Stock').text)))
            new_data[sku] = {"Price": price, "Stock": stock, "Title": title}
        except:
            continue

    # ZORUNLU TETİKLEME: Eğer hafıza boşsa veya ilk kez doluyorsa mesaj at
    if not old_data:
        send_telegram("✅ *Sistem Başlatıldı!*\nHafıza ilk kez oluşturuldu, artık takibe hazırım.")
    
    # Değişiklik kontrolü
    for sku, info in new_data.items():
        if sku in old_data:
            if old_data[sku]['Stock'] != info['Stock']:
                updates.append(f"📦 *STOK DEĞİŞTİ*\n{info['Title']}\nYeni Stok: {info['Stock']}")

    # Dosyayı kaydet
    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    
    # Güncellemeleri gönder
    for msg in updates[:5]:
        send_telegram(msg)

if __name__ == "__main__":
    start_tracking()
