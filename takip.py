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
    print("XML çekiliyor...")
    response = requests.get(XML_URL, timeout=30)
    response.encoding = 'utf-8'
    parser = etree.XMLParser(recover=True, encoding='utf-8')
    root = etree.fromstring(response.content, parser=parser)
    
    # Mevcut hafızayı oku
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

            # Sadece hafıza doluysa kıyasla (ikinci turda çalışır)
            if old_data and sku in old_data:
                old = old_data[sku]
                if stock < old['Stock']:
                    updates.append(f"📉 *STOK AZALDI (-{old['Stock'] - stock})*\n{title}\nKalan: {stock}")
                elif stock > old['Stock']:
                    updates.append(f"📈 *STOK ARTTI*\n{title}\nYeni: {stock}")
                elif old['Price'] != price:
                    updates.append(f"💰 *FİYAT DEĞİŞTİ*\n{title}\n{old['Price']} -> {price}")
            # Yeni ürün kontrolü
            elif old_data and sku not in old_data:
                updates.append(f"🆕 *YENİ ÜRÜN*\n{title}")
        except:
            continue

    # DOSYAYA YAZ (Zorunlu ve temiz yazım)
    with open(HAFIZA_FILE, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    
    # Eğer hafıza ilk kez doluyorsa bilgi ver
    if not old_data:
        send_telegram("✅ *Hafıza Oluşturuldu!*\nİlk tarama tamam, artık sadece değişiklik olunca yazacağım.")

    if updates:
        for msg in updates[:10]:
            send_telegram(msg)

if __name__ == "__main__":
    start_tracking()
