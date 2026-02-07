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
    print("Teknotok XML taranıyor...")
    try:
        response = requests.get(XML_URL, timeout=30)
        response.encoding = 'utf-8'
        content = response.text

        # XML yapısına takılmadan <post> bloklarını ayıkla
        posts = re.findall(r'<post>(.*?)</post>', content, re.DOTALL)
        
        new_data = {}
        for p in posts:
            sku_m = re.search(r'<Sku>(.*?)</Sku>', p)
            title_m = re.search(r'<Title>(.*?)</Title>', p)
            stock_m = re.search(r'<Stock>(.*?)</Stock>', p)
            price_m = re.search(r'<Price>(.*?)</Price>', p)

            if sku_m and title_m:
                sku = sku_m.group(1).strip()
                title = title_m.group(1).strip()
                stock_val = stock_m.group(1).strip() if stock_m else "0"
                price = price_m.group(1).strip() if price_m else "0"

                s_digits = "".join(filter(str.isdigit, str(stock_val)))
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
                    if info['Stock'] != old_data[sku]['Stock']:
                        emoji = "📈" if info['Stock'] > old_data[sku]['Stock'] else "📉"
                        durum = "STOK ARTTI" if info['Stock'] > old_data[sku]['Stock'] else "STOK AZALDI"
                        msg = (f"{emoji} *{durum}*\n\n"
                               f"*Ürün:* {info['Title']}\n"
                               f"*SKU:* `{sku}`\n"
                               f"*Eski Stok:* {old_data[sku]['Stock']}\n"
                               f"*Yeni Stok:* {info['Stock']}\n"
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
            basari_mesaji = f"✅ *BAŞARDIK!*\n\n{len(new_data)} ürün başarıyla hafızaya alındı. Sistem takibe başladı."
            send_telegram(basari_mesaji)
        
        for msg in updates:
            send_telegram(msg)
            
        print(f"Bitti. İşlenen ürün: {len(new_data)}")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    start_tracking()
