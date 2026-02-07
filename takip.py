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
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def start_tracking():
    print("Teknotok XML taranıyor...")
    try:
        response = requests.get(XML_URL, timeout=30)
        response.encoding = 'utf-8'
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(response.content, parser=parser)
        
        new_data = {}
        # Paylaştığın yapıdaki <post> etiketlerini bulur
        posts = root.xpath("//post")
        
        for post in posts:
            # Senin paylaştığın büyük harf düzeniyle verileri çekiyoruz
            sku = post.findtext("Sku")
            title = post.findtext("Title")
            stock_val = post.findtext("Stock")
            price = post.findtext("Price")

            if sku and title:
                s_digits = "".join(filter(str.isdigit, str(stock_val)))
                new_data[sku.strip()] = {
                    "Stock": int(s_digits) if s_digits else 0,
                    "Title": title.strip(),
                    "Price": price
                }

        # Hafıza yönetimi
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
                        # İstediğin alt alta yerleşim düzeni
                        msg = (f"{emoji} *{durum}*\n\n"
                               f"*Ürün:* {info['Title']}\n"
                               f"*SKU:* `{sku}`\n"
                               f"*Eski Stok:* {old_stock}\n"
                               f"*Yeni Stok:* {new_stock}\n"
                               f"*Fiyat:* {info.get('Price', '---')} TL")
                        updates.append(msg)
                else:
                    msg = (f"🆕 *YENİ ÜRÜN*\n\n"
                           f"*Ürün:* {info['Title']}\n"
                           f"*SKU:* `{sku}`\n"
                           f"*Stok:* {info['Stock']}\n"
                           f"*Fiyat:* {info.get('Price', '---')} TL")
                    updates.append(msg)

        # Güncel veriyi kaydet
        with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=4)

        # Raporlama
        if not old_data and len(new_data) > 0:
            send_telegram(f"✅ *Bağlantı Kuruldu!*\nTeknotok XML'den {len(new_data)} ürün başarıyla hafızaya alındı. İzleme başladı.")
        
        for msg in updates:
            send_telegram(msg)
            
        print(f"İşlem tamam. Bulunan ürün: {len(new_data)}")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    start_tracking()
