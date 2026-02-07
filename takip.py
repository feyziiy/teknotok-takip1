import requests
from lxml import etree
import json
import os

# AYARLAR
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
    response = requests.get(XML_URL, timeout=30)
    response.encoding = 'utf-8'
    parser = etree.XMLParser(recover=True, encoding='utf-8')
    root = etree.fromstring(response.content, parser=parser)
    
    if os.path.exists(HAFIZA_FILE) and os.path.getsize(HAFIZA_FILE) > 0:
        with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    else:
        old_data = {}

    new_data = {}
    updates = []

    for post in root.xpath('.//post'):
        try:
            sku = post.find('Sku').text.strip()
            title = post.find('Title').text.strip()
            price = post.find('Price').text.strip()
            stock_text = post.find('Stock').text if post.find('Stock') is not None else "0"
            stock = int(''.join(filter(str.isdigit, stock_text)))
            
            new_data[sku] = {"Price": price, "Stock": stock, "Title": title}

            if old_data:
                if sku not in old_data:
                    updates.append(f"🆕 *YENİ ÜRÜN*\n{title}\nStok: {stock}")
                else:
                    old = old_data[sku]
                    if stock == 0 and old['Stock'] > 0:
                        updates.append(f"🚫 *STOK BİTTİ*\n{title}")
                    elif stock < old['Stock']:
                        updates.append(f"📉 *STOK AZALDI (-{old['Stock']-stock})*\n{title}\nKalan: {stock}")
                    elif stock > old['Stock']:
                        updates.append(f"📈 *STOK ARTTI*\n{title}\nYeni Stok: {stock}")
        except:
            continue

    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    
    if updates:
        for msg in updates[:10]:
            send_telegram(msg)

if __name__ == "__main__":
    start_tracking()
