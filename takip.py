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
    print("Teknotok XML Cimbiz Modu Baslatildi...")
    try:
        response = requests.get(XML_URL, timeout=30)
        response.encoding = 'utf-8'
        content = response.text

        # XML yapisina takilmadan tum postlari ayikla
        posts = re.findall(r'<post>(.*?)</post>', content, re.DOTALL)
        
        new_data = {}
        for p in posts:
            # Etiketlerin icindeki veriyi cek
            def get_val(tag, text):
                res = re.search(f'<{tag}>(.*?)</{tag}>', text, re.DOTALL)
                return res.group(1).strip() if res else None

            sku = get_val("Sku", p)
            title = get_val("Title", p)
            stock = get_val("Stock", p)
            price = get_val("Price", p)

            if sku and title:
                s_digits = "".join(filter(str.isdigit, str(stock)))
                new_data[sku] = {
                    "Stock": int(s_digits) if s_digits else 0,
                    "Title": title,
                    "Price": price or "0"
                }

        # Hafiza Islemleri
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
                        msg = (f"{emoji} *STOK DEĞİŞTİ*\n\n"
                               f"*Ürün:* {info['Title']}\n"
                               f"*SKU:* `{sku}`\n"
                               f"*Eski Stok:* {old_data[sku]['Stock']}\n"
                               f"*Yeni Stok:* {info['Stock']}\n"
                               f"*Fiyat:* {info['Price']} TL")
                        updates.append(msg)
                else:
                    updates.append(f"🆕 *YENİ ÜRÜN:* {info['Title']}")

        with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)

        if not old_data and len(new_data) > 0:
            send_telegram(f"✅ *ZAFER!* \n\n{len(new_data)} ürün başarıyla takibe alındı. Sistem artık tıkır tıkır çalışıyor.")
        
        for msg in updates[:10]:
            send_telegram(msg)
            
        print(f"Bitti. Bulunan urun: {len(new_data)}")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    start_tracking()
