import requests
import json
import os
import re

# --- AYARLARIN ---
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
    print("Teknotok XML Derin Tarama Başlatıldı...")
    try:
        response = requests.get(XML_URL, timeout=30)
        response.encoding = 'utf-8'
        content = response.text

        # XML yapısına takılmadan <post> ... </post> bloklarını cımbızla çekiyoruz
        posts = re.findall(r'<post>(.*?)</post>', content, re.DOTALL)
        
        new_data = {}
        
        for post_content in posts:
            # Her blok içinden verileri özel Regex ile ayıklıyoruz
            sku_match = re.search(r'<Sku>(.*?)</Sku>', post_content)
            title_match = re.search(r'<Title>(.*?)</Title>', post_content)
            stock_match = re.search(r'<Stock>(.*?)</Stock>', post_content)
            price_match = re.search(r'<Price>(.*?)</Price>', post_content)

            if sku_match and title_match:
                sku = sku_match.group(1).strip()
                title = title_match.group(1).strip()
                stock_val = stock_match.group(1).strip() if stock_match else "0"
                price = price_match.group(1).strip() if price_match else "0"

                s_digits = "".join(filter(str.isdigit, stock_val))
                new_data[sku] = {
                    "Stock": int(s_digits) if s_digits else 0,
                    "Title": title,
                    "Price": price
                }

        # Hafıza Yönetimi
        if os.path.exists(HAFIZA_FILE) and os.path.getsize(HAFIZA_FILE) > 0:
            with open(HAFIZA_FILE, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
        else:
            old_data = {}

        updates = []
        if old_data:
            for sku, info in new_data.items():
                if sku in old_data:
                    old_stock = old_data[sku]['Stock']
                    new_stock = info['Stock']
                    
                    if new_stock != old_stock:
                        emoji = "📈" if new_stock > old_stock else "📉"
                        durum = "STOK ARTTI" if new_stock > old_stock else "STOK AZALDI"
                        
                        msg = (f"{emoji} *{durum}*\n\n"
                               f"*Ürün:* {info['Title']}\n"
                               f"*SKU:* `{sku}`\n"
                               f"*Eski Stok:* {old_stock}\n"
                               f"*Yeni Stok:* {new_stock}\n"
                               f"*Fiyat:* {info['Price']} TL")
                        updates.append(msg)
                else:
                    msg = (f"🆕 *YENİ ÜRÜN*\n\n"
                           f"*Ürün:* {info['Title']}\n"
                           f"*SKU:* `{sku}`\n"
                           f"*Stok:* {info['Stock']}\n"
                           f"*Fiyat:* {info['Price']} TL")
                    updates.append(msg)

        with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)

        if not old_data and len(new_data) > 0:
            send_telegram(f"✅ *Sistem
