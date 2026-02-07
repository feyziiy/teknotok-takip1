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
    print("XML Çekiliyor...")
    response = requests.get(XML_URL, timeout=30)
    response.encoding = 'utf-8'
    parser = etree.XMLParser(recover=True, encoding='utf-8')
    root = etree.fromstring(response.content, parser=parser)
    
    new_data = {}
    
    # --- XML ANALİZ VE VERİ ÇEKME ---
    # XML içindeki tüm elemanları derinlemesine tara
    all_elements = root.xpath("//*")
    
    # Ürün olabilecek her şeyi bulmaya çalış
    for el in all_elements:
        # Bir elementin ürünü temsil etmesi için en az 3 alt dalı olmalı (sku, title, stock gibi)
        if len(el) >= 3:
            sku, title, stock = None, None, 0
            
            for child in el:
                tag = child.tag.lower()
                text = (child.text or "").strip()
                
                # SKU/ID Bulma
                if any(x in tag for x in ['sku', 'id', 'kod', 'model']):
                    sku = text
                # Başlık Bulma
                if any(x in tag for x in ['title', 'name', 'ad', 'baslik']):
                    title = text
                # Stok Bulma
                if any(x in tag for x in ['stock', 'qty', 'stok', 'adet']):
                    s_digits = "".join(filter(str.isdigit, text))
                    stock = int(s_digits) if s_digits else 0

            if sku and title:
                new_data[sku] = {"Stock": stock, "Title": title}

    # --- HAFIZA İŞLEMLERİ ---
    if os.path.exists(HAFIZA_FILE) and os.path.getsize(HAFIZA_FILE) > 0:
        with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    else:
        old_data = {}

    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)

    # --- RAPOR
