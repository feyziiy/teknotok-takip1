import requests
import xml.etree.ElementTree as ET
import json
import os

# Ayarlar
BOT_TOKEN = "8591872798:AAH-WNlXVF01knmB6q_iRpQkpHp4oyZvo1w"
CHAT_ID = "7798613067"
XML_URL = "https://teknotok.com/wp-content/uploads/teknotok-feeds/teknotokxml.xml"
HAFIZA_FILE = "urun_takip_hafiza.json"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def start_tracking():
    # XML Çek
    response = requests.get(XML_URL)
    response.encoding = 'utf-8'
    root = ET.fromstring(response.text)
    
    # Hafızayı Yükle
    if os.path.exists(HAFIZA_FILE):
        with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    else:
        old_data = {}

    new_data = {}
    updates = []

    # XML içinde dön
    for post in root.findall('.//post'):
        sku = post.find('Sku').text.strip()
        title = post.find('Title').text.strip()
        price = post.find('Price').text.strip()
        stock = int(''.join(filter(str.isdigit, post.find('Stock').text)))

        new_data[sku] = {"Price": price, "Stock": stock, "Title": title}

        if old_data and sku in old_data:
            old = old_data[sku]
            if old['Stock'] > 0 and stock <= 0:
                updates.append(f"❌ *STOK BİTTİ*\n{title}")
            elif old['Price'] != price:
                updates.append(f"💰 *FİYAT DEĞİŞTİ*\n{title}\n📉 Eski: {old['Price']}\n📈 Yeni: {price}")
            elif old['Stock'] <= 0 and stock > 0:
                updates.append(f"✅ *STOK GELDİ*\n{title}\nFiyat: {price}")
        elif old_data:
            updates.append(f"🆕 *YENİ ÜRÜN*\n{title}\nFiyat: {price}")

    # Hafızayı Kaydet
    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)

    # Bildirimleri Gönder
    for msg in updates:
        send_telegram(msg)

if __name__ == "__main__":
    start_tracking()
