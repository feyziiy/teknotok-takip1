import requests
from lxml import etree
import json
import os
import sys

# AYARLARIN
BOT_TOKEN = "8591872798:AAH-WNlXVF01knmB6q_iRpQkpHp4oyZvo1w"
CHAT_ID = "7798613067"
XML_URL = "https://teknotok.com/wp-content/uploads/teknotok-feeds/teknotokxml.xml"
HAFIZA_FILE = "urun_takip_hafiza.json"

def send_telegram(message):
    print(f"Mesaj Gonderiliyor: {message}")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=15)
        print(f"Telegram Yaniti: {r.status_code}")
    except Exception as e:
        print(f"Baglanti Hatasi: {e}")

def start_tracking():
    # TEST MESAJI (Bunu goruyorsan kod calisiyor demektir)
    send_telegram("🔄 *Kontrol Başladı:* Veriler taranıyor...")

    try:
        response = requests.get(XML_URL, timeout=30)
        response.encoding = 'utf-8'
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(response.content, parser=parser)
        
        # XML'i kazıyalım
        items = root.xpath('//*[local-name()="post" or local-name()="item" or local-name()="product"]')
        if not items:
            items = root.xpath('//*[sku or Sku or ID]')

        new_data = {}
        for item in items:
            sku = item.findtext('.//Sku') or item.findtext('.//sku') or item.findtext('.//ID')
            title = item.findtext('.//Title') or item.findtext('.//title') or item.findtext('.//Name')
            stock_val = item.findtext('.//Stock') or item.findtext('.//stock') or "0"
            
            if sku and title:
                s_str = "".join(filter(str.isdigit, str(stock_val)))
                stock = int(s_str) if s_str else 0
                new_data[sku.strip()] = {"Stock": stock, "Title": title.strip()}

        # Hafıza yazımı
        with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)
        
        send_telegram(f"✅ *Tarama Tamamlandı:* {len(new_data)} ürün hafızaya alındı.")

    except Exception as e:
        send_telegram(f"🚨 *Hata Yakalandı:* {str(e)}")

if __name__ == "__main__":
    start_tracking()
