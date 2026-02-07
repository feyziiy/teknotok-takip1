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
    requests.post(url, json=payload, timeout=10)

def start_tracking():
    # TEST MESAJI: Bunu görünce botun yaşadığını anlayacağız
    send_telegram("🚀 *Kontrol Başladı!* XML taranıyor...")

    response = requests.get(XML_URL, timeout=30)
    response.encoding = 'utf-8'
    parser = etree.XMLParser(recover=True, encoding='utf-8')
    root = etree.fromstring(response.content, parser=parser)
    
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

    for post in root.xpath('.//post'):
        try:
            sku = post.find('Sku').text.strip()
            title = post.find('Title').text.strip()
            price = post.find('Price').text.strip()
            stock_text = post.find('Stock').text
            stock = int(''.join(filter(str.isdigit, stock_text))) if stock_text else 0
            new_data[sku] = {"Price": price, "Stock": stock, "Title": title}

            if old_data and sku in old_data:
                old = old_data[sku]
                if old['Price'] != price:
                    updates.append(f"💰 *FİYAT DEĞİŞTİ*\n{title}\n📉 {old['Price']} -> 📈 {price}")
                
                # Stok Değişimi
                curr_stock = int(stock)
                prev_stock = int(old['Stock'])
                if curr_stock < prev_stock:
                    updates.append(f"📉 *STOK AZALDI*\n{title}\nKalan: {curr_stock}")
                elif curr_stock > prev_stock:
                    updates.append(f"📈 *STOK ARTTI*\n{title}\nYeni: {curr_stock}")
        except:
            continue

    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    
    if updates:
        for msg in updates[:5]:
            send_telegram(msg)
