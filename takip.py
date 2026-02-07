import requests
from lxml import etree
import json
import os

# AYARLARIN
BOT_TOKEN = "8591872798:AAH-WNlXVF01knmB6q_iRpQkpHp4oyZvo1w"
CHAT_ID = "7798613067"
XML_URL = "https://teknotok.com/wp-content/uploads/teknotok-feeds/teknotokxml.xml"
HAFIZA_FILE = "urun_takip_hafiza.json"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    r = requests.post(url, json=payload)
    print(f"Telegram Gönderim Durumu: {r.status_code}")

def start_tracking():
    print("--- İŞLEM BAŞLADI ---")
    try:
        response = requests.get(XML_URL, timeout=30)
        root = etree.fromstring(response.content)
        print(f"XML başarıyla çekildi. Ürün sayısı: {len(root.xpath('.//post'))}")
    except Exception as e:
        print(f"HATA: XML çekilemedi: {e}")
        return

    # Hafızayı oku
    if os.path.exists(HAFIZA_FILE):
        with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    else:
        old_data = {}

    new_data = {}
    found_target = False

    for post in root.xpath('.//post'):
        sku = post.find('Sku').text.strip() if post.find('Sku') is not None else "Yok"
        title = post.find('Title').text.strip() if post.find('Title') is not None else "Başlıksız"
        price = post.find('Price').text.strip() if post.find('Price') is not None else "0"
        stock = post.find('Stock').text.strip() if post.find('Stock') is not None else "0"
        
        new_data[sku] = {"Price": price, "Stock": stock, "Title": title}

        # TEST ÜRÜNÜ KONTROLÜ
        if sku == "311732":
            found_target = True
            print(f"Hedef Ürün Bulundu! Stok: {stock}")

    # DEĞİŞİKLİK VAR MI?
    if old_data != new_data:
        print("Değişiklik tespit edildi, mesaj gönderiliyor...")
        send_telegram("🔔 *SİSTEM AKTİF*\nDeğişiklikler tarandı ve hafıza güncellendi.")
    else:
        print("Hafıza ile XML aynı. Hiçbir değişiklik yok.")

    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    start_tracking()
