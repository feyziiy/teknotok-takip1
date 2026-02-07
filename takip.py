import requests
from lxml import etree
import json
import os

BOT_TOKEN = "8591872798:AAH-WNlXVF01knmB6q_iRpQkpHp4oyZvo1w"
CHAT_ID = "7798613067"
XML_URL = "https://teknotok.com/wp-content/uploads/teknotok-feeds/teknotokxml.xml"
HAFIZA_FILE = "urun_takip_hafiza.json"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def start_tracking():
    try:
        response = requests.get(XML_URL, timeout=30)
        response.encoding = 'utf-8'
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(response.content, parser=parser)
        
        # XML içindeki tüm ürün benzeri yapıları tara
        items = root.xpath('//*[local-name()="post" or local-name()="item" or local-name()="product"]')
        if not items:
            items = root.xpath('//*[sku or Sku or ID]')

        new_data = {}
        for item in items:
            sku = item.findtext('.//Sku') or item.findtext('.//sku') or item.findtext('.//ID')
            title = item.findtext('.//Title') or item.findtext('.//title') or item.findtext('.//Name')
            stock_val = item.findtext('.//Stock') or item.findtext('.//stock') or "0"
            
            if sku and title:
                stock = int(''.join(filter(str.isdigit, str(stock_val)))) if any(c.isdigit() for c in str(stock_val)) else 0
                new_data[sku.strip()] = {"Stock": stock, "Title": title.strip()}

        if os.path.exists(HAFIZA_FILE) and os.path.getsize(HAFIZA_FILE) > 0:
            with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        else:
            old_data = {}

        updates = []
        if old_data:
            for sku, info in new_data.items():
                if sku in old_data:
                    if info['Stock'] < old_data[sku]['Stock']:
                        updates.append(f"📉 *STOK AZALDI*\n{info['Title']}\nKalan: {info['Stock']}")
                else:
                    updates.append(f"🆕 *YENİ ÜRÜN*\n{info['Title']}")

        with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)

        if not old_data and new_data:
            send_telegram(f"✅ *Sistem Hazır!* {len(new_data)} ürün takibe alındı.")
        
        for msg in updates[:10]:
            send_telegram(msg)
            
    except Exception as e:
        send_telegram(f"🚨 Hata oluştu: {str(e)}")

if __name__ == "__main__":
    start_tracking()
