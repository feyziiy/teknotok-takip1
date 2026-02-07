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
    except Exception as e:
        print(f"Telegram hatası: {e}")

def start_tracking():
    print("XML verisi kontrol ediliyor...")
    try:
        response = requests.get(XML_URL, timeout=30)
        response.encoding = 'utf-8'
        parser = etree.XMLParser(recover=True, encoding='utf-8')
        root = etree.fromstring(response.content, parser=parser)
    except Exception as e:
        print(f"XML Okuma Hatası: {e}")
        return

    # Hafızayı oku
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

    # XML içindeki her ürünü tara
    for post in root.xpath('.//post'):
        try:
            sku = post.find('Sku').text.strip()
            title = post.find('Title').text.strip()
            price = post.find('Price').text.strip()
            stock_text = post.find('Stock').text
            # Sayısal olmayan karakterleri temizle ve tam sayıya çevir
            stock = int(''.join(filter(str.isdigit, stock_text))) if stock_text else 0

            new_data[sku] = {"Price": price, "Stock": stock, "Title": title}

            # SENİN GÖNDERDİĞİN KIYASLAMA MANTIĞI BURADA BAŞLIYOR:
            if old_data and sku in old_data:
                old = old_data[sku]
                
                # 1. Fiyat Değişimi Kontrolü
                if old['Price'] != price:
                    updates.append(f"💰 *FİYAT DEĞİŞTİ*\n{title}\n📉 {old['Price']} -> 📈 {price}")
                
                # 2. Stok Azalması (Satış Takibi)
                current_stock = int(stock)
                old_stock = int(old['Stock'])
                
                if current_stock < old_stock:
                    fark = old_stock - current_stock
                    updates.append(f"📉 *STOK AZALDI (-{fark})*\n{title}\nKalan Stok: {current_stock}")
                
                # 3. Stok Artışı (Yeni Ürün Girişi)
                elif current_stock > old_stock:
                    fark = current_stock - old_stock
                    updates.append(f"📈 *STOK ARTTI (+{fark})*\n{title}\nYeni Stok: {current_stock}")
        except Exception as e:
            continue

    # Yeni verileri hafızaya kaydet
    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    
    # Değişiklik varsa mesaj at
    if updates:
        for msg in updates[:10]: 
            send_telegram(msg)
    else:
        print("Herhangi bir stok veya fiyat değişikliği yok.")

if __name__ == "__main__":
    start_tracking()
